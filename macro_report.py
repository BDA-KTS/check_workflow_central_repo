import json
from pathlib import Path
from typing import Any, Counter
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
    plt.savefig("plots/plotsummary_passed.png", dpi=300, bbox_inches="tight")
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
    plt.savefig("plots/plotsummary_label_states.png", dpi=300, bbox_inches="tight")
    plt.show()

def plot_filecheck_passed(df_filecheck):
    counts = df_filecheck["passed"].value_counts().sort_index()
    total = counts.sum()

    ax = counts.plot(kind="bar", color=["tab:red", "tab:green"])
    ax.set_title("File Check: Passed vs Failed")
    ax.set_xlabel("Passed")
    ax.set_ylabel("Count")
    ax.set_xticklabels(["False", "True"], rotation=0)

    for i, count in enumerate(counts):
        pct = count / total * 100
        ax.text(i, count + 0.02 * counts.max(), f"{count}\n({pct:.1f}%)",
                ha="center", va="bottom")

    ax.set_ylim(0, counts.max() * 1.3)
    plt.tight_layout()
    plt.savefig("plots/filecheck_passed.png", dpi=300, bbox_inches="tight")
    plt.show()

def plot_filecheck_label_states(df_filecheck):
    def has_any(labels) -> bool:
        return isinstance(labels, list) and len(labels) > 0

    warning_has = df_filecheck["warning_labels"].apply(has_any)
    error_has = df_filecheck["error_labels"].apply(has_any)

    categories = {
        "No warnings / No errors": ((~warning_has) & (~error_has)).sum(),
        "Warnings only": (warning_has & (~error_has)).sum(),
        "Errors only": ((~warning_has) & error_has).sum(),
        "Warnings + Errors": (warning_has & error_has).sum(),
    }

    ax = plt.gca()
    bars = ax.bar(categories.keys(), categories.values(),
                  color=["tab:green", "tab:orange", "tab:red", "tab:purple"])
    ax.set_title("File Check: Label States")
    ax.set_xlabel("Category")
    ax.set_ylabel("Count")
    plt.xticks(rotation=20, ha="right")

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height, str(int(height)),
                ha="center", va="bottom")

    plt.tight_layout()
    plt.savefig("plots/filecheck_label_state.png", dpi=300, bbox_inches="tight")
    plt.show()

def plot_warning_labels(df_filecheck):
    labels = []
    for item in df_filecheck["warning_labels"].dropna():
        if isinstance(item, list):
            labels.extend(item)

    if not labels:
        print("No warning labels found.")
        return

    counts = Counter(labels)
    labels_sorted = dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    plt.figure(figsize=(10, 5))
    plt.bar(labels_sorted.keys(), labels_sorted.values(), color="tab:orange")
    plt.title("Warning Labels in File Check")
    plt.xlabel("Warning Label")
    plt.ylabel("Count")
    plt.xticks(rotation=30, ha="right")

    for i, v in enumerate(labels_sorted.values()):
        plt.text(i, v + 0.05, str(v), ha="center", va="bottom")

    plt.tight_layout()
    plt.savefig("plots/filecheck_warning_labels.png", dpi=300, bbox_inches="tight")
    plt.show()


def plot_error_labels(df_filecheck):
    labels = []
    for item in df_filecheck["error_labels"].dropna():
        if isinstance(item, list):
            labels.extend(item)

    if not labels:
        print("No error labels found.")
        return

    counts = Counter(labels)
    labels_sorted = dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    plt.figure(figsize=(10, 5))
    plt.bar(labels_sorted.keys(), labels_sorted.values(), color="tab:red")
    plt.title("Error Labels in File Check")
    plt.xlabel("Error Label")
    plt.ylabel("Count")
    plt.xticks(rotation=30, ha="right")

    for i, v in enumerate(labels_sorted.values()):
        plt.text(i, v + 0.05, str(v), ha="center", va="bottom")

    plt.tight_layout()
    plt.savefig("plots/filecheck_error_labels.png", dpi=300, bbox_inches="tight")
    plt.show()

