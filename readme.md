# NS1 Proofpoint

This script manages DNS records for specified zones using the NS1 API. It specifically handles records like `_dmarc`, `_proofpoint-verification`, `spf`, and `dkim`, ensuring they have the correct values and types. It also supports handling defensive zones and deleting specific records if they exist.

> **⚠️ USE WITH CAUTION and TEST IN A NON-PRODUCTION ENVIRONMENT. ⚠️**

Yes it should have a better name as there are more than just proofpoint out there.  Agari etc etc.

The core goal of the code is to provide a safe way to stamp a larger set of domains with the necessary records to be added to a service such as Proofpoint or Agari, parked, or otherwise managed.  It can be run often to keep a record set as is (if you can do it safely, remove the prompting).

Other record types may be added in the future (or just work if we are lucky).

The forced linking of a domain to another for parking may be blended into this code in the future.
Currently it skips linked zones and has no offer to unlink or otherwise manage them.

## Prerequisites

- Python 3.x
- `requests` library (`pip install requests`)
- `PyYAML` library (`pip install pyyaml`)
- NS1 API key

### Required Python Packages

The code is built and tested on the below but the above two are the only ones that are required.

You can install the tested packages using `pip`:

```sh
pip install -r requirements.txt
```

Here is the `requirements.txt` file:

```plaintext
certifi==2024.8.30
charset-normalizer==3.3.2
idna==3.10
PyYAML==6.0.2
requests==2.32.3
urllib3==2.2.3
```

## Configuration

Create a `config.py` or `config_local.py` file with the following content:

```
API_KEY = 'your_ns1_api_key'
LOG_FILE = 'path_to_log_file.log'
```

Create a `config_records.yaml` file with the following content:

```
regular_records:
  - name: "_dmarc"
    type: "CNAME"
    value_template: "_dmarc.{zone}.dmarc.has.pphosted.com."
  - name: "_proofpoint-verification"
    type: "TXT"
    value: "hello-world"
  - name: "spf"
    type: "TXT"
    value_template: "v=spf1 include:{domain} ~all"
  - name: "dkim"
    type: "CNAME"
    value_template: "dkim._domainkey.{zone}.dkim.has.pphosted.com."

defensive_records:
  - name: "_dmarc"
    type: "TXT"
    value_template: "v=DMARC1; p=none; rua=mailto:dmarc-reports@{domain}"
  - name: "_proofpoint-verification"
    type: "TXT"
    value: "defensive-verification"
  - name: "dkim"
    delete_if_exists: true
```

## CSV Input

Prepare a CSV file containing the list of zones and their types. For example, `zones.csv`:

```
type,zone
defensive,example.com
regular,email.example.com
other_yaml_records,other.example.com
```

## Usage

1. Prepare the CSV file containing the list of zones and their types as shown above.

2. Run the script:

```sh
python ns1-proofpoint.py zones.csv
```

3. The script will process each zone, list the current values of the specified records, and show the proposed changes. You will be prompted to confirm the changes for each zone:

```
Processing zone: example.com (Type: defensive)
Current _dmarc.example.com value: ['v=DMARC1; p=none; rua=mailto:dmarc-reports@example.com'], type: TXT
Current _proofpoint-verification.example.com value: ['defensive-verification'], type: TXT
Proposed changes:
 - Delete dkim.example.com
Do you want to proceed with the changes for zone example.com? (Y/n): y
```

4. The script will apply the changes if you confirm with `Y`.

## Logging

The script logs actions to the file specified in the `LOG_FILE` configuration. This includes fetching records, proposed changes, user prompts, and responses, as well as the record details (value and type) before and after changes.

## Notes

- The script includes rate limiting with a 1-second delay between processing each zone to avoid hitting API rate limits.
- Ensure your NS1 API key has the necessary permissions to manage DNS records for the specified zones.

## License

This project is licensed under the MIT License.