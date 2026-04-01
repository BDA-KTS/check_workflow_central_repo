import json

try:
    with open("methods.json", encoding="utf-8") as f:
        methods_data = json.load(f)

    with open("tutorials.json", encoding="utf-8") as f:
        tutorials_data = json.load(f)

    all_entries = (
        methods_data.get("software_source_codes", [])
        + methods_data.get("tutorials", [])
        + tutorials_data.get("tutorials", [])
    )

    unique_top_level_tasks = sorted({
        task
        for entry in all_entries
        for task in entry.get("top_level_tasks", [])
    })

    print(unique_top_level_tasks)

except FileNotFoundError as e:
    print(f"Datei nicht gefunden: {e}")
except json.JSONDecodeError as e:
    print(f"Ungültiges JSON: {e}")