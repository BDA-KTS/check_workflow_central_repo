import json
from pathlib import Path
from typing import Any
import matplotlib.pyplot as plt
import pandas as pd

REQUIRED_COLUMNS = {
    "owner",
    "repo",
    "name",
    "passed",
    "warning_labels",
    "error_labels",
    "Workflow Duration",
}

def load_jsonl(path: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_no}: {exc}") from exc

    if not rows:
        raise ValueError("The JSONL file is empty.")

    df = pd.DataFrame(rows)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            "Missing required columns: " + ", ".join(sorted(missing))
        )

    return df
def plot_summary_passed(df_sum):
    counts = df_sum["passed"].value_counts().sort_index()
    total = counts.sum()

    ax = counts.plot(kind="bar", color=["tab:red", "tab:green"])
    ax.set_title("How many Workflows passed?")
    ax.set_xlabel("Passed")
    ax.set_ylabel("Count")
    ax.set_xticklabels(["False", "True"], rotation=0)

    for i, count in enumerate(counts):
        pct = count / total * 100
        ax.text(
            i,
            count + 0.02 * counts.max(),
            f"{count}\n({pct:.1f}%)",
            ha="center",
            va="bottom",
        )

    ax.set_ylim(0, counts.max() * 1.3)
    plt.tight_layout()
    plt.show()


def plot_summary_label_states(df_summary):
    def has_label(labels, needle: str) -> bool:
        if not isinstance(labels, list):
            return False
        return any(needle.lower() in str(label).lower() for label in labels)

    warning_has = df_summary["error_labels"].apply(lambda labels: has_label(labels, "warning"))
    error_has = df_summary["error_labels"].apply(lambda labels: has_label(labels, "critical"))

    categories = {
        "No warnings / No errors": ((~warning_has) & (~error_has)).sum(),
        "Warnings only": (warning_has & (~error_has)).sum(),
        "Errors only": ((~warning_has) & error_has).sum(),
    }

    ax = plt.gca()
    bars = ax.bar(
        categories.keys(),
        categories.values(),
        color=["tab:green", "tab:orange", "tab:red", "tab:purple"],
    )
    ax.set_title("Summary label states")
    ax.set_xlabel("Category")
    ax.set_ylabel("Count")
    plt.xticks(rotation=20, ha="right")

    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            str(int(height)),
            ha="center",
            va="bottom",
        )
    plt.tight_layout()
    plt.show()


df = load_jsonl(Path("report_jsonl/merged.jsonl"))
#print(df)

df_summary = df[df["name"] == "Summary"]
plot_summary_passed(df_summary)
plot_summary_label_states(df_summary)
