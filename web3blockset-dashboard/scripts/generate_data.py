"""
Generate pre-computed JSON summary files and lightweight CSV for the Web3BlockSet Dashboard.

Usage:
    python scripts/generate_data.py \
        --issues-csv /path/to/web3blockset/issues_prs.csv \
        --repos-csv /path/to/web3blockset/repositories.csv \
        --output ./public/data
"""

import argparse
import json
import os
from datetime import datetime

import pandas as pd
import numpy as np


def load_issues_csv(path: str) -> pd.DataFrame:
    print(f"Loading issues CSV from {path}...")
    df = pd.read_csv(
        path,
        dtype={
            "repository": str,
            "owner": str,
            "issue_id": "Int64",
            "issue_number": "Int64",
            "issue_title": str,
            "state": str,
            "author": str,
            "author_id": "Int64",
            "locked": str,
            "comments_count": "Int64",
            "commits_count": "Int64",
            "labels": str,
            "type": str,
            "comments_count_filtered": "Int64",
            "repository_category": str,
            "year": "Int64",
            "data_source": str,
            "owner_used": str,
            "matching_keywords": str,
            "matching_mandatory_keywords": str,
        },
        parse_dates=["created_at", "updated_at", "closed_at"],
        low_memory=False,
    )
    print(f"  Loaded {len(df):,} records")
    return df


def load_repos_csv(path: str) -> pd.DataFrame:
    print(f"Loading repositories CSV from {path}...")
    df = pd.read_csv(path)
    print(f"  Loaded {len(df):,} records")
    return df


def generate_overview(df: pd.DataFrame, repos_df: pd.DataFrame) -> dict:
    print("Generating overview.json...")
    closed = df[df["state"] == "closed"]
    closed_with_dates = closed.dropna(subset=["created_at", "closed_at"])
    resolution_days = (
        closed_with_dates["closed_at"] - closed_with_dates["created_at"]
    ).dt.total_seconds() / 86400
    resolution_days = resolution_days[resolution_days >= 0]

    issues_closed = closed_with_dates[closed_with_dates["type"] == "Issue"]
    prs_closed = closed_with_dates[closed_with_dates["type"] == "Pull Request"]
    iss_res = (issues_closed["closed_at"] - issues_closed["created_at"]).dt.total_seconds() / 86400
    pr_res = (prs_closed["closed_at"] - prs_closed["created_at"]).dt.total_seconds() / 86400
    iss_res = iss_res[iss_res >= 0]
    pr_res = pr_res[pr_res >= 0]

    provider = df[df["data_source"] == "provider"]
    community = df[df["data_source"] == "community"]

    return {
        "totalRecords": int(len(df)),
        "totalIssues": int((df["type"] == "Issue").sum()),
        "totalPRs": int((df["type"] == "Pull Request").sum()),
        "totalProviderRepos": int(len(repos_df)),
        "totalOrganizations": int(repos_df["organization"].nunique()) if "organization" in repos_df.columns else 80,
        "totalUniqueAuthors": int(df["author"].nunique()),
        "totalProviderRecords": int(len(provider)),
        "totalCommunityRecords": int(len(community)),
        "totalCommunityRepos": int(community[["repository", "owner"]].drop_duplicates().shape[0]) if len(community) > 0 else 0,
        "totalUniqueRepos": int(df[["repository", "owner"]].drop_duplicates().shape[0]),
        "openRecords": int((df["state"] == "open").sum()),
        "closedRecords": int((df["state"] == "closed").sum()),
        "yearRange": [int(df["year"].min()), int(df["year"].max())],
        "medianResolutionDays": round(float(resolution_days.median()), 2) if len(resolution_days) > 0 else None,
        "medianIssueResolutionDays": round(float(iss_res.median()), 2) if len(iss_res) > 0 else None,
        "medianPRResolutionDays": round(float(pr_res.median()), 2) if len(pr_res) > 0 else None,
        "lastUpdated": datetime.now().strftime("%Y-%m-%d"),
    }


def generate_yearly_trends(df: pd.DataFrame) -> list:
    print("Generating yearly_trends.json...")
    rows = []
    for year, grp in df.groupby("year"):
        if pd.isna(year):
            continue
        provider = grp[grp["data_source"] == "provider"]
        community = grp[grp["data_source"] == "community"]
        rows.append({
            "year": int(year),
            "issues": int((grp["type"] == "Issue").sum()),
            "prs": int((grp["type"] == "Pull Request").sum()),
            "total": int(len(grp)),
            "providerIssues": int((provider["type"] == "Issue").sum()),
            "providerPRs": int((provider["type"] == "Pull Request").sum()),
            "communityIssues": int((community["type"] == "Issue").sum()),
            "communityPRs": int((community["type"] == "Pull Request").sum()),
        })
    return sorted(rows, key=lambda x: x["year"])


