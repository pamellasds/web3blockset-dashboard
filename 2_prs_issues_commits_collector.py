"""Collect issues, PRs, and commits from GitHub repositories."""
import os
import csv
import yaml
import json
import time
import argparse
import requests
import sys
from datetime import datetime
from github import Github
from tqdm import tqdm
import pandas as pd

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "GITHUB_TOKEN")

class GitHubCollector:
    def __init__(self, mode):
        self.token = GITHUB_TOKEN
        self.github = Github(self.token)
        self.mode = mode
        
        self.base_dir = f"prs_issues_commits_collected/{mode}"
        self.data_dir = f"{self.base_dir}/data"
        self.checkpoints_dir = f"{self.base_dir}/checkpoints"
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.checkpoints_dir, exist_ok=True)
    
    def load_config(self, path):
        with open(path, 'r') as f:
            if path.endswith(('.yaml', '.yml')):
                return yaml.safe_load(f)
            return json.load(f)
    
    def get_checkpoint(self, repo_name):
        checkpoint = f"{self.checkpoints_dir}/{repo_name.replace('/', '_')}_checkpoint.json"
        try:
            with open(checkpoint, 'r') as f:
                data = json.load(f)
                return set(data.get('processed_issues', []))
        except FileNotFoundError:
            return set()
    
    def save_checkpoint(self, repo_name, processed_issues):
        checkpoint = f"{self.checkpoints_dir}/{repo_name.replace('/', '_')}_checkpoint.json"
        with open(checkpoint, 'w') as f:
            json.dump({
                'processed_issues': list(processed_issues),
                'last_updated': datetime.now().isoformat(),
                'total_processed': len(processed_issues)
            }, f, indent=2)
    def seed_checkpoints_from_csv(self, csv_path):
        """
        Pre-populate checkpoints and build a since-map from an existing issues_prs.csv.
        Returns a dict {repo_full_name: datetime} with the max updated_at per repo,
        so the API only fetches issues/PRs updated after the last known record.
        """
        if not os.path.exists(csv_path):
            print(f"[seed] CSV not found: {csv_path} — starting fresh.")
            return {}

        print(f"[seed] Loading existing records from {csv_path}...")
        df = pd.read_csv(
            csv_path,
            usecols=lambda c: c in ('repository', 'owner', 'issue_number', 'updated_at'),
            dtype={'repository': str, 'owner': str, 'issue_number': 'Int64'},
            parse_dates=['updated_at'],
            low_memory=False,
        )

        since_map = {}
        seeded = 0

        for (owner, repo), grp in df.groupby(['owner', 'repository']):
            repo_full = f"{owner}/{repo}"
            issue_numbers = set(grp['issue_number'].dropna().astype(int).tolist())

            # Write checkpoint so Script 2 skips these numbers
            self.save_checkpoint(repo_full, issue_numbers)
            seeded += len(issue_numbers)

            # Max updated_at → use as `since` parameter in GitHub API
            max_updated = grp['updated_at'].dropna().max()
            if pd.notna(max_updated):
                since_map[repo_full] = max_updated.to_pydatetime()

        print(f"[seed] Seeded checkpoints for {len(since_map)} repos ({seeded:,} known issues/PRs).")
        return since_map


    
    def check_rate_limit(self):
        try:
            headers = {'Authorization': f'token {self.token}'}
            r = requests.get('https://api.github.com/rate_limit', headers=headers, timeout=10)
            
            if r.status_code == 200:
                remaining = r.json()['resources']['core']['remaining']
                reset = r.json()['resources']['core']['reset']
                
                if remaining < 200:
                    wait = max(reset - time.time(), 0) + 10
                    print(f"Rate limit low, waiting {int(wait)}s...")
                    time.sleep(wait)
                elif remaining < 500:
                    time.sleep(1)
        except:
            time.sleep(30)
    
    def get_commit_count(self, repo, pr_number):
        try:
            return repo.get_pull(pr_number).commits
        except:
            return 0
    
    def collect_comments(self, issue):
        comments = []
        try:
            for c in issue.get_comments():
                comments.append({
                    "Comment ID": c.id,
                    "Issue/PR ID": issue.id,
                    "Issue/PR Number": issue.number,
                    "Issue/PR Type": "Pull Request" if issue.pull_request else "Issue",
                    "Comment Author": c.user.login,
                    "Comment Author ID": c.user.id,
                    "Comment Body": c.body,
                    "Comment Created At": c.created_at.isoformat() if c.created_at else None,
                    "Comment Updated At": c.updated_at.isoformat() if c.updated_at else None,
                    "User Type": "Organization" if c.user.type == "Organization" else 
                                ("Admin" if c.user.site_admin else "User")
                })
        except:
            pass
        return comments
    
    def collect_commits(self, repo, pr_number):
        commits = []
        try:
            pr = repo.get_pull(pr_number)
            for commit in pr.get_commits():
                try:
                    files_count = len(list(commit.files))
                except:
                    files_count = 0
                
                commits.append({
                    "Repository": repo.full_name.replace('/', '_'),
                    "Issue/PR Number": pr_number,
                    "Issue/PR Type": "Pull Request",
                    "Commit SHA": commit.sha,
                    "Commit Message": commit.commit.message,
                    "Commit Author": commit.author.login if commit.author else None,
                    "Commit Author Email": commit.commit.author.email,
                    "Commit Date": commit.commit.author.date.isoformat() if commit.commit.author.date else None,
                    "Files Changed": files_count,
                    "Additions": commit.stats.additions if commit.stats else 0,
                    "Deletions": commit.stats.deletions if commit.stats else 0
                })
        except:
            pass
        return commits
    
    def save_data(self, repo_name, issues, comments, commits, append=False):
        repo_dir = f"{self.data_dir}/{repo_name.replace('/', '_')}"
        os.makedirs(repo_dir, exist_ok=True)
        mode = 'a' if append else 'w'
        
        if issues:
            self._save_files(f"{repo_dir}/issues", issues, mode)
        if comments:
            self._save_files(f"{repo_dir}/comments", comments, mode)
        if commits:
            self._save_files(f"{repo_dir}/commits", commits, mode)
    
    def _save_files(self, base_path, data, mode):
        csv_path = f"{base_path}.csv"
        json_path = f"{base_path}.json"
        
        exists = os.path.exists(csv_path)
        with open(csv_path, mode, newline='', encoding='utf-8') as f:
            if data:
                writer = csv.DictWriter(f, fieldnames=list(data[0].keys()), 
                                       quoting=csv.QUOTE_ALL, escapechar='\\')
                if not exists or mode == 'w':
                    writer.writeheader()
                writer.writerows(data)
        
        if mode == 'a' and os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f) + data
            except:
                pass
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def collect_repositories(self, config, since_map=None):
        repos = config.get('repositories', [])
        if not repos:
            print("No repositories found in config")
            return
        
        print(f"Collecting from {len(repos)} provider repositories\n")
        
        for i, repo_url in enumerate(repos, 1):
            try:
                repo_name = repo_url.replace('https://github.com/', '')
                print(f"[{i}/{len(repos)}] {repo_name}")
                
                processed = self.get_checkpoint(repo_name)
                repo = self.github.get_repo(repo_name)

                issues_data = []
                comments_data = []
                commits_data = []

                since = since_map.get(repo_name) if since_map else None
                if since:
                    print(f"  Collecting since {since.date()} (incremental)")
                    issues = repo.get_issues(state='all', since=since)
                else:
                    issues = repo.get_issues(state='all')
                total = issues.totalCount
                print(f"  Total issues/PRs to fetch: {total}")
                
                for issue in tqdm(issues, total=min(total, 1000), desc="  Processing"):
                    if issue.number in processed:
                        continue
                    
                    self.check_rate_limit()
                    
                    is_pr = issue.pull_request is not None
                    
                    if issue.comments > 0:
                        comments_data.extend(self.collect_comments(issue))
                    
                    commit_count = 0
                    if is_pr:
                        commit_count = self.get_commit_count(repo, issue.number)
                        commits_data.extend(self.collect_commits(repo, issue.number))
                    
                    issue_data = {
                        'Repository': repo_name,
                        'Owner': repo.owner.login,
                        'Issue ID': issue.id,
                        'Issue Number': issue.number,
                        'Issue Title': issue.title,
                        'Issue Body': issue.body or '',
                        'State': issue.state,
                        'Created At': issue.created_at.isoformat() if issue.created_at else None,
                        'Updated At': issue.updated_at.isoformat() if issue.updated_at else None,
                        'Closed At': issue.closed_at.isoformat() if issue.closed_at else None,
                        'Author': issue.user.login,
                        'Author ID': issue.user.id,
                        'Locked': issue.locked,
                        'Number of Comments': issue.comments,
                        'Number of Commits': commit_count,
                        'Labels': ', '.join([l.name for l in issue.labels]),
                        'Type': "Pull Request" if is_pr else "Issue"
                    }
                    
                    issues_data.append(issue_data)
                    processed.add(issue.number)
                    
                    if len(issues_data) % 50 == 0:
                        self.save_data(repo_name, issues_data, comments_data, commits_data, append=True)
                        self.save_checkpoint(repo_name, processed)
                        issues_data, comments_data, commits_data = [], [], []
                
                if issues_data:
                    self.save_data(repo_name, issues_data, comments_data, commits_data, append=True)
                
                self.save_checkpoint(repo_name, processed)
                print(f"  Saved {len(processed)} issues/PRs\n")
                
            except Exception as e:
                print(f"  Error: {e}\n")
                continue
    
    def make_request_with_retry(self, url, headers, params, max_retries=3):
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, params=params, timeout=30)
                return response
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    print(f"  Request failed, retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise e
    
    def collect_search(self, config):
        search_patterns = config.get('search_patterns', {})
        mandatory_terms = config.get('mandatory_terms', [])
        
        if not search_patterns:
            print("No search patterns found")
            return
        
        print(f"Searching with {len(search_patterns)} keyword patterns\n")
        batch_data = {}
        
        for platform, keywords in search_patterns.items():
            print(f"\nPlatform: {platform}")
            
            for keyword in keywords:
                print(f"  Keyword: {keyword}")
                
                for page in range(1, 11):
                    try:
                        self.check_rate_limit()
                        
                        query = f'"{keyword}" in:title,body type:issue'
                        headers = {'Authorization': f'token {self.token}'}
                        params = {
                            'q': query,
                            'sort': 'created',
                            'order': 'desc',
                            'per_page': 100,
                            'page': page
                        }
                        
                        response = self.make_request_with_retry(
                            'https://api.github.com/search/issues',
                            headers,
                            params
                        )
                        
                        if response.status_code == 403:
                            print(f"  Rate limit.")
                            time.sleep(60)
                            continue
                        elif response.status_code != 200:
                            print(f"  Search failed: {response.status_code}")
                            break
                        
                        items = response.json().get('items', [])
                        if not items:
                            break
                        
                        print(f"  Page {page}: {len(items)} results")
                        
                        for item in items:
                            try:
                                repo_name = item['repository_url'].split('/repos/')[-1]
                                issue_num = item['number']
                                
                                processed = self.get_checkpoint(repo_name)
                                if issue_num in processed:
                                    continue
                                
                                if repo_name not in batch_data:
                                    batch_data[repo_name] = {
                                        'issues': [],
                                        'comments': [],
                                        'commits': [],
                                        'processed_numbers': processed
                                    }
                                
                                text = f"{item['title']} {item.get('body', '') or ''}".lower()
                                if keyword.lower() not in text:
                                    continue
                                
                                found_mandatory = [t for t in mandatory_terms if t.lower() in text]
                                if mandatory_terms and not found_mandatory:
                                    continue
                                
                                is_pr = 'pull_request' in item and item['pull_request'] is not None
                                owner = repo_name.split('/')[0]
                                
                                repo_obj = self.github.get_repo(repo_name)
                                issue_obj = repo_obj.get_issue(issue_num)
                                
                                if item['comments'] > 0:
                                    batch_data[repo_name]['comments'].extend(
                                        self.collect_comments(issue_obj)
                                    )
                                
                                commit_count = 0
                                if is_pr:
                                    commit_count = self.get_commit_count(repo_obj, issue_num)
                                
                                issue_data = {
                                    'Repository': repo_name,
                                    'Owner': owner,
                                    'Owner_Used': platform,
                                    'Issue ID': item['id'],
                                    'Issue Number': issue_num,
                                    'Issue Title': item['title'],
                                    'Issue Body': item.get('body', '') or '',
                                    'State': item['state'],
                                    'Created At': item['created_at'],
                                    'Updated At': item['updated_at'],
                                    'Closed At': item.get('closed_at'),
                                    'Author': item['user']['login'],
                                    'Author ID': item['user']['id'],
                                    'Locked': item['locked'],
                                    'Number of Comments': item['comments'],
                                    'Number of Commits': commit_count,
                                    'Labels': ', '.join([l['name'] for l in item.get('labels', [])]),
                                    'Type': "Pull Request" if is_pr else "Issue",
                                    'Matching Keywords': keyword,
                                    'Matching Mandatory Keywords': ", ".join(found_mandatory)
                                }
                                
                                batch_data[repo_name]['issues'].append(issue_data)
                                batch_data[repo_name]['processed_numbers'].add(issue_num)
                                
                            except Exception as e:
                                print(f"    Error: {e}")
                            
                            total = sum(len(d['issues']) for d in batch_data.values())
                            if total % 10 == 0 and total > 0:
                                print(f"  Saving batch ({total} issues)...")
                                for r_name, r_data in batch_data.items():
                                    if r_data['issues']:
                                        self.save_data(r_name, r_data['issues'], 
                                                     r_data['comments'], r_data['commits'], 
                                                     append=True)
                                        self.save_checkpoint(r_name, r_data['processed_numbers'])
                                        r_data['issues'], r_data['comments'], r_data['commits'] = [], [], []
                                time.sleep(1)
                        
                        time.sleep(2)
                        
                    except Exception as e:
                        print(f"  Error on page {page}: {e}")
                        break
        
        print("\nSaving final batch...")
        for repo_name, data in batch_data.items():
            if data['issues']:
                self.save_data(repo_name, data['issues'], data['comments'], 
                             data['commits'], append=True)
            if len(data['processed_numbers']) > 0:
                self.save_checkpoint(repo_name, data['processed_numbers'])


def main():
    parser = argparse.ArgumentParser(description='Collect GitHub issues, PRs, and commits')
    parser.add_argument('--providers', action='store_true', 
                       help='Collect from provider repos (uses repositories.yaml)')
    parser.add_argument('--communities', action='store_true',
                       help='Search community repos (uses keywords.json)')
    parser.add_argument('--since-csv', default='',
                       help='Path to existing issues_prs.csv to seed checkpoints and enable incremental collection')
    args = parser.parse_args()
    
    try:
        if args.providers:
            config_path = "additional_files/repositories.yaml"
            if not os.path.exists(config_path):
                print(f"Config not found: {config_path}")
                sys.exit(1)
            
            collector = GitHubCollector('providers')
            config = collector.load_config(config_path)
            since_map = {}
            if args.since_csv and os.path.exists(args.since_csv):
                since_map = collector.seed_checkpoints_from_csv(args.since_csv)
            collector.collect_repositories(config, since_map=since_map)
            print("\nProvider collection complete")
            
        else:
            config_path = "additional_files/keywords.json"
            if not os.path.exists(config_path):
                print(f"Config not found: {config_path}")
                sys.exit(1)
            
            collector = GitHubCollector('communities')
            config = collector.load_config(config_path)
            collector.collect_search(config)
            print("\nCommunity collection complete")
            
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()