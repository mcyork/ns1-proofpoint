# NS1 Proofpoint

This script manages DNS records for specified zones using the NS1 API. It specifically handles records like `_dmarc`, `_proofpoint-verification`, `spf`, and `dkim`, ensuring they have the correct values and types.

## Prerequisites

- Python 3.x
- `requests` library (`pip install requests`)
- `PyYAML` library (`pip install pyyaml`)
- NS1 API key

## Configuration

Create a `config.py` or `config_local.py` file with the following content:

```
API_KEY = 'your_ns1_api_key'
LOG_FILE = 'path_to_log_file.log'
```

Create a `config_records.yaml` file with the following content:

```
records:
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
```

## Usage

1. Prepare a text file containing the list of zones, one per line. For example, `zones.txt`:

```
example.com
example.org
example.net
```

2. Run the script:

```sh
python ns1-proofpoint.py
```

3. When prompted, enter the path to the file containing the list of zones:

```
Enter the path to the file containing the list of zones: zones.txt
```

4. The script will process each zone, list the current values of the specified records, and show the proposed changes. You will be prompted to confirm the changes for each zone:

```
Processing zone: example.com
Current _dmarc.example.com value: ['_dmarc.example.com.dmarc.has.pphosted.com.'], type: CNAME
Current _proofpoint-verification.example.com value: ['hello-world'], type: TXT
Proposed changes:
 - Change _dmarc.example.com to _dmarc.example.com.dmarc.has.pphosted.com. (type: CNAME)
 - Change _proofpoint-verification.example.com to your_proofpoint_value (type: TXT)
Do you want to proceed with the changes for zone example.com? (Y/n): y
```

5. The script will apply the changes if you confirm with `Y`.

## Logging

The script logs actions to the file specified in the `LOG_FILE` configuration. This includes fetching records, proposed changes, user prompts, and responses, as well as the record details (value and type) before and after changes.

## Notes

- The script includes rate limiting with a 1-second delay between processing each zone to avoid hitting API rate limits.
- Ensure your NS1 API key has the necessary permissions to manage DNS records for the specified zones.

## License

This project is licensed under the MIT License.