def generate_category_distribution(df: pd.DataFrame) -> list:
    print("Generating category_distribution.json...")
    rows = []
    for cat, grp in df.groupby("repository_category"):
        if pd.isna(cat):
            continue
        rows.append({
            "category": str(cat),
            "count": int(len(grp)),
            "issues": int((grp["type"] == "Issue").sum()),
            "prs": int((grp["type"] == "Pull Request").sum()),
            "repos": int(grp[["repository", "owner"]].drop_duplicates().shape[0]),
            "percentage": round(len(grp) / len(df) * 100, 1),
        })
    return sorted(rows, key=lambda x: x["count"], reverse=True)


def generate_top_owners(df: pd.DataFrame, top_n: int = 30) -> list:
    print("Generating top_owners.json...")
    rows = []
    for owner, grp in df.groupby("owner"):
        if pd.isna(owner):
            continue
        cats = grp["repository_category"].dropna().unique().tolist()
        rows.append({
            "owner": str(owner),
            "count": int(len(grp)),
            "issues": int((grp["type"] == "Issue").sum()),
            "prs": int((grp["type"] == "Pull Request").sum()),
            "repos": int(grp["repository"].nunique()),
            "categories": cats[:3],
        })
    rows.sort(key=lambda x: x["count"], reverse=True)
    return rows[:top_n]


def generate_top_repositories(df: pd.DataFrame, repos_df: pd.DataFrame, top_n: int = 30) -> list:
    print("Generating top_repositories.json...")
    stars_map = {}
    if "stars" in repos_df.columns:
        for _, row in repos_df.iterrows():
            key = str(row.get("html_url", "")).split("/")[-1] if "html_url" in repos_df.columns else ""
            if key:
                stars_map[key] = int(row.get("stars", 0)) if pd.notna(row.get("stars")) else 0

    rows = []
    for (repo, owner), grp in df.groupby(["repository", "owner"]):
        if pd.isna(repo):
            continue
        cat = grp["repository_category"].dropna().iloc[0] if len(grp["repository_category"].dropna()) > 0 else ""
        rows.append({
            "repository": str(repo),
            "owner": str(owner),
            "count": int(len(grp)),
            "issues": int((grp["type"] == "Issue").sum()),
            "prs": int((grp["type"] == "Pull Request").sum()),
            "category": str(cat),
            "stars": stars_map.get(str(repo), 0),
        })
    rows.sort(key=lambda x: x["count"], reverse=True)
    return rows[:top_n]


def generate_language_distribution(repos_df: pd.DataFrame) -> list:
    print("Generating language_distribution.json...")
    lang_counts = repos_df["language"].dropna().value_counts()
    total = lang_counts.sum()
    rows = []
    for lang, count in lang_counts.items():
        rows.append({
            "language": str(lang),
            "repos": int(count),
            "percentage": round(count / total * 100, 1),
        })
    return rows


def generate_state_distribution(df: pd.DataFrame) -> dict:
    print("Generating state_distribution.json...")
    by_type = []
    for t in ["Issue", "Pull Request"]:
        sub = df[df["type"] == t]
        by_type.append({
            "type": t,
            "open": int((sub["state"] == "open").sum()),
            "closed": int((sub["state"] == "closed").sum()),
        })

    by_source = []
    for s in ["provider", "community"]:
        sub = df[df["data_source"] == s]
        by_source.append({
            "source": s,
            "open": int((sub["state"] == "open").sum()),
            "closed": int((sub["state"] == "closed").sum()),
        })

    return {"byType": by_type, "byDataSource": by_source}


def generate_resolution_by_category(df: pd.DataFrame) -> list:
    print("Generating resolution_by_category.json...")
    closed = df[(df["state"] == "closed") & df["created_at"].notna() & df["closed_at"].notna()].copy()
    closed["resolution_days"] = (closed["closed_at"] - closed["created_at"]).dt.total_seconds() / 86400
    closed = closed[closed["resolution_days"] >= 0]

    rows = []
    for cat, grp in closed.groupby("repository_category"):
        if pd.isna(cat):
            continue
        iss = grp[grp["type"] == "Issue"]["resolution_days"]
        prs = grp[grp["type"] == "Pull Request"]["resolution_days"]
        rows.append({
            "category": str(cat),
            "medianDays": round(float(grp["resolution_days"].median()), 2),
            "closedCount": int(len(grp)),
            "issueMedian": round(float(iss.median()), 2) if len(iss) > 0 else None,
            "prMedian": round(float(prs.median()), 2) if len(prs) > 0 else None,
        })
    rows.sort(key=lambda x: x["closedCount"], reverse=True)
    return rows


def generate_top_labels(df: pd.DataFrame, top_n: int = 50) -> list:
    print("Generating top_labels.json...")
    label_counts: dict[str, int] = {}
    for labels_str in df["labels"].dropna():
        for label in str(labels_str).split(","):
            label = label.strip()
            if label:
                label_counts[label] = label_counts.get(label, 0) + 1

    sorted_labels = sorted(label_counts.items(), key=lambda x: x[1], reverse=True)
    return [{"label": l, "count": c} for l, c in sorted_labels[:top_n]]


