#!/usr/bin/env python3
"""WIP bridge: Web3BlockSet consensus practice × GitSkills verification instruction.

Single entrypoint: python analyze.py
"""

from __future__ import annotations

import csv
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parent
# Layout: .../2026_web3blockset_dashboard/{2027_msr, web3blockset}
#          .../phd/gitskills
W3 = ROOT.parent.parent / "web3blockset"
GS = ROOT.parent.parent.parent / "gitskills"
if not GS.exists():
    GS = Path("/home/pamella/Desktop/phd/gitskills")

PROCESSED = ROOT / "data" / "processed"
MANUAL = ROOT / "data" / "manual_review"
TABLES = ROOT / "results" / "tables"
FIGURES = ROOT / "results" / "figures"
PAPER_FIG = ROOT / "paper" / "figures"

YEAR_MIN, YEAR_MAX = 2018, 2025
SAMPLE_SEED = 20270401
SAMPLE_PER_BUCKET = 12

COLORS = ["#0F766E", "#B45309", "#1D4ED8", "#BE123C", "#047857", "#C2410C", "#0E7490", "#334155"]
LAYOUT = dict(
    font=dict(family="IBM Plex Sans, Segoe UI, sans-serif", size=13, color="#0F172A"),
    paper_bgcolor="#F8FAFC",
    plot_bgcolor="#F8FAFC",
    margin=dict(l=60, r=30, t=70, b=50),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None),
    width=920,
    height=520,
)

csv.field_size_limit(10**9)

CONSENSUS_KEYS = {
    "ethereum/consensus-specs",
    "ethereum/annotated-spec",
    "ethereum/beacon-APIs",
    "ethereum/execution-specs",
    "ethereum/EIPs",
    "sigp/lighthouse",
    "ConsenSys/teku",
}

BUCKETS = {
    "fork_choice": ["fork choice", "fork_choice", "forkchoice", "get_head", "reorg"],
    "finality_justification": ["finality", "justif", "finalize"],
    "attestation_aggregation": ["attestation", "aggregate"],
    "state_transition": ["state transition", "state_transition", "process_block", "process_slots"],
    "testing_verification": [
        "spec test", "consensus test", "formal", "model check",
        "property test", "invariant", "fuzz", "symbolic",
    ],
    "networking_p2p": ["libp2p", "gossip", "req/resp", "networking"],
}

GS_TERMS = [
    "fork choice",
    "consensus spec",
    "beacon chain",
    "formal verification",
    "model check",
    "property-based",
    "invariant test",
    "fuzzing",
]


def _year(v: str) -> int | None:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def prepare_w3() -> pd.DataFrame:
    rows = []
    with (W3 / "issues_prs.csv").open(newline="", encoding="utf-8", errors="replace") as fh:
        for i, row in enumerate(csv.DictReader(fh), 1):
            if (row.get("data_source") or "").lower() != "provider":
                continue
            owner = (row.get("owner") or row.get("organization") or "").strip()
            repo = (row.get("repository") or "").strip()
            key = f"{owner}/{repo}"
            if key not in CONSENSUS_KEYS:
                continue
            y = _year(row.get("year") or "")
            if y is None or y < YEAR_MIN or y > YEAR_MAX:
                continue
            title = row.get("issue_title") or ""
            body = (row.get("issue_body") or "")[:800]
            text = f"{title} {body}".lower()
            bucket = "other"
            for b, terms in BUCKETS.items():
                if any(t in text for t in terms):
                    bucket = b
                    break
            rows.append(
                {
                    "issue_id": row.get("issue_id"),
                    "year": y,
                    "repo_key": key,
                    "type": row.get("type"),
                    "issue_title": title[:240],
                    "repository_category": (row.get("repository_category") or "").strip(),
                    "concern_bucket": bucket,
                }
            )
            if i % 300_000 == 0:
                print(f"... scanned {i:,}", flush=True)

    df = pd.DataFrame(rows)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_parquet(PROCESSED / "consensus_practice.parquet", index=False)
    print(f"W3 consensus docs={len(df):,} repos={df['repo_key'].nunique()}")
    return df


