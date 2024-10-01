import os
import requests
import json
import time
import sys
import yaml
import csv
from datetime import datetime

# Try to import from config_local first, fall back to config if not found
try:
    import config_local as config
except ImportError:
    import config

HEADERS = {
    "X-NSONE-Key": config.API_KEY,
    "Content-Type": "application/json"
}

def log_action(action):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(config.LOG_FILE, "a") as log_file:
        log_file.write(f"[{timestamp}] {action}\n")

def get_zone_records(zone_name):
    url = f"https://api.nsone.net/v1/zones/{zone_name}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        print(f"Zone {zone_name} not found.")
        log_action(f"Zone {zone_name} not found.")
        return None
    else:
        print(f"Failed to fetch records for zone {zone_name}: {response.text}")
        log_action(f"Failed to fetch records for zone {zone_name}: {response.text}")
        return None

def delete_record(zone_name, record_name):
    url = f"https://api.nsone.net/v1/zones/{zone_name}/{record_name}"
    print(f"Deleting record with URL: {url}")  # Debug logging for URL
    response = requests.delete(url, headers=HEADERS)
    if response.status_code == 200:
        print(f"Record {record_name} deleted successfully.")
        log_action(f"Record {record_name} deleted successfully.")
    elif response.status_code == 404:
        print(f"Record {record_name} not found.")
        log_action(f"Record {record_name} not found.")
    else:
        print(f"Failed to delete record {record_name}: {response.text}")
        log_action(f"Failed to delete record {record_name}: {response.text}")

def create_record(zone_name, record_name, record_type, data):
    full_domain = f"{record_name}.{zone_name}"
    payload = {
        "zone": zone_name,
        "domain": full_domain,  # Ensuring the full domain
        "type": record_type,
        "answers": [{"answer": [data]}]
    }
    url = f"https://api.nsone.net/v1/zones/{zone_name}/{full_domain}/{record_type}"
    print(f"Creating record with URL: {url}")  # Debug logging for URL
    print(f"Creating record with payload: {json.dumps(payload, indent=2)}")  # Debug logging for payload
    response = requests.put(url, headers=HEADERS, json=payload)
    if response.status_code == 200:
        print(f"Record {record_name} created successfully.")
        log_action(f"Record {record_name} created successfully.")
    elif response.status_code == 409:
        print(f"Record {record_name} already exists.")
        log_action(f"Record {record_name} already exists.")
    else:
        print(f"Failed to create record {record_name}: {response.text}")
        log_action(f"Failed to create record {record_name}: {response.text}")

def list_specific_records(zone_name, record_names):
    records = get_zone_records(zone_name)
    if records:
        found_records = {name: next((r for r in records.get("records", []) if r["domain"] == f"{name}.{zone_name}"), None) for name in record_names}
        return found_records
    else:
        return {name: None for name in record_names}

def process_zones(file_path, config_data):
    if not os.path.exists(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
        log_action(f"Error: The file '{file_path}' does not exist.")
        return

    with open(file_path, "r") as file:
        reader = csv.DictReader(file)
        zones = list(reader)

    for zone_info in zones:
        zone_type = zone_info['type']
        zone = zone_info['zone'].strip()
        if not zone:
            continue

        print(f"Processing zone: {zone} (Type: {zone_type})")
        log_action("=" * 20)
        log_action(f"Processing zone: {zone} (Type: {zone_type})")

        # Check if the zone is linked
        records = get_zone_records(zone)
        # Check if records exist and if the 'link' field is present and true
        if isinstance(records, dict) and records.get("link"):
            print(f"Zone {zone} is linked. Skipping.")
            log_action(f"Zone {zone} is linked. Skipping.")
            log_action("=" * 20)
            continue

        # Select the appropriate set of records based on the zone type
        config_records = config_data.get(f"{zone_type}_records", [])

        record_names = [record['name'] for record in config_records]
        found_records = list_specific_records(zone, record_names)

        proposed_changes = []

        for record in config_records:
            name = record['name']
            record_type = record.get('type')
            value_template = record.get('value_template')
            value = record.get('value')
            delete_if_exists = record.get('delete_if_exists', False)

            # Evaluate the value_template with the actual zone and domain values
            if value_template:
                value = value_template.format(zone=zone, domain=zone)

            current_record = found_records[name]
            if current_record:
                current_value = current_record['short_answers']
                current_type = current_record['type']
                print(f"Current {name}.{zone} value: {current_value}, type: {current_type}")
                log_action(f"Current {name}.{zone} value: {current_value}, type: {current_type}")
                if delete_if_exists:
                    proposed_changes.append(f"Delete {name}.{zone}")
                elif value not in current_value or current_type != record_type:
                    proposed_changes.append(f"Change {name}.{zone} to {value} (type: {record_type})")
            elif not delete_if_exists:
                proposed_changes.append(f"Create {name}.{zone} with value {value} (type: {record_type})")

        if proposed_changes:
            print("Proposed changes:")
            for change in proposed_changes:
                print(f" - {change}")
        else:
            print("No changes needed.")

        question = f"Do you want to proceed with the changes for zone {zone}? (Y/n): "
        confirm = input(question).strip().lower()
        log_action(f"User prompt: {question}")
        log_action(f"User response: {confirm}")

        if confirm != 'y':
            print(f"Skipped changes for zone {zone}.")
            log_action(f"Skipped changes for zone {zone}.")
            log_action("=" * 20)
            continue

        for record in config_records:
            name = record['name']
            record_type = record.get('type')
            value_template = record.get('value_template')
            value = record.get('value')
            delete_if_exists = record.get('delete_if_exists', False)

            # Evaluate the value_template with the actual zone and domain values
            if value_template:
                value = value_template.format(zone=zone, domain=zone)

            current_record = found_records[name]
            if current_record:
                current_value = current_record['short_answers']
                current_type = current_record['type']
                if delete_if_exists:
                    delete_record(zone, f"{name}.{zone}")
                    log_action(f"Deleted {name}.{zone}")
                elif value not in current_value or current_type != record_type:
                    delete_record(zone, f"{name}.{zone}")
                    create_record(zone, name, record_type, value)
                    log_action(f"Changed {name}.{zone} to {value} (type: {record_type})")
                else:
                    print(f"Record {name}.{zone} already has the correct value and type.")
                    log_action(f"Record {name}.{zone} already has the correct value and type.")
            elif not delete_if_exists:
                create_record(zone, name, record_type, value)
                log_action(f"Created {name}.{zone} with value {value} (type: {record_type})")

        log_action("=" * 20)
        time.sleep(1)  # To avoid rate limiting

# Main execution
if len(sys.argv) > 1:
    file_path = sys.argv[1]
else:
    file_path = input("Enter the path to the CSV file containing the list of zones: ").strip()

# Load the YAML configuration
with open("config_records.yaml", "r") as yaml_file:
    config_data = yaml.safe_load(yaml_file)

process_zones(file_path, config_data)