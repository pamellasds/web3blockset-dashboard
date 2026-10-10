#!/usr/bin/env python3
"""MSR 2027 short WIP — RQ3a: core maintainers vs occasional contributors.

Provider-only Web3BlockSet. Single entrypoint: python analyze.py
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parent
# CSVs live in ../web3blockset (sibling of 2027_msr)
W3_DATA = ROOT.parent.parent / "web3blockset"
RAW_ISSUES = W3_DATA / "issues_prs.csv"
RAW_REPOS = W3_DATA / "repositories.csv"

PROCESSED = ROOT / "data" / "processed"
MANUAL = ROOT / "data" / "manual_review"
TABLES = ROOT / "results" / "tables"
FIGURES = ROOT / "results" / "figures"
PAPER_FIG = ROOT / "paper" / "figures"

YEAR_MIN, YEAR_MAX = 2018, 2025
# Core = top CORE_PCT of authors by Issues/PRs opened in the repo (non-tautological share)
CORE_PCT = 0.10
MIN_REPO_DOCS = 30
SAMPLE_PER_STRATUM = 8
SAMPLE_SEED = 20270303

COLORS = ["#0F766E", "#B45309", "#1D4ED8", "#BE123C", "#047857", "#C2410C", "#0E7490", "#334155"]
LAYOUT = dict(
    font=dict(family="IBM Plex Sans, Segoe UI, sans-serif", size=13, color="#0F172A"),
    paper_bgcolor="#F8FAFC",
    plot_bgcolor="#F8FAFC",
    margin=dict(l=60, r=30, t=60, b=50),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None),
    width=920,
    height=520,
)

csv.field_size_limit(10**9)


def _year(v: str) -> int | None:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def _split_authors(cell: str) -> list[str]:
    if not cell or not str(cell).strip():
        return []
    # dataset uses ';' (sometimes ',')
    parts = str(cell).replace(",", ";").split(";")
    return [p.strip() for p in parts if p.strip()]


def _hhi(counts: pd.Series) -> float:
    if counts.empty or counts.sum() == 0:
        return float("nan")
    p = counts / counts.sum()
    return float((p**2).sum())


def _gini(values: np.ndarray) -> float:
    """Gini coefficient for non-negative contribution counts."""
    v = np.sort(values.astype(float))
    if v.size == 0 or v.sum() == 0:
        return float("nan")
    n = v.size
    idx = np.arange(1, n + 1)
    return float((2 * np.sum(idx * v) - (n + 1) * np.sum(v)) / (n * np.sum(v)))


# ---------------------------------------------------------------------------
# 1) Prepare
# ---------------------------------------------------------------------------
def prepare() -> pd.DataFrame:
    repo_cat: dict[str, str] = {}
    with RAW_REPOS.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            org = (row.get("organization") or "").strip().lower()
            url = (row.get("html_url") or "").rstrip("/").lower()
            name = url.split("/")[-1] if url else ""
            cat = (row.get("repository_category") or "").strip()
            if org and name and cat:
                repo_cat[f"{org}/{name}"] = cat

    rows = []
    with RAW_ISSUES.open(newline="", encoding="utf-8", errors="replace") as fh:
        for i, row in enumerate(csv.DictReader(fh), 1):
            if (row.get("data_source") or "").strip().lower() != "provider":
                continue
            year = _year(row.get("year") or "")
            if year is None or year < YEAR_MIN or year > YEAR_MAX:
                continue
            owner = (row.get("owner") or row.get("organization") or "").strip()
            repo = (row.get("repository") or "").strip()
            key = f"{owner}/{repo}"
            cat = (row.get("repository_category") or "").strip() or repo_cat.get(key.lower(), "")
            if not cat:
                continue
            author = (row.get("author") or "").strip()
            if not author or author.lower() in {"", "none", "nan", "null"}:
                continue
            try:
                n_comments = float(row.get("comments_count_filtered") or row.get("comments_count") or 0)
            except ValueError:
                n_comments = 0.0
            rows.append(
                {
                    "issue_id": row.get("issue_id"),
                    "year": year,
                    "owner": owner,
                    "repository": repo,
                    "repo_key": key,
                    "type": (row.get("type") or "").strip(),
                    "state": (row.get("state") or "").strip().lower(),
                    "author": author,
                    "author_id": (row.get("author_id") or "").strip(),
                    "comment_authors": row.get("comment_authors") or "",
                    "n_comments": n_comments,
                    "issue_title": (row.get("issue_title") or "")[:240],
                    "repository_category": cat,
                }
            )
            if i % 300_000 == 0:
                print(f"... scanned {i:,}", flush=True)

    df = pd.DataFrame(rows)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_parquet(PROCESSED / "provider_collab.parquet", index=False)
    print(f"docs={len(df):,} repos={df['repo_key'].nunique()} authors={df['author'].nunique()}")
    return df


# ---------------------------------------------------------------------------
# 2) Role labeling + metrics
# ---------------------------------------------------------------------------
def label_roles(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per repo: core = top CORE_PCT authors by number of opened Issues/PRs."""
    role_rows = []
    repo_stats = []

    for repo_key, g in df.groupby("repo_key"):
        if len(g) < MIN_REPO_DOCS:
            continue
        counts = g["author"].value_counts()
        total = int(counts.sum())
        n_authors = int(counts.size)
        n_core = max(1, int(np.ceil(CORE_PCT * n_authors)))
        core = set(counts.head(n_core).index)
        share_core_docs = float(counts.head(n_core).sum() / total)
        hhi = _hhi(counts)
        gini = _gini(counts.to_numpy())
        cat = g["repository_category"].iloc[0]

        repo_stats.append(
            {
                "repo_key": repo_key,
                "repository_category": cat,
                "n_docs": total,
                "n_authors": n_authors,
                "n_core": n_core,
                "core_author_share": n_core / n_authors,
                "core_doc_share": share_core_docs,
                "hhi_authors": hhi,
                "gini_authors": gini,
            }
        )
        for author, c in counts.items():
            role_rows.append(
                {
                    "repo_key": repo_key,
                    "repository_category": cat,
                    "author": author,
                    "n_docs_opened": int(c),
                    "role": "core" if author in core else "occasional",
                }
            )

    roles = pd.DataFrame(role_rows)
    repos = pd.DataFrame(repo_stats)
    return roles, repos


