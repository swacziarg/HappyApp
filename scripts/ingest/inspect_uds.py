import json
from pathlib import Path
import pprint

def main():
    repo_root = Path(__file__).resolve().parents[2]

    uds_dir = (
        repo_root
        / "data"
        / "raw"
        / "garmin_export_2025-12-31"
        / "DI_CONNECT"
        / "DI-Connect-Aggregator"
    )

    matches = list(uds_dir.glob("UDSFile_*.json"))
    if not matches:
        raise FileNotFoundError("No UDSFile found")

    records = json.load(open(matches[0]))

    for r in records:
        # Look for a record after you got the watch
        if r.get("calendarDate") >= "2025-09-15":
            pprint.pprint(r)
            break


if __name__ == "__main__":
    main()
