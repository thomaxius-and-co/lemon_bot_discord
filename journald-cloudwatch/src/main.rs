extern crate rusoto_core;
extern crate rusoto_logs;

use std::env;
use std::str::FromStr;
use std::thread;
use std::time;

use rusoto_core::{default_tls_client, EnvironmentProvider, Region};
use rusoto_logs::*;

fn main() {
    println!("Starting journald-cloudwatch...");

    let client = make_client();
    let stream = init_log_stream(&client).unwrap();
    println!("Log group and stream initialized");
    println!("Last log entry in stream at {:?}", stream.last_event_timestamp);

    loop {
        println!("TODO: Implement something...");
        thread::sleep(time::Duration::from_millis(60 * 1000));
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
    let instance_id = 32477856; // TODO: Get instance ID
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
