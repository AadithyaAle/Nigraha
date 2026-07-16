import boto3
import json
import os
import time
from rich.console import Console

console = Console()
LOG_GROUP = "StackSentinel-Logs"
STREAM_NAME = "Laptop-G15-Agent"

def push_to_cloud():
    """
    Reads the local history and pushes new entries to AWS CloudWatch.
    """
    if not os.path.exists("sentinel_history.json"):
        return

    # Check for AWS Credentials
    session = boto3.Session(profile_name="Stack-Sentinel")
    credentials = session.get_credentials()
    if not credentials:
        # Fail silently so the app works offline
        return 

    try:
        client = boto3.client('bedrock-runtime', region_name='us-east-1')

        # 1. Create Log Group if missing
        try:
            client.create_log_group(logGroupName=LOG_GROUP)
        except client.exceptions.ResourceAlreadyExistsException:
            pass

        # 2. Create Log Stream if missing
        try:
            client.create_log_stream(logGroupName=LOG_GROUP, logStreamName=STREAM_NAME)
        except client.exceptions.ResourceAlreadyExistsException:
            pass

        # 3. Read Local Logs
        with open("sentinel_history.json", "r") as f:
            data = json.load(f)
            if not data: return

        # Get the last entry to push
        latest_entry = data[-1]
        
        # 4. Push to Cloud
        log_event = {
            'timestamp': int(time.time() * 1000),
            'message': json.dumps(latest_entry)
        }

        client.put_log_events(
            logGroupName=LOG_GROUP,
            logStreamName=STREAM_NAME,
            logEvents=[log_event]
        )
        
        console.print(f"[dim]☁️  Synced event to AWS CloudWatch: {LOG_GROUP}[/dim]")

    except Exception as e:
        # Don't crash the main app if internet is down
        pass