"""Collect Web3 repository metadata from GitHub organizations."""
import requests
import csv
import time
import os
import yaml
import json
import logging

# Configuration
GITHUB_TOKEN = "GITHUB_TOKEN"
ORGANIZATIONS_FILE = "additional_files/web3_organizations.json"
OUTPUT_DIR = "./additional_files"
RATE_LIMIT_DELAY = 1.0
MIN_STARS = 300
MIN_ISSUES = 1

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class RepoInfoCollector:
    def __init__(self, token):
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        })
        
    def get_repos(self, owner):
        repos, page = [], 1
        
        while True:
            time.sleep(RATE_LIMIT_DELAY)
            
            url = f'https://api.github.com/orgs/{owner}/repos'
            response = self.session.get(url, params={'per_page': 100, 'page': page})
            
            if response.status_code == 404:
                url = f'https://api.github.com/users/{owner}/repos'
                response = self.session.get(url, params={'per_page': 100, 'page': page})
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch {owner}: {response.status_code}")
                break
            
            batch = response.json()
            if not batch:
                break
                
            repos.extend(batch)
            logger.info(f"{owner}: page {page} ({len(batch)} repos)")
            page += 1
            
        return repos


def load_organizations(filepath):
    with open(filepath, 'r') as f:
        orgs = json.load(f)
    
    if not isinstance(orgs, list):
        raise ValueError("Expected JSON array of organization names")
    
    return orgs


def filter_quality_repos(all_repos):
    unique = {}
    stats = {'filtered_stars': 0, 'filtered_issues': 0, 'no_issues': 0, 'dupes': 0}
    
    for repo in all_repos:
        url = repo.get('html_url')
        if not url or not repo.get('has_issues', True):
            stats['no_issues'] += 1
            continue
            
        stars = repo.get('stars', 0)
        issues = repo.get('open_issues', 0)
        
        if stars < MIN_STARS:
            stats['filtered_stars'] += 1
            continue
        if issues < MIN_ISSUES:
            stats['filtered_issues'] += 1
            continue
        
        if url in unique:
            stats['dupes'] += 1
            existing = unique[url]
            if stars < existing['stars']:
                continue
        
        unique[url] = {
            'url': url,
            'name': repo['full_name'],
            'stars': stars,
            'issues': issues,
            'organization': repo['organization']
        }
    
    results = sorted(unique.values(), key=lambda x: x['stars'], reverse=True)
    
    logger.info(f"Filtered: {stats['filtered_stars']} low stars, "
                f"{stats['filtered_issues']} low issues, "
                f"{stats['no_issues']} no issues, "
                f"{stats['dupes']} duplicates")
    logger.info(f"Quality repos: {len(results)}")
    
    return results


def save_csv(repos, filename):
    if not repos:
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=repos[0].keys())
        writer.writeheader()
        writer.writerows(repos)
    
    logger.info(f"Saved {len(repos)} repos to {filename}")


def save_yaml(quality_repos, filename):
    data = {'repositories': [r['url'] for r in quality_repos]}
    
    with open(filename, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    logger.info(f"Saved {len(quality_repos)} URLs to {filename}")


def main():
    print(f"Collecting Web3 repositories...")
    print(f"Filters: min {MIN_STARS} stars, min {MIN_ISSUES} issues\n")
    
    if GITHUB_TOKEN == "ghp_your_token_here":
        print("ERROR: Set your GitHub token first.")
        return
    
    try:
        organizations = load_organizations(ORGANIZATIONS_FILE)
        print(f"Loaded {len(organizations)} organizations\n")
    except Exception as e:
        print(f"Failed to load organizations: {e}")
        return
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    collector = RepoInfoCollector(GITHUB_TOKEN)
    
    all_repos = []
    for i, owner in enumerate(organizations, 1):
        logger.info(f"[{i}/{len(organizations)}] {owner}")
        repos = collector.get_repos(owner)
        
        for repo in repos:
            all_repos.append({
                'organization': owner,
                'repo_name': repo['name'],
                'full_name': repo['full_name'],
                'description': (repo.get('description') or '')[:200],
                'stars': repo.get('stargazers_count', 0),
                'forks': repo.get('forks_count', 0),
                'language': repo.get('language', ''),
                'created_at': repo.get('created_at', ''),
                'updated_at': repo.get('updated_at', ''),
                'archived': repo.get('archived', False),
                'size_kb': repo.get('size', 0),
                'has_issues': repo.get('has_issues', False),
                'open_issues': repo.get('open_issues_count', 0),
                'default_branch': repo.get('default_branch', 'main'),
                'clone_url': repo.get('clone_url', ''),
                'html_url': repo.get('html_url', '')
            })
    
    quality_repos = filter_quality_repos(all_repos)
    
    csv_path = os.path.join(OUTPUT_DIR, 'repositories_no_filtered.csv')
    yaml_path = os.path.join(OUTPUT_DIR, 'repositories.yaml')
    
    save_csv(all_repos, csv_path)
    save_yaml(quality_repos, yaml_path)

if __name__ == "__main__":
    main()