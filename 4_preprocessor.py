"""Preprocess GitHub issues and PRs for analysis."""
import pandas as pd
import re
import time
import os
from pathlib import Path
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import nltk

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

class DataProcessor:
    def __init__(self):
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))
        
        # Domain-specific stopwords
        self.stop_words.update([
            "nan", "thanks", "ok", "summary", "change", "update", "changes", "updates",
            "platform", "decentralized", "undefined", "thank", "summari", "chang",
            "updat", "decentr", "undefin", "patch", "merg", "pr", "unchang",
            "changeset", "overview", "commit"
        ])
    
    def clean_text(self, text):
        if not isinstance(text, str):
            return ""
        
        # Remove code blocks and technical elements
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`[^`]*`', '', text)
        text = re.sub(r'http[s]?://[^\s]+', '', text)
        text = re.sub(r'<[^>]*>', ' ', text)
        return text
    
    def normalize_text(self, text):
        if not isinstance(text, str):
            return ""
        
        text = self.clean_text(text).lower()
        
        # Technical patterns to remove
        patterns = [
            r'0x[a-fA-F0-9]+',
            r'[a-fA-F0-9]{32,}',
            r'\d{4}-\d{2}-\d{2}',
            r'\B@\w+\b',
            r'\b\d+\b',
            r'[^\w\s-]'
        ]
        
        for pattern in patterns:
            text = re.sub(pattern, ' ', text)
        
        return text
    
    def filter_words(self, text):
        words = text.split()
        filtered = [
            w for w in words 
            if len(w) >= 3 and w.isalpha() and w not in self.stop_words and w.strip()
        ]
        return ' '.join(filtered).strip()
    
    def preprocess(self, text, use_stemming=False):
        processed = self.filter_words(self.normalize_text(text))
        
        if use_stemming:
            words = processed.split()
            return ' '.join([self.stemmer.stem(w) for w in words if len(w) >= 3])
        
        return processed
    
    def filter_by_length(self, df, min_words=15):
        before = len(df)
        word_counts = df['clean_text'].apply(
            lambda x: len(str(x).split()) if pd.notna(x) else 0
        )
        df_filtered = df[word_counts >= min_words].copy()
        removed = before - len(df_filtered)
        
        if removed > 0:
            print(f"Removed {removed} docs with < {min_words} words")
        
        return df_filtered
    
    def standardize_columns(self, df):
        mapping = {
            'Issue ID': 'issue_id',
            'Issue Number': 'issue_number',
            'Issue Title': 'issue_title',
            'Issue Body': 'issue_body',
            'Repository': 'repository',
            'Owner': 'owner',
            'Owner_Used': 'owner_used',
            'Author ID': 'author_id',
            'Author': 'author',
            'Created At': 'created_at',
            'Updated At': 'updated_at',
            'Closed At': 'closed_at',
            'State': 'state',
            'Labels': 'labels',
            'Locked': 'locked',
            'Number of Comments': 'comments_count',
            'Number of Comments (Filtered)': 'comments_count_filtered',
            'Number of Commits': 'commits_count',
            'Concatenated Comments': 'concatenated_comments',
            'Comment Authors': 'comment_authors',
            'Type': 'type',
            'Concatenated Comment': 'concatenated_comment',
            'Matching Keywords': 'matching_keywords',
            'Matching Mandatory Keywords': 'matching_mandatory_keywords'
        }
        return df.rename(columns=mapping)
    
    def clean_dataframe(self, df):
        df = df.dropna(subset=['Issue ID']).copy()
        df = self.standardize_columns(df)
        
        if 'repository' in df.columns:
            df['repository'] = df['repository'].apply(
                lambda x: x.split('/')[-1] if isinstance(x, str) and '/' in x else x
            )
        
        df['year'] = pd.to_datetime(df['created_at'], errors='coerce').dt.year
        
        return df
    
    def combine_text(self, df):
        comments_col = 'concatenated_comment' if 'concatenated_comment' in df.columns else 'concatenated_comments'
        
        df['raw_text'] = (
            df['issue_title'].fillna('') + ' ' +
            df['issue_body'].fillna('') + ' ' +
            df[comments_col].fillna('')
        )
        
        return df
    
    def process_text_columns(self, df):
        print("Processing text columns...")
        df['clean_text'] = df['raw_text'].apply(lambda x: self.preprocess(x, False))
        df['stemmed_text'] = df['raw_text'].apply(lambda x: self.preprocess(x, True))
        return df
    
    def process_dataset(self, input_file, dataset_type):
        print(f"\nProcessing {dataset_type} from {input_file}...")
        
        try:
            df = pd.read_csv(input_file)
            print(f"Initial: {len(df)} records")
            
            df = self.clean_dataframe(df)
            df = self.combine_text(df)
            df = self.process_text_columns(df)
            df = self.filter_by_length(df)
            
            df['data_source'] = dataset_type
            
            print(f"Final: {len(df)} records")            
            return df
            
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def deduplicate(self, df):
        print("\nDeduplicating...")
        print(f"Before: {len(df)}")
        
        issues = df[df['type'].str.lower() == 'issue'].copy() if 'type' in df.columns else pd.DataFrame()
        prs = df[df['type'].str.lower() == 'pull request'].copy() if 'type' in df.columns else pd.DataFrame()
        
        if len(issues) > 0:
            before = len(issues)
            issues = (
                issues.sort_values('data_source', ascending=False)
                .drop_duplicates(subset=['issue_id', 'issue_number'], keep='first')
            )
            print(f"  Issues: {before} → {len(issues)}")
        
        if len(prs) > 0:
            before = len(prs)
            prs = (
                prs.sort_values('data_source', ascending=False)
                .drop_duplicates(subset=['issue_id', 'issue_number'], keep='first')
            )
            print(f"  PRs: {before} → {len(prs)}")
        
        if len(issues) > 0 and len(prs) > 0:
            result = pd.concat([issues, prs], ignore_index=True)
        elif len(issues) > 0:
            result = issues
        else:
            result = prs
        
        print(f"After: {len(result)}")
        return result
    
    def process_all(self):
        print("=" * 60)
        print("Starting preprocessing pipeline")
        print("=" * 60)
        
        datasets = [
            {
                'input': "repo_comments_combiner_collected/providers_combined.csv",
                'type': 'provider'
            },
            {
                'input': "repo_comments_combiner_collected/communities_combined.csv",
                'type': 'community'
            }
        ]
        
        processed = []
        for ds in datasets:
            if Path(ds['input']).exists():
                df = self.process_dataset(ds['input'], ds['type'])
                if df is not None:
                    processed.append(df)
            else:
                print(f"\nFile not found: {ds['input']}")
        
        if not processed:
            print("\nNo input files found")
            return None
        
        combined = pd.concat(processed, ignore_index=True)
        combined = self.deduplicate(combined)
        
        output = "web3blockset/issues_prs.csv"
        os.makedirs(os.path.dirname(output), exist_ok=True)
        combined.to_csv(output, index=False)
        
        print(f"\n{'=' * 60}")
        print(f"Saved: {output}")
        print(f"Total records: {len(combined)}")
        print(f"\nBy source:")
        print(f"  Providers: {len(combined[combined['data_source'] == 'provider'])}")
        
        prov = combined[combined['data_source'] == 'provider']
        if len(prov) > 0:
            print(f"    Issues: {len(prov[prov['type'].str.lower() == 'issue'])}")
            print(f"    PRs: {len(prov[prov['type'].str.lower() == 'pull request'])}")
        
        print(f"  Communities: {len(combined[combined['data_source'] == 'community'])}")
        
        comm = combined[combined['data_source'] == 'community']
        if len(comm) > 0:
            print(f"    Issues: {len(comm[comm['type'].str.lower() == 'issue'])}")
            print(f"    PRs: {len(comm[comm['type'].str.lower() == 'pull request'])}")
        
        print("=" * 60)
        
        return combined


def main():
    processor = DataProcessor()
    processor.process_all()


if __name__ == "__main__":
    main()