def analyze(df: pd.DataFrame) -> dict:
    TABLES.mkdir(parents=True, exist_ok=True)
    roles, repos = label_roles(df)
    roles.to_csv(TABLES / "author_roles_by_repo.csv", index=False)
    repos.to_csv(TABLES / "repo_concentration.csv", index=False)

    # attach opener role (merge is much faster than row-wise apply)
    d = df[df["repo_key"].isin(set(repos["repo_key"]))].copy()
    d = d.merge(
        roles[["repo_key", "author", "role"]].rename(columns={"role": "opener_role"}),
        on=["repo_key", "author"],
        how="left",
    )
    d["opener_role"] = d["opener_role"].fillna("unknown")

    core_by_repo = (
        roles[roles["role"] == "core"]
        .groupby("repo_key")["author"]
        .apply(set)
        .to_dict()
    )

    core_flags = []
    n_commenters = []
    for repo_key, authors_cell, opener in zip(
        d["repo_key"].to_numpy(), d["comment_authors"].to_numpy(), d["author"].to_numpy()
    ):
        participants = set(_split_authors(authors_cell))
        n_commenters.append(len(participants))
        participants.add(opener)
        cores = core_by_repo.get(repo_key, set())
        core_flags.append(bool(participants & cores) if cores else False)
    d["core_in_thread"] = core_flags
    d["n_unique_commenters"] = n_commenters
    d.to_parquet(PROCESSED / "provider_collab_labeled.parquet", index=False)

    # --- global summary ---
    opener_share = d["opener_role"].value_counts(normalize=True).to_dict()
    # response: occasional-opened threads that include a core commenter
    occ = d[d["opener_role"] == "occasional"]
    core_reply_rate = float(occ["core_in_thread"].mean()) if len(occ) else float("nan")

    by_cat = (
        repos.groupby("repository_category", as_index=False)
        .agg(
            n_repos=("repo_key", "count"),
            median_gini=("gini_authors", "median"),
            median_hhi=("hhi_authors", "median"),
            median_core_author_share=("core_author_share", "median"),
            median_core_doc_share=("core_doc_share", "median"),
            median_authors=("n_authors", "median"),
        )
        .sort_values("median_gini", ascending=False)
    )
    by_cat.to_csv(TABLES / "concentration_by_category.csv", index=False)

    # yearly concentration (median gini across repos with activity that year)
    yearly = []
    for year, g in d.groupby("year"):
        # recompute opener concentration that year per repo
        ginisf = []
        for _, rg in g.groupby("repo_key"):
            if len(rg) < 10:
                continue
            ginisf.append(_gini(rg["author"].value_counts().to_numpy()))
        yearly.append(
            {
                "year": int(year),
                "n_docs": int(len(g)),
                "share_opened_by_core": float((g["opener_role"] == "core").mean()),
                "core_reply_rate_to_occasional": float(
                    g.loc[g["opener_role"] == "occasional", "core_in_thread"].mean()
                )
                if (g["opener_role"] == "occasional").any()
                else float("nan"),
                "median_repo_gini": float(np.nanmedian(ginisf)) if ginisf else float("nan"),
                "mean_unique_commenters": float(g["n_unique_commenters"].mean()),
            }
        )
    yearly_df = pd.DataFrame(yearly).sort_values("year")
    yearly_df.to_csv(TABLES / "yearly_collab_metrics.csv", index=False)

    # thread mix
    mix = (
        d.groupby(["opener_role", "core_in_thread"], as_index=False)
        .size()
        .rename(columns={"size": "n"})
    )
    mix.to_csv(TABLES / "thread_role_mix.csv", index=False)

    # top concentrated repos
    repos.sort_values("gini_authors", ascending=False).head(25).to_csv(
        TABLES / "top_concentrated_repos.csv", index=False
    )

    summary = {
        "year_min": YEAR_MIN,
        "year_max": YEAR_MAX,
        "core_pct": CORE_PCT,
        "min_repo_docs": MIN_REPO_DOCS,
        "n_docs": int(len(d)),
        "n_repos": int(repos.shape[0]),
        "n_authors": int(roles["author"].nunique()),
        "share_docs_opened_by_core": float(opener_share.get("core", 0)),
        "share_docs_opened_by_occasional": float(opener_share.get("occasional", 0)),
        "core_reply_rate_to_occasional": core_reply_rate,
        "median_gini": float(repos["gini_authors"].median()),
        "median_hhi": float(repos["hhi_authors"].median()),
        "median_core_author_share": float(repos["core_author_share"].median()),
        "median_n_core": float(repos["n_core"].median()),
        "median_n_authors": float(repos["n_authors"].median()),
    }
    (TABLES / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return summary


# ---------------------------------------------------------------------------
# 3) Plots
# ---------------------------------------------------------------------------
def _save(fig: go.Figure, name: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    PAPER_FIG.mkdir(parents=True, exist_ok=True)
    fig.update_layout(**LAYOUT)
    for folder in (FIGURES, PAPER_FIG):
        fig.write_html(folder / f"{name}.html", include_plotlyjs="cdn")
        fig.write_image(folder / f"{name}.png", scale=2)
        fig.write_image(folder / f"{name}.pdf")
    print("saved", name)


def make_plots() -> None:
    repos = pd.read_csv(TABLES / "repo_concentration.csv")
    yearly = pd.read_csv(TABLES / "yearly_collab_metrics.csv")
    by_cat = pd.read_csv(TABLES / "concentration_by_category.csv")
    summary = json.loads((TABLES / "summary.json").read_text(encoding="utf-8"))

    # Fig1: distribution of Gini / core author share
    fig1 = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Gini de autoria (por repo)", "% autores que são core (por repo)"),
    )
    fig1.add_trace(
        go.Histogram(x=repos["gini_authors"], nbinsx=30, marker_color=COLORS[0], name="Gini"),
        row=1, col=1,
    )
    fig1.add_trace(
        go.Histogram(x=repos["core_author_share"], nbinsx=30, marker_color=COLORS[1], name="core share"),
        row=1, col=2,
    )
    fig1.update_layout(
        title=f"Concentração de colaboração (core = top {int(100*summary['core_pct'])}% autores)",
        showlegend=False,
    )
    fig1.update_xaxes(title="Gini", row=1, col=1, gridcolor="#E2E8F0")
    fig1.update_xaxes(title="Share de autores core", row=1, col=2, gridcolor="#E2E8F0")
    fig1.update_yaxes(title="Nº repositórios", gridcolor="#E2E8F0")
    _save(fig1, "fig1_concentration_dist")

    # Fig2: yearly — share opened by core + reply rate
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    fig2.add_trace(
        go.Scatter(
            x=yearly["year"], y=yearly["share_opened_by_core"],
            mode="lines+markers", name="Docs abertos por core",
            line=dict(color=COLORS[0], width=3), marker=dict(size=8),
        ),
        secondary_y=False,
    )
    fig2.add_trace(
        go.Scatter(
            x=yearly["year"], y=yearly["core_reply_rate_to_occasional"],
            mode="lines+markers", name="Core responde occasional",
            line=dict(color=COLORS[1], width=3, dash="dot"),
            marker=dict(size=8, symbol="diamond"),
        ),
        secondary_y=True,
    )
    fig2.update_layout(title="Dinâmica ano a ano: quem abre e quem responde")
    fig2.update_xaxes(title="Ano", dtick=1, gridcolor="#E2E8F0")
    fig2.update_yaxes(title="Share aberto por core", range=[0, 1], secondary_y=False, gridcolor="#E2E8F0")
    fig2.update_yaxes(title="Taxa de resposta core→occasional", range=[0, 1], secondary_y=True)
    _save(fig2, "fig2_yearly_roles")

    # Fig3: Gini by category (top categories by n_repos)
    cat = by_cat[by_cat["n_repos"] >= 5].sort_values("median_gini", ascending=True).tail(12)
    fig3 = go.Figure(
        go.Bar(
            x=cat["median_gini"],
            y=cat["repository_category"],
            orientation="h",
            marker_color=COLORS[2],
            text=[f"{v:.2f}" for v in cat["median_gini"]],
            textposition="outside",
        )
    )
    fig3.update_layout(
        title="Concentração mediana (Gini) por categoria validada",
        xaxis_title="Gini mediano",
        yaxis_title="",
    )
    fig3.update_xaxes(gridcolor="#E2E8F0", range=[0, 1])
    _save(fig3, "fig3_gini_by_category")

    # Fig4: scatter authors vs gini
    fig4 = px.scatter(
        repos,
        x="n_authors",
        y="gini_authors",
        color="repository_category",
        hover_name="repo_key",
        title="Mais autores ≠ colaboração mais igualitária",
        opacity=0.75,
    )
    fig4.update_traces(marker=dict(size=8, line=dict(width=0)))
    fig4.update_xaxes(title="Nº de autores no repo", gridcolor="#E2E8F0")
    fig4.update_yaxes(title="Gini de autoria", gridcolor="#E2E8F0")
    fig4.update_layout(showlegend=False)
    _save(fig4, "fig4_authors_vs_gini")


# ---------------------------------------------------------------------------
# 4) Blind sample — validate role heuristic
# ---------------------------------------------------------------------------
def build_blind_sample(df: pd.DataFrame) -> None:
    """Stratified by category: authors labeled core/occasional, blinded for reviewers."""
    MANUAL.mkdir(parents=True, exist_ok=True)
    roles = pd.read_csv(TABLES / "author_roles_by_repo.csv")
    # focus on authors with some activity
    roles = roles[roles["n_docs_opened"] >= 2].copy()
    roles["stratum"] = roles["repository_category"] + " | " + roles["role"]

    rng = np.random.default_rng(SAMPLE_SEED)
    parts = []
    for stratum, g in roles.groupby("stratum"):
        n = min(SAMPLE_PER_STRATUM, len(g))
        if n == 0:
            continue
        idx = rng.choice(g.index.to_numpy(), size=n, replace=False)
        parts.append(g.loc[idx])
    sample = pd.concat(parts, ignore_index=True)
    sample = sample.sample(frac=1.0, random_state=SAMPLE_SEED).reset_index(drop=True)
    sample.insert(0, "review_id", [f"R{i:03d}" for i in range(1, len(sample) + 1)])

    # enrich with example titles from that author-repo
    examples = []
    for _, r in sample.iterrows():
        hits = df[(df["repo_key"] == r["repo_key"]) & (df["author"] == r["author"])]
        titles = " || ".join(hits["issue_title"].head(3).tolist())
        examples.append(titles[:400])
    sample["example_titles"] = examples

    sample[
        [
            "review_id", "stratum", "role", "repository_category", "repo_key",
            "author", "n_docs_opened", "example_titles",
        ]
    ].to_csv(MANUAL / "key_mapping.csv", index=False)

    blind = sample[["review_id", "repo_key", "author", "n_docs_opened", "example_titles"]].copy()
    for col in [
        "inferred_role",  # core_maintainer | regular | occasional | bot_or_automation | unsure
        "evidence",
        "is_org_affiliated",  # yes/no/unsure (from GitHub page if checked)
        "notes",
        "reviewer_id",
    ]:
        blind[col] = ""
    blind.to_csv(MANUAL / "blind_sample.csv", index=False)
    (
        sample.groupby(["repository_category", "role"], as_index=False)
        .size()
        .rename(columns={"size": "n_sampled"})
        .to_csv(MANUAL / "stratum_counts.csv", index=False)
    )
    print(f"blind sample n={len(blind)}")


def main() -> None:
    print("== prepare ==")
    df = prepare()
    print("== analyze ==")
    analyze(df)
    print("== plots ==")
    make_plots()
    print("== blind sample ==")
    # reload labeled-friendly df
    df = pd.read_parquet(PROCESSED / "provider_collab.parquet")
    build_blind_sample(df)
    print("Done.")


if __name__ == "__main__":
    main()
