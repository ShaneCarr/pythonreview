import gzip, brotli, hashlib, time, resource, csv, psutil, os
from pathlib import Path
from datetime import datetime

# === Settings ===
RUNS_PER_LEVEL = 20
GZIP_LEVELS = range(1, 10)
BROTLI_LEVELS = range(1, 10)
# Simulated network bandwidths in bits per second
# These are used to estimate network transfer time using:
#
#     transfer_time_ms = (compressed_size_bytes * 8) / bandwidth_bps * 1000
#
# Explanation:
#   - compressed_size_bytes * 8 → converts bytes to bits
#   - divide by bandwidth (bps) → gives time in seconds
#   - multiply by 1000 → converts to milliseconds

NETWORK_PROFILES = {
    "3G": 400_000,        # ~400 Kbps, conservative estimate for mobile 3G
    "4G": 10_000_000,     # ~10 Mbps, reasonable baseline for LTE
    "WiFi": 100_000_000   # ~100 Mbps, lower-end home or enterprise Wi-Fi
}

# Say the payload is 10,000 bytes (10 KB) and bandwidth is 1 Mbps = 1,000,000 bits/sec:
# (10_000 bytes * 8 bits/byte) / 1_000_000 bps = 0.08 seconds = 80 ms
# === Utilities ===
def md5(data):
    return hashlib.md5(data).hexdigest()

def get_memory_usage_kb():
    return psutil.Process(os.getpid()).memory_info().rss / 1024

def compress_and_report(label, data, compress_fn):
    total_time = 0
    total_user_cpu = 0
    total_sys_cpu = 0
    compressed_size = None
    integrity = "PASS"

    for _ in range(RUNS_PER_LEVEL):
        start = time.perf_counter()
        ru_start = resource.getrusage(resource.RUSAGE_SELF)

        compressed = compress_fn(data)

        ru_end = resource.getrusage(resource.RUSAGE_SELF)
        end = time.perf_counter()

        total_time += (end - start)
        total_user_cpu += (ru_end.ru_utime - ru_start.ru_utime)
        total_sys_cpu += (ru_end.ru_stime - ru_start.ru_stime)

        if compressed_size is None:
            compressed_size = len(compressed)
            try:
                if label.startswith("Gzip"):
                    decompressed = gzip.decompress(compressed)
                else:
                    decompressed = brotli.decompress(compressed)
                if md5(decompressed) != md5(data):
                    integrity = "FAIL"
            except Exception as e:
                integrity = f"ERROR ({str(e)})"

    mem_kb = get_memory_usage_kb()
    avg_time_ms = (total_time / RUNS_PER_LEVEL) * 1000
    avg_user_cpu_ms = (total_user_cpu / RUNS_PER_LEVEL) * 1000
    avg_sys_cpu_ms = (total_sys_cpu / RUNS_PER_LEVEL) * 1000

    # Network transfer time estimates (ms)
    network_costs = {
        net: (compressed_size * 8 / bps) * 1000
        for net, bps in NETWORK_PROFILES.items()
    }

    return {
        "label": label,
        "algo": "gzip" if "Gzip" in label else "brotli",
        "level": int(label.split()[-1]),
        "orig_size_bytes": len(data),
        "compressed_bytes": compressed_size,
        "compression_ratio": round(len(data) / compressed_size, 2),
        "avg_wall_time_ms": round(avg_time_ms, 2),
        "avg_user_cpu_ms": round(avg_user_cpu_ms, 2),
        "avg_sys_cpu_ms": round(avg_sys_cpu_ms, 2),
        "mem_kb": round(mem_kb, 2),
        "net_3g_ms": round(network_costs["3G"], 2),
        "net_4g_ms": round(network_costs["4G"], 2),
        "net_wifi_ms": round(network_costs["WiFi"], 2),
        "total_3g_time_ms": round(avg_time_ms + network_costs["3G"], 2),
        "total_4g_time_ms": round(avg_time_ms + network_costs["4G"], 2),
        "total_wifi_time_ms": round(avg_time_ms + network_costs["WiFi"], 2),
        "integrity": integrity
    }

# === Main Run ===
def main():
    input_path = "response.json"
    output_prefix = "compression_compare"

    data = Path(input_path).read_bytes()
    results = []

    for level in GZIP_LEVELS:
        label = f"Gzip Level {level}"
        compress_fn = lambda d: gzip.compress(d, compresslevel=level)
        results.append(compress_and_report(label, data, compress_fn))

    for level in BROTLI_LEVELS:
        label = f"Brotli Level {level}"
        compress_fn = lambda d: brotli.compress(d, quality=level)
        results.append(compress_and_report(label, data, compress_fn))

    # Write results
    timestamp = datetime.now().isoformat(timespec="seconds").replace(":", "-")
    output_file = f"{output_prefix}_{timestamp}.csv"

    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Results written to: {output_file}")

if __name__ == "__main__":
    main()