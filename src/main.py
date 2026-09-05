"""
Social Media Moderation Analytics Pipeline

Portfolio version of the moderation analytics backend.

Key features:
- Load four social-media CSV datasets
- Clean and validate records
- Exclude bot accounts from human-behaviour analysis
- Merge related datasets
- Save a nested JSON backup
- Calculate engagement statistics
- Generate pivot, correlation, heatmap and categorical visualisations
- Record audit events
- Measure pipeline stage latency for reproducibility and performance review
"""

import json
from pathlib import Path
from time import perf_counter

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


BASE_PATH = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_PATH / "raw_data"
OUTPUT_PATH = BASE_PATH / "outputs"
OUTPUT_PATH.mkdir(exist_ok=True)

AUDIT_FILE = BASE_PATH / "audit_log.txt"
JSON_BACKUP = BASE_PATH / "moderation_backup.json"

_DATA_CACHE = None


def write_audit(message: str) -> None:
    """Append a message to the audit log."""
    with open(AUDIT_FILE, "a", encoding="utf-8") as file:
        file.write(message + "\n")


def timed_stage(name: str, function, *args, **kwargs):
    """Run a function and return its result together with elapsed seconds."""
    start = perf_counter()
    result = function(*args, **kwargs)
    elapsed = perf_counter() - start
    write_audit(f"{name} completed in {elapsed:.4f} seconds.")
    return result, elapsed


def load_data():
    """Load the four source CSV datasets."""
    files = {
        "USERS": DATA_PATH / "USERS.csv",
        "POSTS": DATA_PATH / "POSTS.csv",
        "INTERACTIONS": DATA_PATH / "INTERACTIONS.csv",
        "TOPICS": DATA_PATH / "TOPICS.csv",
    }

    missing = [str(path) for path in files.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing required dataset file(s):\n" + "\n".join(missing)
        )

    users = pd.read_csv(files["USERS"], encoding="latin1")
    posts = pd.read_csv(files["POSTS"], encoding="latin1")
    interactions = pd.read_csv(files["INTERACTIONS"], encoding="latin1")
    topics = pd.read_csv(files["TOPICS"], encoding="latin1")

    write_audit("Loaded USERS, POSTS, INTERACTIONS and TOPICS datasets.")
    return users, posts, interactions, topics


def clean_data(raw_data=None):
    """Clean datasets and prepare human-only analysis data."""
    if raw_data is None:
        raw_data = load_data()

    users, posts, interactions, topics = raw_data

    users_clean = users.copy()
    posts_clean = posts.copy()
    interactions_clean = interactions.copy()
    topics_clean = topics.copy()

    users_clean["account_type"] = (
        users_clean["account_type"].astype(str).str.lower().str.strip()
    )
    topics_clean["moderation_level"] = (
        topics_clean["moderation_level"].astype(str).str.lower().str.strip()
    )
    interactions_clean["interaction_type"] = (
        interactions_clean["interaction_type"].astype(str).str.lower().str.strip()
    )

    posts_clean = posts_clean.rename(
        columns={"text_preview": "content_preview"}
    )

    if "location" in users_clean.columns:
        users_clean["location"] = users_clean["location"].fillna("Unknown")

    posts_clean["content_preview"] = (
        posts_clean["content_preview"].fillna("No content")
    )
    posts_clean["topic_id"] = posts_clean["topic_id"].fillna("Unknown")
    posts_clean["language"] = posts_clean["language"].fillna("Unknown")
    interactions_clean["reaction_type"] = (
        interactions_clean["reaction_type"].fillna("None")
    )

    posts_clean["timestamp"] = pd.to_datetime(
        posts_clean["timestamp"], format="mixed", errors="coerce"
    )
    interactions_clean["timestamp"] = pd.to_datetime(
        interactions_clean["timestamp"], format="mixed", errors="coerce"
    )

    users_clean = users_clean.drop_duplicates()
    posts_clean = posts_clean.drop_duplicates()
    interactions_clean = interactions_clean.drop_duplicates()
    topics_clean = topics_clean.drop_duplicates()

    human_users = users_clean[users_clean["account_type"] != "bot"]

    posts_human = posts_clean[
        posts_clean["user_id"].isin(human_users["user_id"])
    ]
    posts_human = posts_human[
        posts_human["topic_id"].isin(topics_clean["topic_id"])
    ]

    interactions_human = interactions_clean[
        interactions_clean["user_id"].isin(human_users["user_id"])
        & interactions_clean["post_id"].isin(posts_human["post_id"])
    ]

    write_audit(
        "Cleaned datasets: missing values handled, timestamps parsed, "
        "duplicates removed."
    )
    write_audit("Renamed text_preview to content_preview.")
    write_audit("Excluded bot accounts from human behaviour analysis.")
    write_audit(
        "Removed invalid post, user and topic references from analysis data."
    )

    return users_clean, posts_human, interactions_human, topics_clean


