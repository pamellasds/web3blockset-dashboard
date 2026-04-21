#!/usr/bin/env bash
# =============================================================================
# Web3BlockSet — Quarterly Dataset Update Pipeline
# =============================================================================
#
# Usage:
#   ./update_pipeline.sh                          # Dashboard refresh only (from existing CSV)
#   ./update_pipeline.sh --full                   # Incremental data collection + dashboard refresh
#   ./update_pipeline.sh --full --update-repos    # Also re-discover repos from GitHub orgs (Step 1)
#
# --full        Runs Steps 2-4 (incremental: seeds checkpoints from existing CSV,
#               fetches only issues/PRs updated since last collection). Requires GITHUB_TOKEN.
# --update-repos  Also runs Step 1 (repo metadata discovery). Use when you want to
#               pick up new repos added to the tracked organizations.
# Default mode regenerates dashboard JSONs from the existing local CSV and
# commits/pushes the result to trigger a GitHub Pages redeploy.
#
# Cronjob — monthly (every 1st at 02:00 local time):
#   0 2 1 * * cd /home/pamella/Desktop/phd/web3blockset-dashboard && ./update_pipeline.sh >> logs/pipeline.log 2>&1
# =============================================================================

set -euo pipefail
export GIT_SSH_COMMAND="ssh -i /home/pamella/.ssh/id_ed25519 -o StrictHostKeyChecking=accept-new"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

FULL_PIPELINE=false
UPDATE_REPOS=false
for arg in "$@"; do
    case "$arg" in
        --full)          FULL_PIPELINE=true ;;
        --update-repos)  UPDATE_REPOS=true ;;
    esac
done

ISSUES_CSV="web3blockset/issues_prs.csv"
REPOS_CSV="web3blockset/repositories.csv"
DASHBOARD_DATA="web3blockset-dashboard/public/data"
LOG_FILE="UPDATE_LOG.md"
PIPELINE_LOG_DIR="logs"
UPDATE_DATE="$(date '+%Y-%m-%d %H:%M:%S %Z')"
UPDATE_DATE_SHORT="$(date '+%Y-%m-%d')"

mkdir -p "$PIPELINE_LOG_DIR"

echo "========================================================"
echo "  Web3BlockSet Dashboard Update"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "  Mode: $( [ "$FULL_PIPELINE" = true ] && echo 'Full Pipeline' || echo 'Dashboard Refresh' )"
echo "========================================================"

# ---------------------------------------------------------------------------
# Load .env if present
# ---------------------------------------------------------------------------
if [[ -f ".env" ]]; then
    echo "[info] Loading .env..."
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

# ---------------------------------------------------------------------------
# Validate GitHub Token if full pipeline is requested
# ---------------------------------------------------------------------------
if [[ "$FULL_PIPELINE" == true ]]; then
    if [[ -z "${GITHUB_TOKEN:-}" ]] || \
       [[ "$GITHUB_TOKEN" == "GITHUB_TOKEN" ]] || \
       [[ "$GITHUB_TOKEN" == "ghp_your_github_token_here" ]]; then
        echo "[error] GITHUB_TOKEN is not set or is a placeholder."
        echo "        Create a .env file with: GITHUB_TOKEN=your_real_token"
        exit 1
    fi
    echo "[info] GitHub token: ${GITHUB_TOKEN:0:8}..."
fi

# ---------------------------------------------------------------------------
# Capture previous quantitatives from overview.json
# ---------------------------------------------------------------------------
PREV_TOTAL=0; PREV_ISSUES=0; PREV_PRS=0; PREV_PROVIDER=0; PREV_COMMUNITY=0
PREV_REPOS=0; PREV_AUTHORS=0; PREV_UPDATED="unknown"

if [[ -f "$DASHBOARD_DATA/overview.json" ]]; then
    PREV_TOTAL=$(python3   -c "import json; d=json.load(open('$DASHBOARD_DATA/overview.json')); print(d.get('totalRecords',0))")
    PREV_ISSUES=$(python3  -c "import json; d=json.load(open('$DASHBOARD_DATA/overview.json')); print(d.get('totalIssues',0))")
    PREV_PRS=$(python3     -c "import json; d=json.load(open('$DASHBOARD_DATA/overview.json')); print(d.get('totalPRs',0))")
    PREV_PROVIDER=$(python3 -c "import json; d=json.load(open('$DASHBOARD_DATA/overview.json')); print(d.get('totalProviderRecords',0))")
    PREV_COMMUNITY=$(python3 -c "import json; d=json.load(open('$DASHBOARD_DATA/overview.json')); print(d.get('totalCommunityRecords',0))")
    PREV_REPOS=$(python3   -c "import json; d=json.load(open('$DASHBOARD_DATA/overview.json')); print(d.get('totalUniqueRepos',0))")
    PREV_AUTHORS=$(python3 -c "import json; d=json.load(open('$DASHBOARD_DATA/overview.json')); print(d.get('totalUniqueAuthors',0))")
    PREV_UPDATED=$(python3 -c "import json; d=json.load(open('$DASHBOARD_DATA/overview.json')); print(d.get('lastUpdated','unknown'))")