def prepare_gitskills() -> dict:
    summary_path = GS / "data" / "test_types_filter" / "test_types_summary.json"
    layer_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    cache = PROCESSED / "gitskills_term_counts.json"
    PROCESSED.mkdir(parents=True, exist_ok=True)

    if cache.exists():
        term_counts = json.loads(cache.read_text(encoding="utf-8"))
        print("GitSkills term_counts (cache)", term_counts)
    else:
        # One-time scan (slow on large content blobs); results cached.
        db = GS / "gitskills_sample" / "agent_skills_mandatory_only.db"
        con = sqlite3.connect(f"file:{db.as_posix()}?immutable=1", uri=True)
        cur = con.cursor()
        term_counts = {}
        for t in GS_TERMS:
            print(f"  counting skills for '{t}'...", flush=True)
            cur.execute(
                """
                SELECT COUNT(*) FROM artifacts
                WHERE dedup_primary=1
                  AND (instr(lower(content), ?) > 0
                       OR instr(lower(coalesce(name,'')), ?) > 0
                       OR instr(lower(coalesce(description,'')), ?) > 0)
                """,
                (t, t, t),
            )
            term_counts[t] = int(cur.fetchone()[0])
        con.close()
        cache.write_text(json.dumps(term_counts, indent=2), encoding="utf-8")
        print("GitSkills term_counts", term_counts)

    out = {"layers": layer_summary, "term_counts": term_counts}
    (PROCESSED / "gitskills_signals.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out


def analyze(df: pd.DataFrame, gs: dict) -> dict:
    TABLES.mkdir(parents=True, exist_ok=True)

    by_bucket = (
        df["concern_bucket"].value_counts().rename_axis("bucket").reset_index(name="n_docs")
    )
    by_bucket.to_csv(TABLES / "w3_concern_buckets.csv", index=False)

    by_year_bucket = (
        df.groupby(["year", "concern_bucket"], as_index=False).size().rename(columns={"size": "n_docs"})
    )
    by_year_bucket.to_csv(TABLES / "w3_concern_by_year.csv", index=False)

    by_repo = (
        df.groupby(["repo_key", "concern_bucket"], as_index=False).size().rename(columns={"size": "n_docs"})
    )
    by_repo.to_csv(TABLES / "w3_concern_by_repo.csv", index=False)

    layers = gs["layers"]["by_layer"]
    layer_df = pd.DataFrame(
        [{"layer": k, "n_skills": v} for k, v in layers.items()]
    ).sort_values("n_skills", ascending=False)
    layer_df.to_csv(TABLES / "gitskills_layers.csv", index=False)

    terms = pd.DataFrame(
        [{"term": k, "n_skills": v} for k, v in gs["term_counts"].items()]
    ).sort_values("n_skills", ascending=False)
    terms.to_csv(TABLES / "gitskills_terms.csv", index=False)

    # gap table: practice buckets vs instruction proxies
    gap = pd.DataFrame(
        [
            {
                "practice_bucket": "fork_choice",
                "w3_docs": int((df["concern_bucket"] == "fork_choice").sum()),
                "skills_proxy_term": "fork choice",
                "skills_hits": gs["term_counts"].get("fork choice", 0),
            },
            {
                "practice_bucket": "attestation_aggregation",
                "w3_docs": int((df["concern_bucket"] == "attestation_aggregation").sum()),
                "skills_proxy_term": "beacon chain",
                "skills_hits": gs["term_counts"].get("beacon chain", 0),
            },
            {
                "practice_bucket": "finality_justification",
                "w3_docs": int((df["concern_bucket"] == "finality_justification").sum()),
                "skills_proxy_term": "consensus spec",
                "skills_hits": gs["term_counts"].get("consensus spec", 0),
            },
            {
                "practice_bucket": "testing_verification",
                "w3_docs": int((df["concern_bucket"] == "testing_verification").sum()),
                "skills_proxy_term": "formal verification",
                "skills_hits": gs["term_counts"].get("formal verification", 0),
            },
            {
                "practice_bucket": "testing_verification",
                "w3_docs": int((df["concern_bucket"] == "testing_verification").sum()),
                "skills_proxy_term": "model check",
                "skills_hits": gs["term_counts"].get("model check", 0),
            },
        ]
    )
    gap.to_csv(TABLES / "gap_practice_vs_skills.csv", index=False)

    summary = {
        "w3_docs": int(len(df)),
        "w3_repos": int(df["repo_key"].nunique()),
        "w3_buckets": by_bucket.set_index("bucket")["n_docs"].to_dict(),
        "gitskills_test_skills": int(gs["layers"]["n_skills"]),
        "gitskills_layers_focus": {
            k: layers[k] for k in ["unit", "fork", "fuzz_property", "formal_symbolic", "integration"]
        },
        "gitskills_terms": gs["term_counts"],
    }
    (TABLES / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2)[:800])
    return summary


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
    buckets = pd.read_csv(TABLES / "w3_concern_buckets.csv")
    buckets = buckets[buckets["bucket"] != "other"].sort_values("n_docs", ascending=True)
    layers = pd.read_csv(TABLES / "gitskills_layers.csv")
    focus = layers[layers["layer"].isin(
        ["unit", "integration", "system_e2e", "fork", "fuzz_property", "formal_symbolic", "coverage"]
    )].sort_values("n_skills", ascending=True)
    terms = pd.read_csv(TABLES / "gitskills_terms.csv").sort_values("n_skills", ascending=True)
    gap = pd.read_csv(TABLES / "gap_practice_vs_skills.csv")

    fig1 = go.Figure(
        go.Bar(
            x=buckets["n_docs"], y=buckets["bucket"], orientation="h",
            marker_color=COLORS[0],
            text=buckets["n_docs"], textposition="outside",
        )
    )
    fig1.update_layout(
        title="Web3BlockSet: preocupações em repos de consensus/spec/clients",
        xaxis_title="Nº de Issues/PRs (2018–2025)",
        yaxis_title="",
    )
    fig1.update_xaxes(gridcolor="#E2E8F0")
    _save(fig1, "fig1_w3_concerns")

    fig2 = go.Figure(
        go.Bar(
            x=focus["n_skills"], y=focus["layer"], orientation="h",
            marker_color=COLORS[1],
            text=focus["n_skills"], textposition="outside",
        )
    )
    fig2.update_layout(
        title="GitSkills: camadas de teste/verificação em skills blockchain",
        xaxis_title="Nº de skills (pool de tipos de teste)",
        yaxis_title="",
    )
    fig2.update_xaxes(gridcolor="#E2E8F0")
    _save(fig2, "fig2_gitskills_layers")

    fig3 = go.Figure(
        go.Bar(
            x=terms["n_skills"], y=terms["term"], orientation="h",
            marker_color=COLORS[2],
            text=terms["n_skills"], textposition="outside",
        )
    )
    fig3.update_layout(
        title="GitSkills: termos de consensus vs verificação genérica",
        xaxis_title="Nº de skills (mandatory_only, dedup)",
        yaxis_title="",
    )
    fig3.update_xaxes(gridcolor="#E2E8F0", type="log")
    _save(fig3, "fig3_gitskills_terms")

    # paired gap (normalize separately for readability)
    fig4 = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Prática (Web3BlockSet docs)", "Instrução a agents (GitSkills hits)"),
        shared_yaxes=False,
    )
    g = gap.drop_duplicates("skills_proxy_term")
    fig4.add_trace(
        go.Bar(
            x=g["w3_docs"], y=g["practice_bucket"], orientation="h",
            marker_color=COLORS[0], name="W3 docs",
        ),
        row=1, col=1,
    )
    fig4.add_trace(
        go.Bar(
            x=g["skills_hits"], y=g["skills_proxy_term"], orientation="h",
            marker_color=COLORS[3], name="skills",
        ),
        row=1, col=2,
    )
    fig4.update_layout(title="Gap preliminar: prática de consensus × instrução em skills", showlegend=False)
    fig4.update_xaxes(gridcolor="#E2E8F0")
    _save(fig4, "fig4_gap")


