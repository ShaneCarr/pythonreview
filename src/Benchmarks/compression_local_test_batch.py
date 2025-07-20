import gzip, brotli, hashlib, time, resource, csv, psutil, os
from pathlib import Path
from datetime import datetime

# === Settings ===
RUNS_PER_LEVEL = 20
GZIP_LEVELS = range(1, 10)
BROTLI_LEVELS = range(1, 10)

NETWORK_PROFILES = {
    "3G": 400_000,
    "4G": 10_000_000,
    "WiFi": 100_000_000
}

# === Utilities ===
def md5(data):
    return hashlib.md5(data).hexdigest()

def get_memory_usage_kb():
    # It's better to get process once outside the loop for slight efficiency
    # But for a script that runs relatively quickly per payload, this is fine.
    # For very long-running processes, consider making `process` a global or
    # passing it around, or caching it. For now, this is okay.
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
        #amount of time the CPU spent actively executing instructions in user mode
        total_user_cpu += (ru_end.ru_utime - ru_start.ru_utime)
        #measures the amount of time the CPU spent executing instructions in kernel
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

    # Memory usage is captured once per label/level test, which is fine
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
    # Define the directory where your payload files are located
    payloads_dir = Path("payloads") # Assuming a 'payloads' folder in the same directory

    # Define the output prefix for your CSV files
    output_prefix = "compression_compare"

    # Initialize an empty list to store all results from all payloads
    all_results = []

    # Get a list of all JSON files in the payloads directory
    # We use .rglob("*.json") to find JSON files recursively in subdirectories too
    # if you organize them that way, or just .glob("*.json") for just the top level.
    # For now, let's stick with .glob for simplicity based on our folder structure.
    payload_files = sorted(payloads_dir.glob("*.json")) # Sort for consistent order

    if not payload_files:
        print(f"❌ No JSON payload files found in '{payloads_dir}'. Please ensure your 'payloads' folder exists and contains .json files.")
        return

    print(f"📊 Starting compression analysis for {len(payload_files)} payloads...")

    # Loop through each payload file
    for input_path in payload_files:
        payload_name = input_path.stem # Get filename without extension (e.g., "response_small_group")
        print(f"\nProcessing payload: {payload_name} ({input_path})")

        # Read the payload data
        try:
            data = input_path.read_bytes()
        except Exception as e:
            print(f"❗ Error reading {input_path}: {e}")
            continue # Skip to the next payload

        # Temporary list to store results for the current payload
        current_payload_results = []

        # Run Gzip tests for the current payload
        for level in GZIP_LEVELS:
            label = f"Gzip Level {level}"
            compress_fn = lambda d: gzip.compress(d, compresslevel=level)
            result = compress_and_report(label, data, compress_fn)
            result["payload_name"] = payload_name # Add payload identifier
            current_payload_results.append(result)
            print(f"  {label}: Compressed Size={result['compressed_bytes']} bytes, Wall Time={result['avg_wall_time_ms']:.2f} ms")


        # Run Brotli tests for the current payload
        for level in BROTLI_LEVELS:
            label = f"Brotli Level {level}"
            compress_fn = lambda d: brotli.compress(d, quality=level)
            result = compress_and_report(label, data, compress_fn)
            result["payload_name"] = payload_name # Add payload identifier
            current_payload_results.append(result)
            print(f"  {label}: Compressed Size={result['compressed_bytes']} bytes, Wall Time={result['avg_wall_time_ms']:.2f} ms")

        # Add results for the current payload to the master list
        all_results.extend(current_payload_results)

    # Write all results to a single CSV file
    timestamp = datetime.now().isoformat(timespec="seconds").replace(":", "-")
    output_file = f"{output_prefix}_{timestamp}.csv"

    # Ensure all_results is not empty before attempting to write
    if not all_results:
        print("🛑 No results were generated. Exiting.")
        return

    # Dynamically determine fieldnames from the first result entry,
    # ensuring 'payload_name' is included and is the first column.
    fieldnames = ["payload_name"] + [key for key in all_results[0].keys() if key != "payload_name"]

    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)

    print(f"\n✅ All results for all payloads written to: {output_file}")

if __name__ == "__main__":
    main()