fi

echo ""
echo "[prev] Records  : $PREV_TOTAL  (Issues: $PREV_ISSUES | PRs: $PREV_PRS)"
echo "[prev] Repos    : $PREV_REPOS  — Authors: $PREV_AUTHORS"
echo "[prev] Last updated: $PREV_UPDATED"
echo ""

# ---------------------------------------------------------------------------
# FULL PIPELINE: re-collect data from GitHub API
# ---------------------------------------------------------------------------
if [[ "$FULL_PIPELINE" == true ]]; then

    if [[ "$UPDATE_REPOS" == true ]]; then
        echo "--- Step 1: Collecting repository metadata ---"
        python3 1_repo_info_collector.py
        echo ""
    else
        echo "--- Step 1: Skipped (use --update-repos to re-discover repos) ---"
        echo ""
    fi

    # Ensure repositories.yaml exists (needed by Step 2a)
    if [[ ! -f "additional_files/repositories.yaml" ]]; then
        echo "[info] repositories.yaml not found — generating from repositories.csv..."
        python3 -c "
import pandas as pd, yaml
df = pd.read_csv('web3blockset/repositories.csv')
urls = df['html_url'].dropna().str.strip().tolist()
yaml.dump({'repositories': urls}, open('additional_files/repositories.yaml','w'), default_flow_style=False)
print(f'Generated repositories.yaml with {len(urls)} repos')
"
    fi

    echo "--- Step 2a: Collecting provider issues/PRs/commits ---"
    python3 2_prs_issues_commits_collector.py --providers --since-csv "$ISSUES_CSV"

    echo ""
    echo "--- Step 2b: Collecting community issues/PRs (keyword search) ---"
    python3 2_prs_issues_commits_collector.py --communities

    echo ""
    echo "--- Step 3: Combining repo data + comment concatenation ---"
    python3 3_repo_comments_combiner.py

    echo ""
    echo "--- Step 4: Preprocessing text + deduplication ---"
    python3 4_preprocessor.py

fi

# ---------------------------------------------------------------------------
# Re-generate dashboard JSON files
# ---------------------------------------------------------------------------
echo ""
echo "--- Generating dashboard data ---"

if [[ ! -f "$ISSUES_CSV" ]]; then
    echo "[error] $ISSUES_CSV not found."
    echo "        Run --full to collect fresh data, or download the CSV from Zenodo."
    exit 1
fi

python3 web3blockset-dashboard/scripts/generate_data.py \
    --issues-csv "$ISSUES_CSV" \
    --repos-csv  "$REPOS_CSV"  \
    --output      "$DASHBOARD_DATA"

# ---------------------------------------------------------------------------
# Capture new quantitatives
# ---------------------------------------------------------------------------
NEW_TOTAL=$(python3    -c "import json; d=json.load(open('$DASHBOARD_DATA/overview.json')); print(d.get('totalRecords',0))")
NEW_ISSUES=$(python3   -c "import json; d=json.load(open('$DASHBOARD_DATA/overview.json')); print(d.get('totalIssues',0))")
NEW_PRS=$(python3      -c "import json; d=json.load(open('$DASHBOARD_DATA/overview.json')); print(d.get('totalPRs',0))")
NEW_PROVIDER=$(python3 -c "import json; d=json.load(open('$DASHBOARD_DATA/overview.json')); print(d.get('totalProviderRecords',0))")
NEW_COMMUNITY=$(python3 -c "import json; d=json.load(open('$DASHBOARD_DATA/overview.json')); print(d.get('totalCommunityRecords',0))")
NEW_REPOS=$(python3    -c "import json; d=json.load(open('$DASHBOARD_DATA/overview.json')); print(d.get('totalUniqueRepos',0))")
NEW_AUTHORS=$(python3  -c "import json; d=json.load(open('$DASHBOARD_DATA/overview.json')); print(d.get('totalUniqueAuthors',0))")

DELTA_TOTAL=$(( NEW_TOTAL - PREV_TOTAL ))
DELTA_ISSUES=$(( NEW_ISSUES - PREV_ISSUES ))
DELTA_PRS=$(( NEW_PRS - PREV_PRS ))
DELTA_PROVIDER=$(( NEW_PROVIDER - PREV_PROVIDER ))
DELTA_COMMUNITY=$(( NEW_COMMUNITY - PREV_COMMUNITY ))
DELTA_REPOS=$(( NEW_REPOS - PREV_REPOS ))
DELTA_AUTHORS=$(( NEW_AUTHORS - PREV_AUTHORS ))

