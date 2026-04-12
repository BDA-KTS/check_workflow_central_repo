import json
from pathlib import Path

aggregation_dir = Path("aggregation")
output_dir = Path("report_jsonl")
output_dir.mkdir(parents=True, exist_ok=True)
output_file = output_dir / "merged.jsonl"

if not aggregation_dir.exists():
    raise SystemExit(f"Aggregation directory not found: {aggregation_dir}")

count = 0

with output_file.open("w", encoding="utf-8") as out:
    for data_file in aggregation_dir.rglob("*"):
        if data_file.suffix.lower() not in {".json", ".jsonl"}:
            continue

        try:
            if data_file.suffix.lower() == ".jsonl":
                with data_file.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        row = json.loads(line)
                        out.write(json.dumps(row, ensure_ascii=False) + "\n")
                        count += 1
            else:
                with data_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                if isinstance(data, list):
                    for item in data:
                        out.write(json.dumps(item, ensure_ascii=False) + "\n")
                        count += 1
                else:
                    out.write(json.dumps(data, ensure_ascii=False) + "\n")
                    count += 1

        except json.JSONDecodeError as e:
            print(f"Skipping invalid file: {data_file} ({e})")
        except Exception as e:
            print(f"Skipping file {data_file}: {e}")

print(f"Written {count} records to {output_file}")