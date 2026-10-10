#!/usr/bin/env python3
"""Provider-only attention migration analysis for MSR 2027 short WIP.

Uses validated repository_category from Web3BlockSet providers only.
Single entrypoint: python analyze.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
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
TOP_CATS_PLOT = 8
SAMPLE_PER_STRATUM = 10
SAMPLE_SEED = 20270227

COLORS = [
    "#0F766E", "#B45309", "#1D4ED8", "#BE123C",
    "#047857", "#C2410C", "#0E7490", "#334155",
]
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


def _hhi(counts: pd.Series) -> float:
    if counts.empty or counts.sum() == 0:
        return float("nan")
    p = counts / counts.sum()
    return float((p**2).sum())


# ---------------------------------------------------------------------------
# 1) Prepare
# ---------------------------------------------------------------------------
def prepare() -> pd.DataFrame:
    """Load provider Issues/PRs; fill missing category from repositories.csv."""
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
            key = f"{owner}/{repo}".lower()
            cat = (row.get("repository_category") or "").strip() or repo_cat.get(key, "")
            if not cat:
                continue  # only validated categories

            rows.append(
                {
                    "issue_id": row.get("issue_id"),
                    "year": year,
                    "owner": owner,
                    "repository": repo,
                    "repo_key": f"{owner}/{repo}",
                    "type": (row.get("type") or "").strip(),
                    "state": (row.get("state") or "").strip().lower(),
                    "issue_title": (row.get("issue_title") or "")[:240],
                    "labels": (row.get("labels") or "")[:200],
                    "comments_count": row.get("comments_count") or 0,
                    "repository_category": cat,
                    "created_at": row.get("created_at") or "",
                    "closed_at": row.get("closed_at") or "",
                }
            )
            if i % 300_000 == 0:
                print(f"... scanned {i:,}", flush=True)

    df = pd.DataFrame(rows)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_parquet(PROCESSED / "provider_attention.parquet", index=False)
    print(f"provider docs={len(df):,} repos={df['repo_key'].nunique():,} cats={df['repository_category'].nunique()}")
    return df


# ---------------------------------------------------------------------------
# 2) Analyze
# ---------------------------------------------------------------------------
def analyze(df: pd.DataFrame) -> dict:
    TABLES.mkdir(parents=True, exist_ok=True)

    annual = (
        df.groupby(["year", "repository_category"], as_index=False)
        .agg(n_docs=("issue_id", "count"), n_repos=("repo_key", "nunique"))
    )
    annual["share_docs"] = annual.groupby("year")["n_docs"].transform(lambda s: s / s.sum())
    annual.to_csv(TABLES / "annual_category_attention.csv", index=False)

    # concentration among categories each year
    conc = []
    for year, g in annual.groupby("year"):
        ranked = g.sort_values("n_docs", ascending=False)
        top3 = ranked.head(3)["n_docs"].sum()
        conc.append(
            {
                "year": int(year),
                "n_docs": int(g["n_docs"].sum()),
                "n_categories": int(g["repository_category"].nunique()),
                "top3_share": float(top3 / g["n_docs"].sum()),
                "hhi_docs": _hhi(ranked.set_index("repository_category")["n_docs"]),
            }
        )
    concentration = pd.DataFrame(conc).sort_values("year")
    concentration.to_csv(TABLES / "yearly_concentration.csv", index=False)

    # rank mobility: rank of each category by docs/year
    ranks = annual.copy()
    ranks["rank"] = ranks.groupby("year")["n_docs"].rank(ascending=False, method="min")
    rank_pivot = ranks.pivot_table(index="repository_category", columns="year", values="rank")
    rank_pivot.to_csv(TABLES / "category_rank_by_year.csv")

    # top categories overall + rank delta first→last year
    overall = (
        df.groupby("repository_category", as_index=False)
        .agg(n_docs=("issue_id", "count"), n_repos=("repo_key", "nunique"))
        .sort_values("n_docs", ascending=False)
    )
    overall.to_csv(TABLES / "category_prevalence_overall.csv", index=False)

    y0, y1 = YEAR_MIN, YEAR_MAX
    r0 = ranks[ranks["year"] == y0].set_index("repository_category")["rank"]
    r1 = ranks[ranks["year"] == y1].set_index("repository_category")["rank"]
    mobility = pd.DataFrame({"rank_start": r0, "rank_end": r1}).dropna()
    mobility["rank_delta"] = mobility["rank_start"] - mobility["rank_end"]  # + = rose
    mobility = mobility.sort_values("rank_delta", ascending=False).reset_index()
    mobility.to_csv(TABLES / "category_rank_mobility.csv", index=False)

    # Issue vs PR mix by category (latest window)
    mix = (
        df[df["year"] >= 2023]
        .groupby(["repository_category", "type"], as_index=False)
        .size()
        .rename(columns={"size": "n"})
    )
    mix.to_csv(TABLES / "issue_pr_mix_2023_2025.csv", index=False)

    summary = {
        "year_min": YEAR_MIN,
        "year_max": YEAR_MAX,
        "n_docs": int(len(df)),
        "n_repos": int(df["repo_key"].nunique()),
        "n_categories": int(df["repository_category"].nunique()),
        "top3_share_start": float(concentration.loc[concentration["year"] == y0, "top3_share"].iloc[0]),
        "top3_share_end": float(concentration.loc[concentration["year"] == y1, "top3_share"].iloc[0]),
        "hhi_start": float(concentration.loc[concentration["year"] == y0, "hhi_docs"].iloc[0]),
        "hhi_end": float(concentration.loc[concentration["year"] == y1, "hhi_docs"].iloc[0]),
        "top_risers": mobility.head(5).to_dict(orient="records"),
        "top_fallers": mobility.tail(5).iloc[::-1].to_dict(orient="records"),
    }
    (TABLES / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ["n_docs", "n_repos", "n_categories", "top3_share_start", "top3_share_end"]}, indent=2))
    return summary


# ---------------------------------------------------------------------------
# 3) Plots (Plotly)
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
    annual = pd.read_csv(TABLES / "annual_category_attention.csv")
    overall = pd.read_csv(TABLES / "category_prevalence_overall.csv")
    conc = pd.read_csv(TABLES / "yearly_concentration.csv")
    mobility = pd.read_csv(TABLES / "category_rank_mobility.csv")

    ranks = annual.copy()
    ranks["rank"] = ranks.groupby("year")["n_docs"].rank(ascending=False, method="min")

    # Categories that enter the annual top-5 at least once → bump chart cast
    top5_any = set(ranks.loc[ranks["rank"] <= 5, "repository_category"])
    bump = ranks[ranks["repository_category"].isin(top5_any)].copy()
    bump_cats = (
        bump.groupby("repository_category")["n_docs"].sum().sort_values(ascending=False).index.tolist()
    )
    cmap_bump = {c: COLORS[i % len(COLORS)] for i, c in enumerate(bump_cats)}

    # --- Fig 1 (miolo): bump chart year-by-year composition of attention ---
    fig1 = go.Figure()
    for cat in bump_cats:
        g = bump[bump["repository_category"] == cat].sort_values("year")
        fig1.add_trace(
            go.Scatter(
                x=g["year"],
                y=g["rank"],
                mode="lines+markers",
                name=cat,
                line=dict(color=cmap_bump[cat], width=3),
                marker=dict(size=9, color=cmap_bump[cat], line=dict(width=1, color="white")),
                hovertemplate=(
                    f"<b>{cat}</b><br>Ano=%{{x}}<br>Rank=%{{y}}"
                    "<br>Share=%{customdata:.1%}<extra></extra>"
                ),
                customdata=g["share_docs"],
            )
        )
    fig1.update_layout(
        title="Composição ano a ano: quem está no centro da atenção? (bump chart)",
        yaxis=dict(
            title="Rank (1 = mais Issues/PRs)",
            autorange="reversed",
            dtick=1,
            gridcolor="#E2E8F0",
            zeroline=False,
        ),
    )
    fig1.update_xaxes(title="Ano", dtick=1, gridcolor="#E2E8F0")
    _save(fig1, "fig1_yearly_bump")

    top = overall.head(TOP_CATS_PLOT)["repository_category"].tolist()
    d = annual[annual["repository_category"].isin(top)].copy()
    cmap = {c: COLORS[i % len(COLORS)] for i, c in enumerate(top)}

    fig2 = px.area(
        d, x="year", y="share_docs", color="repository_category",
        color_discrete_map=cmap,
        title="Share de atenção por categoria (apoio ao bump)",
    )
    fig2.update_xaxes(title="Ano", dtick=1, gridcolor="#E2E8F0")
    fig2.update_yaxes(title="Share de documentos", tickformat=".0%", gridcolor="#E2E8F0")
    _save(fig2, "fig2_attention_share")

    fig3 = make_subplots(specs=[[{"secondary_y": True}]])
    fig3.add_trace(
        go.Scatter(
            x=conc["year"], y=conc["top3_share"], mode="lines+markers",
            name="Share top-3 categorias", line=dict(color=COLORS[0], width=3), marker=dict(size=8),
        ),
        secondary_y=False,
    )
    fig3.add_trace(
        go.Scatter(
            x=conc["year"], y=conc["hhi_docs"], mode="lines+markers",
            name="HHI", line=dict(color=COLORS[1], width=3, dash="dot"),
            marker=dict(size=8, symbol="diamond"),
        ),
        secondary_y=True,
    )
    fig3.update_layout(title="Concentração da atenção entre categorias do stack")
    fig3.update_xaxes(title="Ano", dtick=1, gridcolor="#E2E8F0")
    fig3.update_yaxes(title="Share top-3", range=[0, 1], secondary_y=False, gridcolor="#E2E8F0")
    fig3.update_yaxes(title="HHI", secondary_y=True)
    _save(fig3, "fig3_concentration")

    # --- Fig 4 (fecho): long-run mobility ---
    mob = pd.concat([mobility.head(5), mobility.tail(5)]).drop_duplicates().iloc[::-1]
    fig4 = go.Figure(
        go.Bar(
            x=mob["rank_delta"],
            y=mob["repository_category"],
            orientation="h",
            marker_color=[COLORS[0] if v >= 0 else COLORS[3] for v in mob["rank_delta"]],
            text=[f"{v:+.0f}" for v in mob["rank_delta"]],
            textposition="outside",
        )
    )
    fig4.update_layout(
        title=f"Fecho: mobilidade de rank {YEAR_MIN}→{YEAR_MAX} (quem subiu / quem desceu)",
        xaxis_title="Δ rank (+ = subiu)",
        yaxis_title="",
    )
    fig4.update_xaxes(gridcolor="#E2E8F0")
    _save(fig4, "fig4_rank_mobility")


# ---------------------------------------------------------------------------
# 4) Blind sample — validate attention construct (not category labels)
# ---------------------------------------------------------------------------
def build_blind_sample(df: pd.DataFrame) -> None:
    """Stratified by validated repository_category; blind to category for reviewers.

    Reviewers judge whether the document reflects development attention
    (maintenance/feature/bug work) vs noise/off-topic — protecting the construct,
    without re-labeling categories already validated in Web3BlockSet.
    """
    MANUAL.mkdir(parents=True, exist_ok=True)
    # keep major categories with enough volume
    counts = df["repository_category"].value_counts()
    keep = counts[counts >= 200].index.tolist()
    base = df[df["repository_category"].isin(keep)].copy()

    rng = np.random.default_rng(SAMPLE_SEED)
    parts = []
    for cat, g in base.groupby("repository_category"):
        n = min(SAMPLE_PER_STRATUM, len(g))
        idx = rng.choice(g.index.to_numpy(), size=n, replace=False)
        parts.append(g.loc[idx])
    sample = pd.concat(parts, ignore_index=True)
    sample = sample.sample(frac=1.0, random_state=SAMPLE_SEED).reset_index(drop=True)
    sample.insert(0, "review_id", [f"R{i:03d}" for i in range(1, len(sample) + 1)])

    sample[
        [
            "review_id", "repository_category", "year", "type", "owner", "repository",
            "issue_id", "issue_title", "labels", "state",
        ]
    ].to_csv(MANUAL / "key_mapping.csv", index=False)

    blind = sample[["review_id", "year", "type", "owner", "repository", "issue_title", "labels"]].copy()
    for col in [
        "is_development_attention",  # yes / no / unsure
        "attention_kind",  # maintenance | feature | bugfix | support_question | docs | other
        "evidence_span",
        "notes",
        "reviewer_id",
    ]:
        blind[col] = ""
    blind.to_csv(MANUAL / "blind_sample.csv", index=False)

    (
        sample.groupby("repository_category", as_index=False)
        .size()
        .rename(columns={"size": "n_sampled"})
        .to_csv(MANUAL / "stratum_counts.csv", index=False)
    )
    print(f"blind sample n={len(blind)} strata={sample['repository_category'].nunique()}")


def main() -> None:
    print("== prepare ==")
    df = prepare()
    print("== analyze ==")
    analyze(df)
    print("== plots ==")
    make_plots()
    print("== blind sample ==")
    build_blind_sample(df)
    print("Done.")


if __name__ == "__main__":
    main()
