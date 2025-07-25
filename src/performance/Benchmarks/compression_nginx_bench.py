import httpx
import time
import brotli
import os
import gzip
import json
import numpy as np
import pandas as pd

# ----------- Config -------------
URL = 'http://localhost:6666/graphql?operationName=FeedGroupNestedClients&apiVnext=2'
TOKEN_FILE = 'token.json'
PAYLOAD_FILE = 'payload.json'
N_RUNS = 20

# Custom compression levels per encoding
ENCODING_LEVELS = {
    "br": 4,         # Brotli compression level
    "gzip": 6,       # Gzip compression level
    "identity": 0    # No compression
}

ACCEPT_ENCODINGS = {
    "br": "Brotli",
    "gzip": "Gzip",
    "identity": "None (Plain)"
}

BASE_HEADERS = {
    "Content-Type": "application/json",
    "x-request-id": "compression-test-bench"
}
# --------------------------------

# Load Bearer token
with open(TOKEN_FILE, 'r') as tf:
    token = tf.read().strip()
BASE_HEADERS["Authorization"] = f"Bearer {token}"

# Load payload
with open(PAYLOAD_FILE, 'rb') as pf:
    payload_bytes = pf.read()

# Results accumulator
all_results = []

# Run compression tests
for enc, label in ACCEPT_ENCODINGS.items():
    print(f"\n=== Testing {label} compression ({enc}) ===")

    level = str(ENCODING_LEVELS.get(enc, 4))  # Use custom level or fallback

    headers = BASE_HEADERS.copy()
    headers.update({
        "Accept-Encoding": enc,
        "X-Compression-Level": level,  # custom header
        "Accept": "application/json",
        "Origin": "https://web.c5devlab3.labs.yammer.dev",
        "Referer": "https://web.c5devlab3.labs.yammer.dev/main/groups/eyJfdHlwZSI6Ikdyb3VwIiwiaWQiOiIzMzcxMDA4MSJ9/all",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:139.0) Gecko/20100101 Firefox/139.0"
    })

    for i in range(N_RUNS):
        try:
            transport = httpx.HTTPTransport()
            with httpx.Client(http2=False, timeout=10.0, transport=transport) as client:
                start = time.time()
                with client.stream("POST", URL, headers=headers, content=payload_bytes) as response:
                    compressed_bytes = b"".join(response.iter_raw())
                elapsed = time.time() - start

            content_encoding = response.headers.get("Content-Encoding", "none")
            reported_level = response.headers.get("X-Compression-Level", "unknown")
            reported_codec = response.headers.get("X-Compression-Codec", content_encoding)

            compressed_kb = len(compressed_bytes) / 1024

            # Decompress
            try:
                if enc == "br" and content_encoding == "br":
                    decompressed = brotli.decompress(compressed_bytes)
                elif enc == "gzip" and content_encoding == "gzip":
                    decompressed = gzip.decompress(compressed_bytes)
                elif enc == "identity" or content_encoding in ["identity", "none", ""]:
                    decompressed = compressed_bytes
                else:
                    decompressed = compressed_bytes
            except Exception as e:
                decompressed = b""
                print(f"[{enc} run {i}] Decompression error: {e}")

            decompressed_kb = len(decompressed) / 1024
            compression_ratio = decompressed_kb / compressed_kb if compressed_kb else None

            all_results.append({
                "Encoding": label,
                "Run": i,
                "Status": response.status_code,
                "Time_ms": elapsed * 1000,
                "Compressed_KB": compressed_kb,
                "Decompressed_KB": decompressed_kb,
                "Compression_Ratio": compression_ratio,
                "Content-Encoding": content_encoding,
                "Reported-Level": reported_level,
                "Reported-Codec": reported_codec,
                "network": "wifi"
            })

        except Exception as e:
            print(f"[{enc} run {i}] Request error: {e}")
            # all_results.append({
            #     "Encoding": label,
            #     "Run": i,
            #     "Status": "ERR",
            #     "Time_ms": None,
            #     "Compressed_KB": None,
            #     "Decompressed_KB": None,
            #     "Compression_Ratio": None,
            #     "Content-Encoding": None,
            #     "Reported-Level": None,
            #     "Reported-Codec": None
            # })

# Output analysis
df = pd.DataFrame(all_results)
df = df[[
    "Encoding", "Run", "Status", "Time_ms",
    "Compressed_KB", "Decompressed_KB", "Compression_Ratio",
    "Content-Encoding", "Reported-Level", "Reported-Codec", "network"
]]

# Save to CSV
#df.to_csv("compression_benchmark_results.csv", index=False)

csv_file = "compression_benchmark_results.csv"
write_header = not os.path.exists(csv_file)  # Only write header if file doesn't exist
df.to_csv(csv_file, mode='a', header=write_header, index=False)

# Print errors
error_summary = df[df["Status"] == "ERR"].groupby("Encoding").size()
print("\n=== Error Counts by Encoding ===")
if error_summary.empty:
    print("No errors encountered in any run.")
else:
    print(error_summary)

# Percentile summary
percentile_summary = (
    df[df["Time_ms"].notnull()]
    .groupby("Encoding")["Time_ms"]
    .describe(percentiles=[0.25, 0.5, 0.75, 0.95, 0.99])
    .round(2)
)
print("\n=== Percentile Summary (ms) ===")
print(percentile_summary[["mean", "std", "25%", "50%", "75%", "95%", "99%"]])