def generate_monthly_activity(df: pd.DataFrame) -> list:
    print("Generating monthly_activity.json...")
    df_valid = df[df["created_at"].notna()].copy()
    df_valid["month"] = df_valid["created_at"].dt.to_period("M")

    rows = []
    for month, grp in df_valid.groupby("month"):
        rows.append({
            "month": str(month),
            "created": int(len(grp)),
            "issues": int((grp["type"] == "Issue").sum()),
            "prs": int((grp["type"] == "Pull Request").sum()),
        })
    return sorted(rows, key=lambda x: x["month"])


def generate_repositories_meta(repos_df: pd.DataFrame) -> list:
    print("Generating repositories_meta.json...")
    rows = []
    for _, row in repos_df.iterrows():
        rows.append({
            "organization": str(row.get("organization", "")) if pd.notna(row.get("organization")) else "",
            "description": str(row.get("description", ""))[:200] if pd.notna(row.get("description")) else "",
            "stars": int(row.get("stars", 0)) if pd.notna(row.get("stars")) else 0,
            "forks": int(row.get("forks", 0)) if pd.notna(row.get("forks")) else 0,
            "language": str(row.get("language", "")) if pd.notna(row.get("language")) else "",
            "archived": bool(row.get("archived", False)) if pd.notna(row.get("archived")) else False,
            "category": str(row.get("repository_category", "")) if pd.notna(row.get("repository_category")) else "",
            "htmlUrl": str(row.get("html_url", "")) if pd.notna(row.get("html_url")) else "",
        })
    return rows


def generate_filter_options(df: pd.DataFrame) -> dict:
    print("Generating filter_options.json...")
    owners = sorted(df["owner"].dropna().unique().tolist())
    repos = []
    for (repo, owner), _ in df.groupby(["repository", "owner"]):
        if pd.notna(repo) and pd.notna(owner):
            repos.append({"name": str(repo), "owner": str(owner)})
    repos.sort(key=lambda x: x["owner"] + "/" + x["name"])

    categories = sorted(df["repository_category"].dropna().unique().tolist())
    years = sorted([int(y) for y in df["year"].dropna().unique()])

    return {
        "owners": owners,
        "repositories": repos,
        "categories": categories,
        "years": years,
        "dataSources": ["provider", "community"],
        "types": ["Issue", "Pull Request"],
        "states": ["open", "closed"],
    }


def generate_light_csv(df: pd.DataFrame, output_path: str):
    print("Generating issues_prs_light.csv...")
    columns = [
        "repository", "owner", "issue_number", "issue_title",
        "state", "created_at", "closed_at", "type",
        "comments_count", "labels", "repository_category",
        "year", "data_source",
    ]
    light = df[columns].copy()
    light["issue_title"] = light["issue_title"].fillna("").str[:150]
    light["created_at"] = light["created_at"].dt.strftime("%Y-%m-%d").fillna("")
    light["closed_at"] = light["closed_at"].dt.strftime("%Y-%m-%d").fillna("")
    light.to_csv(output_path, index=False)
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  Written {output_path} ({size_mb:.1f} MB)")


def save_json(data, output_dir: str, filename: str):
    path = os.path.join(output_dir, filename)
    with open(path, "w") as f:
        json.dump(data, f, separators=(",", ":"), default=str)
    size_kb = os.path.getsize(path) / 1024
    print(f"  Written {filename} ({size_kb:.1f} KB)")


def main():
    parser = argparse.ArgumentParser(description="Generate Web3BlockSet dashboard data")
    parser.add_argument("--issues-csv", required=True, help="Path to issues_prs.csv")
    parser.add_argument("--repos-csv", required=True, help="Path to repositories.csv")
    parser.add_argument("--output", required=True, help="Output directory for JSON files")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    df = load_issues_csv(args.issues_csv)
    repos_df = load_repos_csv(args.repos_csv)

    save_json(generate_overview(df, repos_df), args.output, "overview.json")
    save_json(generate_yearly_trends(df), args.output, "yearly_trends.json")
    save_json(generate_category_distribution(df), args.output, "category_distribution.json")
    save_json(generate_top_owners(df), args.output, "top_owners.json")
    save_json(generate_top_repositories(df, repos_df), args.output, "top_repositories.json")
    save_json(generate_language_distribution(repos_df), args.output, "language_distribution.json")
    save_json(generate_state_distribution(df), args.output, "state_distribution.json")
    save_json(generate_resolution_by_category(df), args.output, "resolution_by_category.json")
    save_json(generate_top_labels(df), args.output, "top_labels.json")
    save_json(generate_monthly_activity(df), args.output, "monthly_activity.json")
    save_json(generate_repositories_meta(repos_df), args.output, "repositories_meta.json")
    save_json(generate_filter_options(df), args.output, "filter_options.json")
    generate_light_csv(df, os.path.join(args.output, "issues_prs_light.csv"))

    print("\nDone! All files generated.")


if __name__ == "__main__":
    main()