def plot_licensecheck_passed(df_licensecheck):
    counts = df_licensecheck["passed"].value_counts().sort_index()
    total = counts.sum()

    ax = counts.plot(kind="bar", color=["tab:red", "tab:green"])
    ax.set_title("License Check: Passed vs Failed")
    ax.set_xlabel("Passed")
    ax.set_ylabel("Count")
    ax.set_xticklabels(["False", "True"], rotation=0)

    for i, count in enumerate(counts):
        pct = count / total * 100
        ax.text(i, count + 0.02 * counts.max(), f"{count}\n({pct:.1f}%)",
                ha="center", va="bottom")

    ax.set_ylim(0, counts.max() * 1.3)
    plt.tight_layout()
    plt.savefig("plots/licensecheck_passed.png", dpi=300, bbox_inches="tight")
    plt.show()

def plot_licensecheck_label_states(df_licensecheck):
    def has_any(labels) -> bool:
        return isinstance(labels, list) and len(labels) > 0

    warning_has = df_licensecheck["warning_labels"].apply(has_any)
    error_has = df_licensecheck["error_labels"].apply(has_any)

    categories = {
        "No warnings / No errors": ((~warning_has) & (~error_has)).sum(),
        "Warnings only": (warning_has & (~error_has)).sum(),
        "Errors only": ((~warning_has) & error_has).sum(),
        "Warnings + Errors": (warning_has & error_has).sum(),
    }

    ax = plt.gca()
    bars = ax.bar(
        categories.keys(),
        categories.values(),
        color=["tab:green", "tab:orange", "tab:red", "tab:purple"],
    )
    ax.set_title("License Check: Label States")
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
    plt.savefig("plots/licensecheck_label_states.png", dpi=300, bbox_inches="tight")
    plt.show()

def plot_licensecheck_warning_labels(df_licensecheck):
    labels = []
    for item in df_licensecheck["warning_labels"].dropna():
        if isinstance(item, list):
            labels.extend(item)

    if not labels:
        print("No warning labels found for License Check.")
        return

    counts = Counter(labels)
    labels_sorted = dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    plt.figure(figsize=(10, 5))
    plt.bar(labels_sorted.keys(), labels_sorted.values(), color="tab:orange")
    plt.title("License Check: Warning Labels")
    plt.xlabel("Warning Label")
    plt.ylabel("Count")
    plt.xticks(rotation=30, ha="right")

    for i, v in enumerate(labels_sorted.values()):
        plt.text(i, v + 0.05, str(v), ha="center", va="bottom")

    plt.tight_layout()
    plt.savefig("plots/licensecheck_warning_labels.png", dpi=300, bbox_inches="tight")
    plt.show()

def plot_licensecheck_error_labels(df_licensecheck):
    labels = []
    for item in df_licensecheck["error_labels"].dropna():
        if isinstance(item, list):
            labels.extend(item)

    if not labels:
        print("No error labels found for License Check.")
        return

    counts = Counter(labels)
    labels_sorted = dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    plt.figure(figsize=(10, 5))
    plt.bar(labels_sorted.keys(), labels_sorted.values(), color="tab:red")
    plt.title("License Check: Error Labels")
    plt.xlabel("Error Label")
    plt.ylabel("Count")
    plt.xticks(rotation=30, ha="right")

    for i, v in enumerate(labels_sorted.values()):
        plt.text(i, v + 0.05, str(v), ha="center", va="bottom")

    plt.tight_layout()
    plt.savefig("plots/licensecheck_error_labels.png", dpi=300, bbox_inches="tight")
    plt.show()

def plot_readmecheck_passed(df_readmecheck):
    counts = df_readmecheck["passed"].value_counts().sort_index()
    total = counts.sum()

    ax = counts.plot(kind="bar", color=["tab:red", "tab:green"])
    ax.set_title("Readme Check: Passed vs Failed")
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
    plt.savefig("plots/readme_passed.png", dpi=300, bbox_inches="tight")
    plt.show()

def plot_readmecheck_label_states(df_readmecheck):
    def has_any(labels) -> bool:
        return isinstance(labels, list) and len(labels) > 0

    warning_has = df_readmecheck["warning_labels"].apply(has_any)
    error_has = df_readmecheck["error_labels"].apply(has_any)

    categories = {
        "No warnings / No errors": ((~warning_has) & (~error_has)).sum(),
        "Warnings only": (warning_has & (~error_has)).sum(),
        "Errors only": ((~warning_has) & error_has).sum(),
        "Warnings + Errors": (warning_has & error_has).sum(),
    }

    ax = plt.gca()
    bars = ax.bar(
        categories.keys(),
        categories.values(),
        color=["tab:green", "tab:orange", "tab:red", "tab:purple"],
    )
    ax.set_title("Readme Check: Label States")
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
    plt.savefig("plots/readme_label_states.png", dpi=300, bbox_inches="tight")
    plt.show()

