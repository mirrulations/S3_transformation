import re
from datetime import datetime, timedelta

LOG_FILE = "script_output.log"
TOTAL_FILES = 25239435
MOVED_PATTERN = re.compile(r"✔ Moved:")

def parse_moved_timestamps(log_file):
    timestamps = []

    with open(log_file, "r") as f:
        for line in f:
            if MOVED_PATTERN.search(line):
                # Extract timestamp from the beginning of the line
                timestamp_str = line.split(" - ")[0]
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
                    timestamps.append(timestamp)
                except ValueError:
                    continue  # Skip malformed timestamps

    return timestamps

def estimate_remaining_time(timestamps):
    if len(timestamps) < 2:
        return None, None, len(timestamps)

    first = timestamps[0]
    last = timestamps[-1]
    duration = (last - first).total_seconds()
    moves_done = len(timestamps)
    avg_time_per_move = duration / moves_done
    moves_remaining = TOTAL_FILES - moves_done
    est_time_remaining_sec = avg_time_per_move * moves_remaining

    return timedelta(seconds=est_time_remaining_sec), timedelta(seconds=duration), moves_done

def main():
    timestamps = parse_moved_timestamps(LOG_FILE)
    est_remaining, total_elapsed, moved = estimate_remaining_time(timestamps)

    if est_remaining is None:
        print("❗ Not enough data to estimate time remaining.")
    else:
        remaining = TOTAL_FILES - moved
        print(f"📦 Total files moved: {moved:,}")
        print(f"🕐 Files remaining: {remaining:,} out of {TOTAL_FILES:,}")
        print(f"⏱️  Total elapsed time: {str(total_elapsed).split('.')[0]}")
        print(f"⏳ Estimated time remaining: {str(est_remaining).split('.')[0]}")

if __name__ == "__main__":
    main()
