"""Combine GitHub data and filter bot content."""
import os
import pandas as pd
from pathlib import Path

class RepoCommentsCombiner:
    def __init__(self, mode, metadata_file="web3blockset/repositories.csv"):
        self.mode = mode
        self.metadata_file = metadata_file
        self.metadata_df = self._load_metadata()
        self.stats = {
            'initial_issues': 0,
            'bot_issues': 0,
            'initial_comments': 0,
            'bot_comments': 0
        }
        self.dedup_stats = {'before': 0, 'after': 0}
    
    def _load_metadata(self):
        if not Path(self.metadata_file).exists():
            print(f"Metadata file not found: {self.metadata_file}")
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(self.metadata_file, dtype=str)
            df['html_url'] = df['html_url'].str.strip().str.lower()
            print(f"Loaded metadata: {len(df)} repositories")
            return df
        except Exception as e:
            print(f"Error loading metadata: {e}")
            return pd.DataFrame()
    
    def is_bot(self, text):
        if not text or pd.isna(text):
            return False
        bot_keywords = ['bot', 'snyk', 'graphite', 'copilot', 'dependabot']
        return any(kw in str(text).lower() for kw in bot_keywords)
    
    def filter_bots(self, df, repo_name=None):
        if df.empty:
            return df
        
        initial = len(df)
        
        if 'Repository' in df.columns:
            bot_count = df['Repository'].apply(self.is_bot).sum()
            if bot_count > 0:
                print(f"  Removing {bot_count} bot repos")
                df = df[~df['Repository'].apply(self.is_bot)]
        
        if 'Author' in df.columns:
            bot_count = df['Author'].apply(self.is_bot).sum()
            if bot_count > 0:
                print(f"  Removing {bot_count} bot authors")
                df = df[~df['Author'].apply(self.is_bot)]
        
        for col in ['Issue Title', 'Issue Body', 'Concatenated Comments']:
            if col in df.columns:
                bot_count = df[col].apply(self.is_bot).sum()
                if bot_count > 0:
                    print(f"  Removing {bot_count} bot {col.lower()}")
                    df = df[~df[col].apply(self.is_bot)]
        
        removed = initial - len(df)
        if removed > 0:
            print(f"  Total removed: {removed}")
        
        return df
    
    def deduplicate(self, df):
        type_col = next((c for c in ['Type', 'type'] if c in df.columns), None)
        id_cols = [c for c in ['Issue ID', 'Issue Number'] if c in df.columns]
        
        if not id_cols:
            print("No ID columns found, skipping deduplication")
            return df
        
        sort_col = 'data_source' if 'data_source' in df.columns else None
        
        def dedup_group(subset, label):
            if subset.empty:
                return subset
            before = len(subset)
            if sort_col:
                subset = subset.sort_values(sort_col, ascending=False)
            subset = subset.drop_duplicates(subset=id_cols, keep='first')
            print(f"  {label}: {before} → {len(subset)}")
            return subset
        
        if type_col:
            type_lower = df[type_col].str.lower()
            issues = dedup_group(df[type_lower == 'issue'].copy(), "Issues")
            prs = dedup_group(df[type_lower == 'pull request'].copy(), "PRs")
            others = dedup_group(df[~type_lower.isin(['issue', 'pull request'])].copy(), "Others")
            
            frames = [f for f in [issues, prs, others] if not f.empty]
            result = pd.concat(frames, ignore_index=True) if frames else df
        else:
            result = dedup_group(df.copy(), "Records")
        
        return result
    
    def process_comments(self, comments_file, issues_df):
        if not comments_file.exists():
            return 0, 0
        
        try:
            comments_df = pd.read_csv(comments_file, dtype=str)
            initial = len(comments_df)
            
            bot_count = 0
            if 'Comment Author' in comments_df.columns:
                bot_count = comments_df['Comment Author'].apply(self.is_bot).sum()
                if bot_count > 0:
                    print(f"  Found {bot_count} bot comments")
                comments_df = comments_df[~comments_df['Comment Author'].apply(self.is_bot)]
            
            if not comments_df.empty and 'Issue/PR ID' in comments_df.columns:
                counts = comments_df.groupby('Issue/PR ID').size()
                groups = comments_df.groupby('Issue/PR ID').agg({
                    'Comment Body': lambda x: ' | '.join([str(c) for c in x if pd.notna(c) and str(c) != 'nan']),
                    'Comment Author': lambda x: '; '.join([str(a) for a in x if pd.notna(a) and str(a) != 'nan'])
                })
                
                for issue_id, row in groups.iterrows():
                    mask = issues_df['Issue ID'] == issue_id
                    issues_df.loc[mask, 'Concatenated Comments'] = row['Comment Body']
                    issues_df.loc[mask, 'Comment Authors'] = row['Comment Author']
                    if issue_id in counts:
                        issues_df.loc[mask, 'Number of Comments (Filtered)'] = counts[issue_id]
            
            return initial, bot_count
            
        except Exception as e:
            print(f"  Error processing comments: {e}")
            return 0, 0
    
    def process_repo(self, repo_path):
        issues_file = repo_path / "issues.csv"
        comments_file = repo_path / "comments.csv"
        
        if not issues_file.exists():
            return None, 0, 0, 0, 0
        
        print(f"  {repo_path.name}")
        
        try:
            issues_df = pd.read_csv(issues_file, dtype=str)
            initial_issues = len(issues_df)
        except Exception as e:
            print(f"    Error reading: {e}")
            return None, 0, 0, 0, 0
        
        bot_issues = 0
        if 'Author' in issues_df.columns:
            bot_issues = issues_df['Author'].apply(self.is_bot).sum()
            if bot_issues > 0:
                print(f"    Found {bot_issues} bot issues/PRs")
            issues_df = issues_df[~issues_df['Author'].apply(self.is_bot)]
        
        if issues_df.empty:
            return None, initial_issues, bot_issues, 0, 0
        
        issues_df['Concatenated Comments'] = ''
        issues_df['Comment Authors'] = ''
        issues_df['Number of Comments (Filtered)'] = 0
        
        initial_comments, bot_comments = self.process_comments(comments_file, issues_df)
        
        issues_df = self.filter_bots(issues_df, repo_path.name)
        
        return issues_df, initial_issues, bot_issues, initial_comments, bot_comments
    
    def combine_repos(self):
        data_path = Path(f"prs_issues_commits_collected/{self.mode}/data")
        
        if not data_path.exists():
            print(f"Data directory not found: {data_path}")
            return None
        
        print(f"Processing {self.mode} data from {data_path}\n")
        all_data = []
        
        for repo_dir in data_path.iterdir():
            if not repo_dir.is_dir() or self.is_bot(repo_dir.name):
                if self.is_bot(repo_dir.name):
                    print(f"Skipping bot repo: {repo_dir.name}")
                continue
            
            result = self.process_repo(repo_dir)
            if result[0] is not None and not result[0].empty:
                repo_data = result[0]
                
                if '_' in repo_dir.name:
                    parts = repo_dir.name.split('_', 1)
                    owner = parts[0]
                    repo_name = parts[1] if len(parts) > 1 else repo_dir.name
                    
                    if self.is_bot(owner):
                        print(f"  Skipping bot owner: {owner}")
                        continue
                    
                    repo_data['Repository'] = f"{owner}/{repo_name}"
                    repo_data['Owner'] = owner
                else:
                    repo_data['Repository'] = repo_dir.name
                    repo_data['Owner'] = "unknown"
                
                all_data.append(repo_data)
                print(f"  Added {len(repo_data)} records")
            
            self.stats['initial_issues'] += result[1]
            self.stats['bot_issues'] += result[2]
            self.stats['initial_comments'] += result[3]
            self.stats['bot_comments'] += result[4]
        
        return self._finalize(all_data)
    
    def _finalize(self, all_data):
        if not all_data:
            print("No data to combine")
            return None
        
        df = pd.concat(all_data, ignore_index=True)
        
        initial = len(df)
        df = self.filter_bots(df)
        filtered = initial - len(df)
        if filtered > 0:
            print(f"Removed {filtered} additional bot records")
        
        if not self.metadata_df.empty:
            df = self._merge_metadata(df)
        
        self.dedup_stats['before'] = len(df)
        df = self.deduplicate(df)
        self.dedup_stats['after'] = len(df)
        
        base_cols = ['Repository', 'Owner']
        other_cols = [c for c in df.columns if c not in base_cols]
        df = df[base_cols + other_cols]
        
        return df
    
    def _merge_metadata(self, df):
        df['repo_lower'] = df['Repository'].str.lower().str.strip()
        
        meta = self.metadata_df.copy()
        meta['repo_name'] = meta['html_url'].str.replace(
            "https://github.com/", "", regex=False
        ).str.lower().str.strip()
        
        merged = df.merge(
            meta[['repo_name', 'organization']],
            left_on='repo_lower',
            right_on='repo_name',
            how='left',
            suffixes=('', '_meta')
        )
        
        if 'organization_meta' in merged.columns:
            merged['Owner'] = merged['organization_meta'].fillna(merged['Owner'])
            merged.drop(columns=['organization_meta'], inplace=True)
        
        merged.drop(columns=['repo_lower', 'repo_name'], inplace=True)
        return merged
    
    def save(self, df):
        if df is None:
            print("No data to save")
            return
        
        os.makedirs('repo_comments_combiner_collected', exist_ok=True)
        output = f'repo_comments_combiner_collected/{self.mode}_combined.csv'
        
        df.to_csv(output, index=False, encoding='utf-8')
        
        print(f"\nSaved: {output}")
        print(f"Total records: {len(df)}")
        
        print(f"\n{'=' * 50}")
        print("Bot Filtering Summary:")
        print(f"  Issues/PRs: {self.stats['initial_issues']} → {self.stats['initial_issues'] - self.stats['bot_issues']}")
        print(f"  (removed {self.stats['bot_issues']} bots)")
        print(f"  Comments: {self.stats['initial_comments']} → {self.stats['initial_comments'] - self.stats['bot_comments']}")
        print(f"  (removed {self.stats['bot_comments']} bots)")


def main():
    modes = [
        ('providers', "prs_issues_commits_collected/providers/data"),
        ('communities', "prs_issues_commits_collected/communities/data")
    ]
    
    for mode, path_str in modes:
        if Path(path_str).exists():
            print(f"\n{'=' * 60}")
            print(f"Processing {mode.upper()}")
            print('=' * 60)
            
            combiner = RepoCommentsCombiner(mode)
            combined = combiner.combine_repos()
            combiner.save(combined)
            
            print(f"\n{mode.capitalize()} complete")
        else:
            print(f"\nNo {mode} data found at {path_str}")
    
    print("\n" + "=" * 60)
    print("Data combination finished!")
    print("=" * 60)


if __name__ == "__main__":
    main()