def transform_data(cleaned_data=None):
    """Merge cleaned datasets into analysis-ready structures."""
    if cleaned_data is None:
        cleaned_data = clean_data()

    users_clean, posts_clean, interactions_clean, topics_clean = cleaned_data

    posts_topics = posts_clean.merge(
        topics_clean, on="topic_id", how="left"
    )
    full_data = interactions_clean.merge(
        posts_topics, on="post_id", how="left"
    )

    write_audit(
        "Merged POSTS, INTERACTIONS and TOPICS into full analysis dataset."
    )

    return (
        users_clean,
        posts_clean,
        interactions_clean,
        topics_clean,
        posts_topics,
        full_data,
    )


def prepare_data(force_reload: bool = False):
    """
    Load, clean and transform the source datasets once.

    Reuses prepared data within the same application session to avoid
    repeatedly reloading and reprocessing the same CSV files.
    """
    global _DATA_CACHE

    if _DATA_CACHE is not None and not force_reload:
        return _DATA_CACHE

    raw_data, load_seconds = timed_stage("Data loading", load_data)
    cleaned_data, clean_seconds = timed_stage(
        "Data cleaning", clean_data, raw_data
    )
    transformed_data, transform_seconds = timed_stage(
        "Data transformation", transform_data, cleaned_data
    )

    _DATA_CACHE = {
        "data": transformed_data,
        "timings": {
            "load_seconds": load_seconds,
            "clean_seconds": clean_seconds,
            "transform_seconds": transform_seconds,
        },
    }
    return _DATA_CACHE


def save_json_backup(prepared=None):
    """Save prepared social-media records as nested JSON."""
    if prepared is None:
        prepared = prepare_data()

    (
        _,
        _,
        interactions_clean,
        _,
        posts_topics,
        _,
    ) = prepared["data"]

    nested_posts = []

    for _, post in posts_topics.iterrows():
        post_interactions = interactions_clean[
            interactions_clean["post_id"] == post["post_id"]
        ][
            [
                "interaction_id",
                "user_id",
                "interaction_type",
                "timestamp",
                "reaction_type",
            ]
        ]

        record = {
            "post_id": post["post_id"],
            "user_id": post["user_id"],
            "timestamp": str(post["timestamp"]),
            "content_type": post["content_type"],
            "content_preview": post["content_preview"],
            "has_media": bool(post["has_media"]),
            "language": post["language"],
            "topic": {
                "topic_id": post["topic_id"],
                "topic_name": post.get("topic_name", ""),
                "category": post.get("category", ""),
                "moderation_level": post.get("moderation_level", ""),
                "description": post.get("description", ""),
            },
            "interactions": post_interactions.astype(str).to_dict(
                orient="records"
            ),
        }
        nested_posts.append(record)

    with open(JSON_BACKUP, "w", encoding="utf-8") as file:
        json.dump(nested_posts, file, indent=4, ensure_ascii=False)

    write_audit("Saved translated JSON backup to moderation_backup.json.")
    return nested_posts


def load_json_backup():
    """Restore a previously generated JSON backup."""
    with open(JSON_BACKUP, "r", encoding="utf-8") as file:
        data = json.load(file)

    write_audit("Loaded JSON backup from moderation_backup.json.")
    return data


def run_report_analysis(prepared=None):
    """Analyse report counts by category and moderation level."""
    if prepared is None:
        prepared = prepare_data()

    full_data = prepared["data"][-1]
    reports = full_data[full_data["interaction_type"] == "report"]

    result = (
        reports.groupby(["category", "moderation_level"])
        .size()
        .reset_index(name="report_count")
    )

    write_audit("Generated report analysis by category and moderation level.")
    return result


def run_posting_pivot(prepared=None):
    """Create posting-activity pivot data and heatmap."""
    if prepared is None:
        prepared = prepare_data()

    posts_topics = prepared["data"][-2].copy()
    posts_topics["hour"] = posts_topics["timestamp"].dt.hour

    pivot_table = posts_topics.pivot_table(
        index="hour",
        columns="topic_id",
        values="post_id",
        aggfunc="count",
        fill_value=0,
    )

    plt.figure(figsize=(10, 6))
    sns.heatmap(pivot_table, cmap="Blues")
    plt.title("Posting Activity by Hour and Topic")
    plt.xlabel("Topic ID")
    plt.ylabel("Hour of Day")
    plt.tight_layout()
    plt.savefig(OUTPUT_PATH / "posting_pivot.png", dpi=200)
    plt.close()

    write_audit(
        "Generated posting activity pivot table and saved posting_pivot.png."
    )
    return pivot_table


def run_statistics(metric="like", prepared=None):
    """Calculate mean, median and mode for a selected engagement metric."""
    if prepared is None:
        prepared = prepare_data()

    full_data = prepared["data"][-1]

    engagement_table = (
        full_data.groupby(["post_id", "interaction_type"])
        .size()
        .unstack(fill_value=0)
    )

    if metric not in engagement_table.columns:
        write_audit(f"Metric {metric} not found. Returning zero statistics.")
        return 0.0, 0.0, 0

    values = engagement_table[metric]
    mean_value = float(round(values.mean(), 2))
    median_value = float(round(values.median(), 2))
    mode_value = int(values.mode().iloc[0])

    write_audit(f"Calculated statistics for metric: {metric}.")
    return mean_value, median_value, mode_value


