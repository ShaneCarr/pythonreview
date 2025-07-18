import httpx
import time
import brotli
import gzip

# ----------- Config -------------
URL = 'http://localhost:6666/graphql?operationName=FeedGroupNestedClients&apiVnext=2'
TOKEN_FILE = 'token.json'
PAYLOAD_FILE = 'payload.json'

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

# Load Bearer token as plain text
with open(TOKEN_FILE, 'r') as tf:
    token = tf.read().strip()
BASE_HEADERS["Authorization"] = f"Bearer {token}"

# Load full payload as-is (for exact match)
with open(PAYLOAD_FILE, 'rb') as pf:
    payload_bytes = pf.read()

# Run compression tests
for enc, label in ACCEPT_ENCODINGS.items():
    print(f"\n=== Testing {label} compression ===")

    headers = BASE_HEADERS.copy()
    headers.update({
        "Accept-Encoding": enc,
        "Accept": "application/json",
        "Origin": "https://web.c5devlab8.labs.yammer.dev",
        "Referer": "https://web.c5devlab8.labs.yammer.dev/main/groups/eyJfdHlwZSI6Ikdyb3VwIiwiaWQiOiIzMzcxMDA4MSJ9/all",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:139.0) Gecko/20100101 Firefox/139.0"
    })

    with httpx.Client(http2=False, timeout=10.0) as client:
        start = time.time()
        #response = client.post(URL, headers=headers, content=payload_bytes)

        transport = httpx.HTTPTransport()

        with httpx.Client(http2=False, timeout=10.0, transport=transport) as client:
            start = time.time()
            with client.stream("POST", URL, headers=headers, content=payload_bytes) as response:
                compressed_bytes = b"".join(response.iter_raw())

            elapsed = time.time() - start

        elapsed = time.time() - start

       # compressed_bytes = response.content
        compressed_kb = len(compressed_bytes) / 1024
        content_encoding = response.headers.get("Content-Encoding", "none")

        print(f"Status: {response.status_code}")
        print(f"Time: {elapsed * 1000:.2f} ms")
        print(f"Content-Encoding: {content_encoding}")
        print(f"Compressed size: {compressed_kb:.2f} KB")
        print(f"Response headers:\n{response.headers}")

        # Attempt decompression if needed
        try:
            if enc == "br" and content_encoding == "br":
                decompressed = brotli.decompress(compressed_bytes)
            elif enc == "gzip" and content_encoding == "gzip":
                decompressed = gzip.decompress(compressed_bytes)
            elif enc == "identity" or content_encoding in ["identity", "none", ""]:
                decompressed = compressed_bytes
            else:
                print("⚠️  Unexpected or missing Content-Encoding, skipping decompression.")
                decompressed = compressed_bytes

            print(f"Decompressed size: {len(decompressed)/1024:.2f} KB")
        except Exception as e:
            print(f"Decompression failed: {e}")
