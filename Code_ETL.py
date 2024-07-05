import psycopg2
import configparser
import boto3
import argparse
import sys
from datetime import datetime
import json
import base64

def fetch_database_credentials():
    """Retrieve PostgreSQL credentials from configuration file."""
    print("Loading database configuration...")
    config = configparser.ConfigParser()
    config.read('postgres.ini')
    credentials = {
        'username': config.get('postgres', 'username'),
        'password': config.get('postgres', 'password'),
        'host': config.get('postgres', 'host'),
        'database': config.get('postgres', 'database')
    }
    print("Database configuration loaded successfully.")
    return credentials


def receive_sqs_messages(endpoint_url, queue_name, wait_time, max_messages):
    """Receive messages from an SQS queue."""
    print(f"Connecting to SQS queue at {endpoint_url}...")
    sqs_client = boto3.client("sqs", endpoint_url=endpoint_url)
    queue_url = f"{endpoint_url}/{queue_name}"
    try:
        print("Receiving messages from the queue...")
        response = sqs_client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=max_messages,
            WaitTimeSeconds=wait_time
        )
        print("Messages received successfully.")
        return response.get('Messages', [])
    except Exception as e:
        print(f"Error - {str(e)}")
        sys.exit()

def encode_base64(string_parameter, action="encode"):
    """Encode or decode a string using base64."""
    if action == "encode":
        ascii_string = string_parameter.encode('ascii')
        encoded_string = base64.b64encode(ascii_string).decode('utf-8')
        return encoded_string
    elif action == "decode":
        decoded_string = base64.b64decode(string_parameter).decode('utf-8')
        return decoded_string


def transform_messages_pii(messages):
    """Transform PII data in the messages."""
    print("Transforming messages...")
    if not messages:
        print("Error - Message list is empty")
        sys.exit()

    transformed_messages = []
    for message in messages:
        try:
            message_body = json.loads(message['Body'])
            ip = message_body.get('ip')
            device_id = message_body.get('device_id')

            if not ip or not device_id:
                continue

        except (KeyError, json.JSONDecodeError):
            continue

        message_body['ip'] = encode_base64(ip)
        message_body['device_id'] = encode_base64(device_id)
        transformed_messages.append(message_body)

    print(f"{len(transformed_messages)} messages transformed successfully.")
    return transformed_messages

def load_data_to_postgresql(messages, credentials):
    """Load transformed messages into PostgreSQL."""
    print("Loading messages into PostgreSQL...")
    if not messages:
        print("Error - No messages to load")
        sys.exit()

    conn = psycopg2.connect(
        host=encode_base64(credentials['host'], action="decode"),
        database=encode_base64(credentials['database'], action="decode"),
        user=encode_base64(credentials['username'], action="decode"),
        password=encode_base64(credentials['password'], action="decode")
    )
    cursor = conn.cursor()

    for message in messages:
        message['locale'] = message.get('locale', 'None')
        message['create_date'] = datetime.now().strftime("%Y-%m-%d")
        values = list(message.values())
        cursor.execute("""
            INSERT INTO user_logins (
                user_id, app_version, device_type, masked_ip, locale, masked_device_id, create_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, values)
        conn.commit()

    cursor.close()
    conn.close()
    print("Messages loaded into PostgreSQL successfully.")

def main():
    """Main function to perform the ETL process."""
    parser = argparse.ArgumentParser(
        prog="ETL Process",
        description="Extracts data from SQS queue, transforms PII data, and loads the processed data into PostgreSQL",
        epilog="Please raise an issue for code modifications"
    )

    parser.add_argument('-e', '--endpoint-url', required=True, help="SQS Endpoint URL")
    parser.add_argument('-q', '--queue-name', required=True, help="SQS Queue name")
    parser.add_argument('-w', '--wait-time', type=int, default=10, help="Wait time in seconds")
    parser.add_argument('-m', '--max-messages', type=int, default=10, help="Maximum number of messages to pull from SQS queue")

    args = parser.parse_args()

    credentials = fetch_database_credentials()
    messages = receive_sqs_messages(args.endpoint_url, args.queue_name, args.wait_time, args.max_messages)
    transformed_messages = transform_messages_pii(messages)
    load_data_to_postgresql(transformed_messages, credentials)

if __name__ == "__main__":
    main()
