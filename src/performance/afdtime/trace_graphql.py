import subprocess
import json
import uuid
import csv
import re
from datetime import datetime

# Read input files
with open("token.txt") as f:
    token = f.read().strip()

with open("payload.json") as f:
    payload_template = f.read()

with open("groups.txt") as f:
    groups = f.read().splitlines()

# Prepare CSV file
csv_filename = f"graphql_timing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
csv_headers = [
    'timestamp',
    'group_id',
    'request_id',
    'dns_resolution_s',
    'tcp_connect_s',
    'tls_handshake_s',
    'time_to_first_byte_s',
    'total_request_time_s',
    'http_status',
    'content_length',
    'x_lodbrok_cell',
    'x_cache'
]

timing_results = []

for group_id in groups:
    # Replace group ID in payload
    payload = payload_template.replace("GROUPIDTOREPLACE", group_id)

    # Generate unique request ID
    request_id = str(uuid.uuid4())

    curl_cmd = [
        "curl",
        "-sS",
        "-D", "-",  # Dump response headers to stdout
        "-o", "/dev/null",  # Discard body
        "-L",  # Follow redirects
        "-X", "POST",
        "https://engage.cloud.microsoft/graphql?operationName=FeedGroupNestedClients&apiVnext=2",
        "-H", "accept: application/json",
        "-H", f"authorization: {token}",
        "-H", f"x-request-id: {request_id}",
        "-H", "content-type: application/json",
        "-w", (
            "\n=== CURL TIMING ===\n"
            "DNS Resolution: %{time_namelookup}s\n"
            "TCP Connect: %{time_connect}s\n"
            "TLS Handshake: %{time_appconnect}s\n"
            "Time to First Byte: %{time_starttransfer}s\n"
            "Total Request Time: %{time_total}s\n"
        ),
        "--data-raw", payload,
    ]

    print(f"[Processing group: {group_id[:50]}...]")

    result = subprocess.run(curl_cmd, capture_output=True, text=True)

    # Parse timing and header information
    if "=== CURL TIMING ===" in result.stdout:
        header_text, timing_text = result.stdout.split("=== CURL TIMING ===", 1)
    else:
        header_text = result.stdout
        timing_text = "[ERROR] Could not parse timing output."

    # Extract timing values using regex
    timing_data = {}
    timing_patterns = {
        'dns_resolution_s': r'DNS Resolution: ([\d.]+)s',
        'tcp_connect_s': r'TCP Connect: ([\d.]+)s',
        'tls_handshake_s': r'TLS Handshake: ([\d.]+)s',
        'time_to_first_byte_s': r'Time to First Byte: ([\d.]+)s',
        'total_request_time_s': r'Total Request Time: ([\d.]+)s'
    }

    for key, pattern in timing_patterns.items():
        match = re.search(pattern, timing_text)
        timing_data[key] = float(match.group(1)) if match else None # covers error case

    # Extract header information
    header_data = {}
    header_patterns = {
        'http_status': r'HTTP/[\d.]+ (\d+)',
        'content_length': r'content-length: (\d+)',
        'x_lodbrok_cell': r'x-lodbrok-cell: ([^\r\n]+)',
        'x_cache': r'x-cache: ([^\r\n]+)'
    }

    for key, pattern in header_patterns.items():
        match = re.search(pattern, header_text, re.IGNORECASE)
        if key == 'content_length':
            header_data[key] = int(match.group(1)) if match else None
        else:
            header_data[key] = match.group(1).strip() if match else None

    # Combine all data for this request
    row_data = {
        'timestamp': datetime.now().isoformat(),
        'group_id': group_id,
        'request_id': request_id,
        **timing_data,
        **header_data
    }

    timing_results.append(row_data)

    # Print summary for this request
    print(f"  Status: {header_data.get('http_status', 'Unknown')}")
    print(f"  Total Time: {timing_data.get('total_request_time_s', 'Unknown')}s")
    print(f"  Cell: {header_data.get('x_lodbrok_cell', 'Unknown')}")
    print()

# Write results to CSV
with open(csv_filename, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
    writer.writeheader()
    writer.writerows(timing_results)

print(f"=== SUMMARY ===")
print(f"Processed {len(timing_results)} requests")
print(f"Results written to: {csv_filename}")
print(
    f"Average total time: {sum(r['total_request_time_s'] for r in timing_results if r['total_request_time_s']) / len([r for r in timing_results if r['total_request_time_s']]):.3f}s")