fmt_delta() { local v=$1; [[ $v -ge 0 ]] && echo "+$v" || echo "$v"; }

echo ""
echo "[new ] Records  : $NEW_TOTAL  (Issues: $NEW_ISSUES | PRs: $NEW_PRS)"
echo "[new ] Repos    : $NEW_REPOS  — Authors: $NEW_AUTHORS"
echo "[delta] $(fmt_delta $DELTA_TOTAL) records  (Issues: $(fmt_delta $DELTA_ISSUES) | PRs: $(fmt_delta $DELTA_PRS))"

# ---------------------------------------------------------------------------
# Create UPDATE_LOG.md header if it doesn't exist
# ---------------------------------------------------------------------------
UPDATE_TYPE="$( [ "$FULL_PIPELINE" = true ] && echo 'Full Pipeline' || echo 'Dashboard Refresh' )"

if [[ ! -f "$LOG_FILE" ]]; then
    python3 -c "
header = '''# Web3BlockSet — Update Log

This file tracks quarterly updates to the Web3BlockSet dataset and dashboard.
Each entry records the update date, mode (full pipeline or dashboard refresh),
and the quantitative changes in that update.

---

'''
open('$LOG_FILE', 'w').write(header)
"
fi

# ---------------------------------------------------------------------------
# Append the new log entry (using Python for precise positioning)
# ---------------------------------------------------------------------------
python3 << PYEOF
import sys
log_path    = '$LOG_FILE'
date_str    = '$UPDATE_DATE'
utype       = '$UPDATE_TYPE'
prev_total  = $PREV_TOTAL
new_total   = $NEW_TOTAL
d_total     = $DELTA_TOTAL
prev_issues = $PREV_ISSUES
new_issues  = $NEW_ISSUES
d_issues    = $DELTA_ISSUES
prev_prs    = $PREV_PRS
new_prs     = $NEW_PRS
d_prs       = $DELTA_PRS
prev_prov   = $PREV_PROVIDER
new_prov    = $NEW_PROVIDER
d_prov      = $DELTA_PROVIDER
prev_comm   = $PREV_COMMUNITY
new_comm    = $NEW_COMMUNITY
d_comm      = $DELTA_COMMUNITY
prev_repos  = $PREV_REPOS
new_repos   = $NEW_REPOS
d_repos     = $DELTA_REPOS
prev_auth   = $PREV_AUTHORS
new_auth    = $NEW_AUTHORS
d_auth      = $DELTA_AUTHORS

def row(label, prev, new, delta):
    sign = '+' if delta >= 0 else ''
    return f'| {label:<22} | {prev:>10,} | {new:>10,} | {sign}{delta:>8,} |'

entry = f'''
## {date_str} — {utype}

| Metric                 |   Previous |    Current |    Delta |
|------------------------|------------|------------|----------|
{row('Total records',     prev_total,  new_total,  d_total)}
{row('Issues',            prev_issues, new_issues, d_issues)}
{row('Pull Requests',     prev_prs,    new_prs,    d_prs)}
{row('Provider records',  prev_prov,   new_prov,   d_prov)}
{row('Community records', prev_comm,   new_comm,   d_comm)}
{row('Unique repos',      prev_repos,  new_repos,  d_repos)}
{row('Unique authors',    prev_auth,   new_auth,   d_auth)}

---

'''

content = open(log_path).read()
# Prepend entry right after the header '---' line
sep = '\n---\n'
idx = content.find(sep)
if idx >= 0:
    content = content[:idx+len(sep)] + entry + content[idx+len(sep):]
else:
    content = content + entry
open(log_path, 'w').write(content)
print('[log] UPDATE_LOG.md updated')
PYEOF

# ---------------------------------------------------------------------------
# Git commit and push
# ---------------------------------------------------------------------------
echo ""
echo "--- Committing and pushing ---"

git add "$DASHBOARD_DATA/"
git add "$LOG_FILE"

git commit -m "chore: dataset update $UPDATE_DATE_SHORT

Records  : $PREV_TOTAL -> $NEW_TOTAL ($(fmt_delta $DELTA_TOTAL))
Issues   : $PREV_ISSUES -> $NEW_ISSUES ($(fmt_delta $DELTA_ISSUES))
PRs      : $PREV_PRS -> $NEW_PRS ($(fmt_delta $DELTA_PRS))
Provider : $PREV_PROVIDER -> $NEW_PROVIDER ($(fmt_delta $DELTA_PROVIDER))
Community: $PREV_COMMUNITY -> $NEW_COMMUNITY ($(fmt_delta $DELTA_COMMUNITY))
Mode     : $UPDATE_TYPE"

git push origin main

echo ""
echo "========================================================"
echo "  Done! GitHub Actions will rebuild and redeploy."
echo "  https://github.com/pamellasds/web3blockset-dashboard/actions"
echo "========================================================"
