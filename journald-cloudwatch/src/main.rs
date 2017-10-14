extern crate rusoto_core;
extern crate rusoto_logs;

mod journald;

use std::env;
use std::str::FromStr;
use std::thread;
use std::time;
use std::sync::mpsc;
use std::collections::BTreeMap;

use rusoto_core::{default_tls_client, EnvironmentProvider, Region};
use rusoto_logs::*;

use journald::Journal;

fn main() {
    println!("Starting journald-cloudwatch...");

    let (tx, rx) = mpsc::channel();

    let client = make_client();
    let stream = init_log_stream(&client).unwrap();
    println!("Log group and stream initialized");
    let last_usec_opt = stream.last_event_timestamp.map(|msec| (msec * 1000) as u64);
    println!("Last log entry in stream at {:?} usec", last_usec_opt);

    let journald_thread = thread::spawn(move || {
        fetch_journald_logs(last_usec_opt, tx.clone());
    });

    process_log_rows(client, rx, stream.upload_sequence_token);
    journald_thread.join().unwrap();
}

fn fetch_journald_logs(last_usec_opt: Option<u64>, tx: mpsc::Sender<(u64, BTreeMap<String, String>)>) -> () {
    let unit = String::from("lemon.service"); // TODO: Read from env or something
    let mut journal = Journal::open().unwrap();

    println!("Seeking to proper point in journal");
    match last_usec_opt {
        None => journal.seek_head(),
        Some(last_usec) => journal.seek(last_usec + 1),
    }.unwrap();

    loop {
        match journal.next().unwrap() {
            Some((usec, record)) => {
                println!("Fetched record {:?}", record);
                if record.get("_SYSTEMD_UNIT").map_or(false, |x| x == &unit) {
                    println!("Found wanted record");
                    tx.send((usec, record)).unwrap();
                }
            },
            None => {
                println!("No more log records. Waiting for a while");
                thread::sleep(time::Duration::from_secs(10));
            },
        }
    }
}

fn process_log_rows(client: Box<CloudWatchLogs>, rx: mpsc::Receiver<(u64, BTreeMap<String, String>)>, initial_upload_sequence_token: Option<String>) -> () {
    println!("Started CloudWatch Logs uploader");
    let batch_size = 1000;
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

                token = upload_batch(&client, &batch, token).unwrap();
                batch.clear();

                last_upload = time::SystemTime::now();
                thread::sleep(time::Duration::from_millis(200));
            }
        }
    }
}

fn upload_batch(client: &Box<CloudWatchLogs>, batch: &Vec<(u64, BTreeMap<String, String>)>, token: Option<String>) -> Result<Option<String>,()> {
    println!("Uploading batch of {} log rows to CloudWatch", batch.len());

    let instance_id = format!("droplet-{}", 32477856); // TODO: Get instance ID
    let log_group_name = String::from("discord-prod-bot");
    let log_stream_name = String::from(format!("discord-prod-bot-{}", instance_id));

    let log_events = batch.iter().map(|x| match x {
        &(usec, ref record) => InputLogEvent {
            message: record.get("MESSAGE").unwrap().to_owned(),
            timestamp: (usec / 1000) as i64,
        }
    }).collect();

    match client.put_log_events(&PutLogEventsRequest {
        log_events,
        log_group_name,
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

fn init_log_stream(client: &Box<CloudWatchLogs>) -> Result<LogStream, AsdfError> {
    let instance_id = format!("droplet-{}", 32477856); // TODO: Get instance ID
    let log_group_name = String::from("discord-prod-bot");
    let log_stream_name = String::from(format!("discord-prod-bot-{}", instance_id));

    match client.create_log_group(&CreateLogGroupRequest{
        log_group_name: log_group_name.clone(),
        tags: None,
    }) {
        Ok(()) => println!("Log group {} created", log_group_name),
        Err(CreateLogGroupError::ResourceAlreadyExists(_)) =>
            println!("Log group {} already exists", log_group_name),
        Err(e) => return Err(AsdfError::from(e)),
    }

    match client.create_log_stream(&CreateLogStreamRequest{
        log_group_name: log_group_name.clone(),
        log_stream_name: log_stream_name.clone(),
    }) {
        Ok(()) => println!("Log stream {} created", log_stream_name),
        Err(CreateLogStreamError::ResourceAlreadyExists(_)) =>
            println!("Log stream {} already exists", log_stream_name),
        Err(e) => return Err(AsdfError::from(e)),
    }

    match client.describe_log_streams(&DescribeLogStreamsRequest{
        order_by: None,
        log_group_name: log_group_name.clone(),
        log_stream_name_prefix: Some(log_stream_name.clone()),
        descending: None,
        limit: None,
        next_token: None,
    }) {
        Ok(describe_log_stream_response) => {
            let streams_opt = describe_log_stream_response.log_streams.unwrap();
            let log_stream = streams_opt.first().unwrap();
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
