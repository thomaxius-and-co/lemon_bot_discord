extern crate rusoto_core;
extern crate rusoto_logs;
extern crate regex;

mod journald;

use std::env;
use std::str::FromStr;
use std::thread;
use std::time;
use std::sync::mpsc;

use rusoto_core::{default_tls_client, EnvironmentProvider, Region};
use rusoto_logs::*;

use journald::Journal;

fn main() {
    println!("Starting journald-cloudwatch...");
    match env::var("SYSTEMD_UNIT_NAMES") {
        Ok(value) => run_workers(value.split(",").collect()),
        Err(e) => panic!("Error reading SYSTEMD_UNIT_NAMES environment variable: {}", e),
    };
}

fn run_workers(units: Vec<&str>) {
    let mut workers = vec![];
    for unit_name in units {
        let parts = unit_name.split("=").collect::<Vec<&str>>();
        let unit = parts[0].to_owned();
        let log_group = parts[1].to_owned();
        let worker = thread::spawn(move || { log_worker(unit, log_group); });
        workers.push(worker);
    }

    for w in workers {
        w.join().unwrap();
    }
}

fn log_worker(unit_name: String, log_group: String) {
    let (tx, rx) = mpsc::channel();

    let client = make_client();
    let stream = init_log_stream(&client, &log_group).unwrap();
    println!("Log group and stream initialized");
    let last_usec_opt = stream.last_event_timestamp.map(|msec| (msec * 1000) as u64);
    println!("Last log entry in stream at {:?} usec", last_usec_opt);

    let journald_thread = thread::spawn(move || {
        fetch_journald_logs(&unit_name, last_usec_opt, tx.clone());
    });

    process_log_rows(client, rx, &log_group, stream.upload_sequence_token);
    journald_thread.join().unwrap();
}

fn is_entry_start(s: &str) -> bool {
    regex::Regex::new(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} .+").unwrap().is_match(s)
}

fn fetch_journald_logs(unit_name: &str, last_usec_opt: Option<u64>, tx: mpsc::Sender<(u64, String)>) -> () {
    let mut journal = Journal::open().unwrap();
    journal.add_match("_SYSTEMD_UNIT", unit_name).unwrap();

    println!("Seeking to proper point in journal");
    match last_usec_opt {
        None => journal.seek_head(),
        Some(last_usec) => journal.seek(last_usec + 1),
    }.unwrap();

    println!("Skipping until next proper log entry start");
    while let Some((_, record)) = journal.next().unwrap() {
        let message = record.get("MESSAGE").unwrap().to_owned();
        if is_entry_start(&message) {
            journal.previous().unwrap();
            break;
        }
    }

    println!("Polling journal for records");
    let mut entry_start_usec = 0;
    let mut entry_pieces = Vec::with_capacity(100);
    loop {
        match journal.next().unwrap() {
            Some((usec, record)) => {
                let message = record.get("MESSAGE").unwrap().to_owned();
                if is_entry_start(&message) {
                    // If we have just started the process, the collected
                    // entry_pieces will be empty. We skip it to avoid
                    // CloudWatch errors.
                    if !entry_pieces.is_empty() {
                      // New entry starting. Combine and deliver the previuos one
                      tx.send((entry_start_usec, entry_pieces.join("\n"))).unwrap();
                    }

                    entry_pieces.clear();
                    entry_start_usec = usec;
                }

                entry_pieces.push(message);
            },
            None => {
                println!("Waiting for journal events");
                journal.wait(None).unwrap();
            }
        }
    }
}

fn process_log_rows(client: Box<CloudWatchLogs>, rx: mpsc::Receiver<(u64, String)>, log_group_name: &str, initial_upload_sequence_token: Option<String>) -> () {
    println!("Started CloudWatch Logs uploader");
    let batch_size = 500;
    let batch_max_wait = time::Duration::from_secs(2);

    let mut token = initial_upload_sequence_token;
    let mut batch = Vec::with_capacity(batch_size);
    let mut last_upload = time::SystemTime::now();
    loop {
        match rx.try_recv() {
            Ok(x) => batch.push(x),
            Err(mpsc::TryRecvError::Empty) => thread::sleep(time::Duration::from_millis(100)),
            Err(mpsc::TryRecvError::Disconnected) => panic!("process_log_rows: channel disconnected, this should never happen"),
        };

        if batch.len() > 0 {
            let force_upload_because_time = last_upload.elapsed().unwrap() > batch_max_wait;
            if batch.len() >= batch_size || force_upload_because_time {
                if force_upload_because_time {
                    println!("Upload triggered by interval");
                }

                token = upload_batch(&client, &batch, &log_group_name, token).unwrap();
                batch.clear();

                last_upload = time::SystemTime::now();
                thread::sleep(time::Duration::from_millis(200));
            }
        }
    }
}