def build_blind_sample(df: pd.DataFrame) -> None:
    """Blind sample of consensus concerns for property-candidate labeling."""
    import numpy as np

    MANUAL.mkdir(parents=True, exist_ok=True)
    base = df[df["concern_bucket"] != "other"].copy()
    rng = np.random.default_rng(SAMPLE_SEED)
    parts = []
    for bucket, g in base.groupby("concern_bucket"):
        n = min(SAMPLE_PER_BUCKET, len(g))
        idx = rng.choice(g.index.to_numpy(), size=n, replace=False)
        parts.append(g.loc[idx])
    sample = pd.concat(parts, ignore_index=True)
    sample = sample.sample(frac=1.0, random_state=SAMPLE_SEED).reset_index(drop=True)
    sample.insert(0, "review_id", [f"R{i:03d}" for i in range(1, len(sample) + 1)])

    sample[
        ["review_id", "concern_bucket", "year", "repo_key", "type", "issue_id", "issue_title"]
    ].to_csv(MANUAL / "key_mapping.csv", index=False)

    blind = sample[["review_id", "year", "repo_key", "type", "issue_title"]].copy()
    for col in [
        "maps_to_spec_component",  # fork_choice|finality|attestation|state_transition|networking|other|unsure
        "property_sketch",  # free text safety/liveness/reachability sketch
        "is_verification_relevant",  # yes|no|unsure
        "notes",
        "reviewer_id",
    ]:
        blind[col] = ""
    blind.to_csv(MANUAL / "blind_sample.csv", index=False)
    print(f"blind sample n={len(blind)}")


def main() -> None:
    print("== W3 ==")
    df = prepare_w3()
    print("== GitSkills ==")
    gs = prepare_gitskills()
    print("== analyze ==")
    analyze(df, gs)
    print("== plots ==")
    make_plots()
    print("== sample ==")
    build_blind_sample(df)
    print("Done.")


if __name__ == "__main__":
    main()
