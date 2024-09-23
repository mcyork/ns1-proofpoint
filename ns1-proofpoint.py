import os
import requests
import json
import time
import sys
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

def delete_record(zone_name, record_name, record_type):
    url = f"https://api.nsone.net/v1/zones/{zone_name}/{record_name}/{record_type}"
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

def list_specific_records(zone_name):
    records = get_zone_records(zone_name)
    if records:
        dmarc_record = next((r for r in records.get("records", []) if r["domain"] == f"_dmarc.{zone_name}"), None)
        proofpoint_record = next((r for r in records.get("records", []) if r["domain"] == f"_proofpoint-verification.{zone_name}"), None)
        return dmarc_record, proofpoint_record
    else:
        return None, None

def process_zones(file_path):
    if not os.path.exists(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
        log_action(f"Error: The file '{file_path}' does not exist.")
        return

    with open(file_path, "r") as file:
        zones = file.readlines()

    for zone in zones:
        zone = zone.strip()
        if not zone:
            continue

        print(f"Processing zone: {zone}")
        log_action("=" * 20)
        log_action(f"Processing zone: {zone}")

        dmarc_record, proofpoint_record = list_specific_records(zone)

        new_dmarc_value = f"_dmarc.{zone}.dmarc.has.pphosted.com."
        proposed_changes = []

        if dmarc_record:
            current_dmarc_value = dmarc_record['short_answers']
            current_dmarc_type = dmarc_record['type']
            print(f"Current _dmarc.{zone} value: {current_dmarc_value}, type: {current_dmarc_type}")
            log_action(f"Current _dmarc.{zone} value: {current_dmarc_value}, type: {current_dmarc_type}")
            if new_dmarc_value not in current_dmarc_value or current_dmarc_type != "CNAME":
                proposed_changes.append(f"Change _dmarc.{zone} to {new_dmarc_value} (type: CNAME)")
        else:
            proposed_changes.append(f"Create _dmarc.{zone} with value {new_dmarc_value} (type: CNAME)")

        if proofpoint_record:
            current_proofpoint_value = proofpoint_record['short_answers']
            current_proofpoint_type = proofpoint_record['type']
            print(f"Current _proofpoint-verification.{zone} value: {current_proofpoint_value}, type: {current_proofpoint_type}")
            log_action(f"Current _proofpoint-verification.{zone} value: {current_proofpoint_value}, type: {current_proofpoint_type}")
            if config.PROOFPOINT_VALUE not in current_proofpoint_value or current_proofpoint_type != "TXT":
                proposed_changes.append(f"Change _proofpoint-verification.{zone} to {config.PROOFPOINT_VALUE} (type: TXT)")
        else:
            proposed_changes.append(f"Create _proofpoint-verification.{zone} with value {config.PROOFPOINT_VALUE} (type: TXT)")

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

        if dmarc_record:
            if new_dmarc_value not in current_dmarc_value or current_dmarc_type != "CNAME":
                delete_record(zone, f"_dmarc.{zone}", current_dmarc_type)
                create_record(zone, "_dmarc", "CNAME", new_dmarc_value)
                log_action(f"Changed _dmarc.{zone} to {new_dmarc_value} (type: CNAME)")
            else:
                print(f"Record _dmarc.{zone} already has the correct value and type.")
                log_action(f"Record _dmarc.{zone} already has the correct value and type.")
        else:
            create_record(zone, "_dmarc", "CNAME", new_dmarc_value)
            log_action(f"Created _dmarc.{zone} with value {new_dmarc_value} (type: CNAME)")

        if proofpoint_record:
            if config.PROOFPOINT_VALUE not in current_proofpoint_value or current_proofpoint_type != "TXT":
                delete_record(zone, f"_proofpoint-verification.{zone}", current_proofpoint_type)
                create_record(zone, "_proofpoint-verification", "TXT", config.PROOFPOINT_VALUE)
                log_action(f"Changed _proofpoint-verification.{zone} to {config.PROOFPOINT_VALUE} (type: TXT)")
            else:
                print(f"Record _proofpoint-verification.{zone} already has the correct value and type.")
                log_action(f"Record _proofpoint-verification.{zone} already has the correct value and type.")
        else:
            create_record(zone, "_proofpoint-verification", "TXT", config.PROOFPOINT_VALUE)
            log_action(f"Created _proofpoint-verification.{zone} with value {config.PROOFPOINT_VALUE} (type: TXT)")

        log_action("=" * 20)
        time.sleep(1)  # To avoid rate limiting

# Main execution
if len(sys.argv) > 1:
    file_path = sys.argv[1]
else:
    file_path = input("Enter the path to the file containing the list of zones: ").strip()

process_zones(file_path)