fn upload_batch(client: &Box<CloudWatchLogs>, batch: &Vec<(u64, String)>, log_group_name: &str, token: Option<String>) -> Result<Option<String>,()> {
    println!("Uploading batch of {} log rows to CloudWatch", batch.len());

    let instance_id = format!("droplet-{}", 32477856); // TODO: Get instance ID
    let log_stream_name = String::from(format!("{}-{}", log_group_name, instance_id));

    let log_events = batch.iter().map(|x| match x {
        &(usec, ref message) => InputLogEvent {
            message: message.to_owned(),
            timestamp: (usec / 1000) as i64,
        }
    }).collect();

    match client.put_log_events(&PutLogEventsRequest {
        log_events,
        log_group_name: log_group_name.to_owned(),
        log_stream_name,
        sequence_token: token.clone(),
    }) {
        Ok(response) => Ok(response.next_sequence_token.clone()),
        Err(e) => {
            // TODO: Handle ratelimit properly with retry exponential backoff
            println!("upload_batch: unknown error {}", e);
            thread::sleep(time::Duration::from_millis(1000));
            Ok(token)
        },
    }
}

fn make_client() -> Box<CloudWatchLogs> {
    let credentials = EnvironmentProvider{};
    let region_str = env::var("AWS_REGION").unwrap();
    let client = CloudWatchLogsClient::new(
        default_tls_client().unwrap(),
        credentials,
        Region::from_str(&region_str).unwrap()
    );
    Box::new(client)
}

fn init_log_stream(client: &Box<CloudWatchLogs>, log_group_name: &str) -> Result<LogStream, AsdfError> {
    let instance_id = format!("droplet-{}", 32477856); // TODO: Get instance ID
    let log_stream_name = String::from(format!("{}-{}", log_group_name, instance_id));

    match client.create_log_group(&CreateLogGroupRequest{
        log_group_name: log_group_name.to_owned(),
        tags: None,
    }) {
        Ok(()) => println!("Log group {} created", log_group_name),
        Err(CreateLogGroupError::ResourceAlreadyExists(_)) =>
            println!("Log group {} already exists", log_group_name),
        Err(e) => return Err(AsdfError::from(e)),
    }

    match client.create_log_stream(&CreateLogStreamRequest{
        log_group_name: log_group_name.to_owned(),
        log_stream_name: log_stream_name.clone(),
    }) {
        Ok(()) => println!("Log stream {} created", log_stream_name),
        Err(CreateLogStreamError::ResourceAlreadyExists(_)) =>
            println!("Log stream {} already exists", log_stream_name),
        Err(e) => return Err(AsdfError::from(e)),
    }

    match client.describe_log_streams(&DescribeLogStreamsRequest{
        order_by: None,
        log_group_name: log_group_name.to_owned(),
        log_stream_name_prefix: Some(log_stream_name.clone()),
        descending: None,
        limit: None,
        next_token: None,
    }) {
        Ok(describe_log_stream_response) => {
            let streams = describe_log_stream_response.log_streams.unwrap();
            let log_stream = streams.iter()
                .find(|&s| s.log_stream_name.as_ref().map_or(false, |x| x == &log_stream_name))
                .unwrap();
            Ok(log_stream.clone())
        },
        Err(e) => Err(AsdfError::from(e)),
    }
}

#[derive(Debug)]
enum AsdfError {
    CreateGroup(CreateLogGroupError),
    CreateStream(CreateLogStreamError),
    DescribeStream(DescribeLogStreamsError),
}

impl From<CreateLogGroupError> for AsdfError {
    fn from(e: CreateLogGroupError) -> Self {
        AsdfError::CreateGroup(e)
    }
}

impl From<CreateLogStreamError> for AsdfError {
    fn from(e: CreateLogStreamError) -> Self {
        AsdfError::CreateStream(e)
    }
}

impl From<DescribeLogStreamsError> for AsdfError {
    fn from(e: DescribeLogStreamsError) -> Self {
        AsdfError::DescribeStream(e)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_is_entry_start() {
        assert!(is_entry_start("2017-10-14 22:29:28,780 INFO OSU_API GET https://osu.ppy.sh/api/get_user?k=<REDACTED>&event_days=1&u=7840726&type=id 504 <html>"));
        assert!(!is_entry_start(""));
        assert!(!is_entry_start("<title>No pippi, that's a bad pippi!</title>"));
    }
}