def run_correlation_visualisation(prepared=None):
    """Analyse report rate against moderation level and save visual outputs."""
    if prepared is None:
        prepared = prepare_data()

    full_data = prepared["data"][-1].copy()
    moderation_map = {"low": 1, "medium": 2, "high": 3}

    full_data["is_report"] = (
        full_data["interaction_type"] == "report"
    ).astype(int)
    full_data["moderation_score"] = full_data["moderation_level"].map(
        moderation_map
    )

    correlation_data = (
        full_data.groupby(
            ["topic_id", "moderation_level", "moderation_score"]
        )
        .agg(
            total_interactions=("interaction_type", "count"),
            report_count=("is_report", "sum"),
        )
        .reset_index()
    )

    correlation_data["report_rate"] = (
        correlation_data["report_count"]
        / correlation_data["total_interactions"]
    )

    correlation_value = correlation_data["moderation_score"].corr(
        correlation_data["report_rate"]
    )

    heatmap_data = correlation_data.pivot(
        index="topic_id",
        columns="moderation_level",
        values="report_count",
    )

    plt.figure(figsize=(8, 6))
    sns.heatmap(heatmap_data, annot=True, fmt=".0f", cmap="Reds")
    plt.title("Report Counts by Topic and Moderation Level")
    plt.xlabel("Moderation Level")
    plt.ylabel("Topic ID")
    plt.tight_layout()
    plt.savefig(OUTPUT_PATH / "report_heatmap.png", dpi=200)
    plt.close()

    plt.figure(figsize=(8, 6))
    sns.barplot(
        data=correlation_data,
        x="moderation_level",
        y="report_rate",
        order=["low", "medium", "high"],
    )
    plt.title(
        "Report Rate by Moderation Level "
        f"(Correlation: {correlation_value:.2f})"
    )
    plt.xlabel("Moderation Level")
    plt.ylabel("Report Rate")
    plt.tight_layout()
    plt.savefig(OUTPUT_PATH / "report_correlation.png", dpi=200)
    plt.close()

    write_audit(
        "Generated report correlation and topic heatmap visualisations."
    )
    return correlation_data, correlation_value


def run_categorical_analysis(prepared=None):
    """Analyse media presence × category × moderation level."""
    if prepared is None:
        prepared = prepare_data()

    posts_topics = prepared["data"][-2]

    result = (
        posts_topics.groupby(
            ["has_media", "category", "moderation_level"]
        )
        .size()
        .reset_index(name="post_count")
    )

    chart = sns.catplot(
        data=result,
        x="category",
        y="post_count",
        hue="moderation_level",
        col="has_media",
        kind="bar",
        height=5,
        aspect=1,
    )

    chart.fig.suptitle(
        "Post Count by Media Presence, Category and Moderation Level"
    )
    chart.fig.subplots_adjust(top=0.85)
    chart.savefig(OUTPUT_PATH / "categorical_analysis.png", dpi=200)
    plt.close()

    write_audit(
        "Generated categorical analysis and saved categorical_analysis.png."
    )
    return result


def run_visualisation(prepared=None):
    """Generate all portfolio visualisations from one prepared dataset."""
    if prepared is None:
        prepared = prepare_data()

    run_posting_pivot(prepared)
    correlation_data, correlation_value = (
        run_correlation_visualisation(prepared)
    )
    run_categorical_analysis(prepared)

    write_audit("Generated all visualisation outputs.")
    return correlation_data, correlation_value


def run_full_analysis(metric="like", force_reload: bool = False):
    """Run the complete moderation analytics workflow."""
    overall_start = perf_counter()

    prepared = prepare_data(force_reload=force_reload)

    _, json_seconds = timed_stage(
        "JSON backup", save_json_backup, prepared
    )
    report_analysis = run_report_analysis(prepared)
    pivot_table = run_posting_pivot(prepared)
    mean_value, median_value, mode_value = run_statistics(
        metric, prepared
    )
    correlation_data, correlation_value = (
        run_correlation_visualisation(prepared)
    )
    categorical_analysis = run_categorical_analysis(prepared)

    total_seconds = perf_counter() - overall_start

    timings = dict(prepared["timings"])
    timings["json_seconds"] = json_seconds
    timings["total_seconds"] = total_seconds

    write_audit(
        f"Completed full moderation analytics pipeline in "
        f"{total_seconds:.4f} seconds."
    )

    return {
        "report_analysis": report_analysis,
        "pivot_table": pivot_table,
        "statistics": {
            "metric": metric,
            "mean": mean_value,
            "median": median_value,
            "mode": mode_value,
        },
        "correlation": correlation_value,
        "categorical_analysis": categorical_analysis,
        "timings": timings,
    }


if __name__ == "__main__":
    results = run_full_analysis("like", force_reload=True)
    print("Full analysis completed.")
    print("Statistics:", results["statistics"])
    print("Stage timings:", results["timings"])