def plot_readmecheck_warning_labels(df_readmecheck):
    labels = []
    for item in df_readmecheck["warning_labels"].dropna():
        if isinstance(item, list):
            labels.extend(item)

    if not labels:
        print("No warning labels found for Readme Check.")
        return

    counts = Counter(labels)
    labels_sorted = dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    plt.figure(figsize=(10, 5))
    plt.bar(labels_sorted.keys(), labels_sorted.values(), color="tab:orange")
    plt.title("Readme Check: Warning Labels")
    plt.xlabel("Warning Label")
    plt.ylabel("Count")
    plt.xticks(rotation=30, ha="right")

    for i, v in enumerate(labels_sorted.values()):
        plt.text(i, v + 0.05, str(v), ha="center", va="bottom")

    plt.tight_layout()
    plt.savefig("plots/readme_warning_labels.png", dpi=300, bbox_inches="tight")
    plt.show()

def plot_readmecheck_error_labels(df_readmecheck):
    labels = []
    for item in df_readmecheck["error_labels"].dropna():
        if isinstance(item, list):
            labels.extend(item)

    if not labels:
        print("No error labels found for Readme Check.")
        return

    counts = Counter(labels)
    labels_sorted = dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    plt.figure(figsize=(10, 5))
    plt.bar(labels_sorted.keys(), labels_sorted.values(), color="tab:red")
    plt.title("Readme Check: Error Labels")
    plt.xlabel("Error Label")
    plt.ylabel("Count")
    plt.xticks(rotation=30, ha="right")

    for i, v in enumerate(labels_sorted.values()):
        plt.text(i, v + 0.05, str(v), ha="center", va="bottom")

    plt.tight_layout()
    plt.savefig("plots/readme_error_labels.png", dpi=300, bbox_inches="tight")
    plt.show()

def plot_bindertest_passed(df_bindertest):
    counts = df_bindertest["passed"].value_counts().sort_index()
    total = counts.sum()

    ax = counts.plot(kind="bar", color=["tab:red", "tab:green"])
    ax.set_title("Binder Test: Passed vs Failed")
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
    plt.savefig("plots/bindertest_passed.png", dpi=300, bbox_inches="tight")
    plt.show()

def parse_duration_to_seconds(duration: str) -> int:
    minutes, seconds = duration.split(":")
    return int(minutes) * 60 + int(seconds)

def plot_summary_duration(df):
    df_summary = df[df["name"] == "Summary"].copy()
    df_summary["duration_seconds"] = df_summary["Workflow Duration"].apply(parse_duration_to_seconds)

    plt.figure(figsize=(8, 5))
    plt.hist(df_summary["duration_seconds"], bins=10, color="tab:blue", edgecolor="black")
    plt.title("Workflow Duration from Summary")
    plt.xlabel("Duration (seconds)")
    plt.ylabel("Number of repos")
    plt.tight_layout()
    plt.savefig("plots/average_duration.png", dpi=300, bbox_inches="tight")
    plt.show()

df = load_jsonl(Path("report_jsonl/merged.jsonl"))
#print(df)

df_summary = df[df["name"] == "Summary"]
plot_summary_passed(df_summary)
plot_summary_label_states(df_summary)

df_filecheck = df[df["name"] == "File Check"]
plot_filecheck_passed(df_filecheck)
plot_filecheck_label_states(df_filecheck)
plot_warning_labels(df_filecheck)
plot_error_labels(df_filecheck)

df_licensecheck = df[df["name"] == "License Check"]

plot_licensecheck_passed(df_licensecheck)
plot_licensecheck_label_states(df_licensecheck)
plot_licensecheck_warning_labels(df_licensecheck)
plot_licensecheck_error_labels(df_licensecheck)

df_readmecheck = df[df["name"] == "Readme Check"]
plot_readmecheck_passed(df_readmecheck)
plot_readmecheck_label_states(df_readmecheck)
plot_readmecheck_warning_labels(df_readmecheck)
plot_readmecheck_error_labels(df_readmecheck)

df_bindertest = df[df["name"] == "Binder Test"]
plot_bindertest_passed(df_bindertest)
plot_summary_duration(df)