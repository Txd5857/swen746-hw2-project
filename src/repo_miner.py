#!/usr/bin/env python3
"""
repo_miner.py

A command-line tool to:
  1) Fetch and normalize commit data from GitHub

Sub-commands:
  - fetch-commits
"""

import os
import argparse
import pandas as pd
from github import Github, Auth

def fetch_commits(repo_name: str, max_commits: int = None) -> pd.DataFrame:
    """
    Fetch up to `max_commits` from the specified GitHub repository.
    Returns a DataFrame with columns: sha, author, email, date, message.
    """
    # 1) Read GitHub
    # 
    # b token from environment
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable not set")

    # 2) Initialize GitHub client and get the repo
    auth = Auth.Token(token)
    g = Github(auth=auth)
    repo = g.get_repo(repo_name)

    # 3) Fetch commit objects (paginated by PyGitHub)
    commits = repo.get_commits()

    # 4) Normalize each commit into a record dict
    records = []
    count = 0

    for commit in commits:
        if max_commits and count >= max_commits:
            break
            
        # Extract commit data
        sha = commit.sha
        author = commit.commit.author.name
        email = commit.commit.author.email
        date = commit.commit.author.date.isoformat()
        message = commit.commit.message.split('\n')[0]  # First line only
        
        records.append({
            'sha': sha,
            'author': author,
            'email': email,
            'date': date,
            'message': message
        })
        
        count += 1

    # 5) Build DataFrame from records
    if not records:
        # Create empty DataFrame with correct columns when no commits
        df = pd.DataFrame(columns=['sha', 'author', 'email', 'date', 'message'])
    else:
        df = pd.DataFrame(records)
    return df
    
def fetch_issues(repo_name: str, state: str = "all", max_issues: int = None) -> pd.DataFrame:
    """
    Fetch up to `max_issues` from the specified GitHub repository (issues only).
    Returns a DataFrame with columns: id, number, title, user, state, created_at, closed_at, comments, open_duration_days.
    """
    # 1) Read GitHub token from environment
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable not set")

    # 2) Initialize client and get the repo
    auth = Auth.Token(token)
    g = Github(auth=auth)
    repo = g.get_repo(repo_name)

    # 3) Fetch issues, filtered by state ('all', 'open', 'closed')
    issues = repo.get_issues(state=state)

    # 4) Normalize each issue (skip PRs)
    records = []
    for idx, issue in enumerate(issues):
        if max_issues and idx >= max_issues:
            break
        
        # Skip pull requests
        if issue.pull_request is not None:
            continue

        # Normalize dates to ISO-8601 format
        created_at = issue.created_at.isoformat() if issue.created_at else None
        closed_at = issue.closed_at.isoformat() if issue.closed_at else None
        
        # Calculate open_duration_days
        open_duration_days = None
        if issue.created_at and issue.closed_at:
            delta = issue.closed_at - issue.created_at
            open_duration_days = delta.days + (delta.seconds / 86400)  # Include fractional days
        
        # Append records
        records.append({
            'id': issue.id,
            'number': issue.number,
            'title': issue.title,
            'user': issue.user.login if issue.user else None,
            'state': issue.state,
            'created_at': created_at,
            'closed_at': closed_at,
            'comments': issue.comments,
            'open_duration_days': open_duration_days
        })

    # 5) Build DataFrame
    if not records:
        # Create empty DataFrame with correct columns when no issues
        df = pd.DataFrame(columns=['id', 'number', 'title', 'user', 'state', 
                                   'created_at', 'closed_at', 'comments', 'open_duration_days'])
    else:
        df = pd.DataFrame(records)
    
    return df

def merge_and_summarize(commits_df: pd.DataFrame, issues_df: pd.DataFrame) -> None:
    """
    Takes two DataFrames (commits and issues) and prints:
      - Top 5 committers by commit count
      - Issue close rate (closed/total)
      - Average open duration for clossed issues (in days)
    """
    # Copy to avoid modifying original data
    commits = commits_df.copy()
    issues = issues_df.copy()

    # 1) Normalize date/time columns to pandas datetime
    commits['date'] = pd.to_datetime(commits['date'], errors='coerce')
    issues['created_at'] = pd.to_datetime(issues['created_at'], errors='coerce')
    issues['closed_at'] = pd.to_datetime(issues['closed_at'], errors='coerce')

    print("=" * 60)
    print("REPOSITORY SUMMARY")
    print("=" * 60)
    print()

    # 2) Top 5 committers
    print("Top 5 committers by commit count:")
    if not commits.empty:
        top_committers = commits['author'].value_counts().head(5)
        for author, count in top_committers.items():
            print(f"  {author}: {count} commits")
    else:
        print("  No commit data available")
    print()

    # 3) Calculate issue close rate
    if not issues.empty:
        total_issues = len(issues)
        closed_issues = len(issues[issues['state'] == 'closed'])
        close_rate = closed_issues / total_issues if total_issues > 0 else 0
        print(f"Issue close rate: {close_rate:.2f} ({closed_issues}/{total_issues} closed)")
        print()

        # 4) Compute average open duration (days) for closed issues
        closed_with_dates = issues[
            (issues['state'] == 'closed') & 
            issues['created_at'].notna() & 
            issues['closed_at'].notna()
        ]
        
        if len(closed_with_dates) > 0:
            # Calculate duration in days
            durations = (closed_with_dates['closed_at'] - closed_with_dates['created_at']).dt.total_seconds() / 86400
            avg_duration = durations.mean()
            print(f"Avg. issue open duration: {avg_duration:.2f} days")
            print(f"  (based on {len(closed_with_dates)} closed issues)")
        else:
            print("Avg. issue open duration: N/A (no closed issues with valid dates)")
    else:
        print("Issue close rate: N/A (no issue data)")
        print("Avg. issue open duration: N/A (no issue data)")
    
    print()
    print("=" * 60)

def main():
    """
    Parse command-line arguments and dispatch to sub-commands.
    """
    parser = argparse.ArgumentParser(
        prog="repo_miner",
        description="Fetch GitHub commits/issues and summarize them"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Sub-command: fetch-commits
    c1 = subparsers.add_parser("fetch-commits", help="Fetch commits and save to CSV")
    c1.add_argument("--repo", required=True, help="Repository in owner/repo format")
    c1.add_argument("--max",  type=int, dest="max_commits",
                    help="Max number of commits to fetch")
    c1.add_argument("--out",  required=True, help="Path to output commits CSV")

    # Sub-command: fetch-issues
    c2 = subparsers.add_parser("fetch-issues", help="Fetch issues and save to CSV")
    c2.add_argument("--repo",  required=True, help="Repository in owner/repo format")
    c2.add_argument("--state", choices=["all","open","closed"], default="all",
                    help="Filter issues by state")
    c2.add_argument("--max",   type=int, dest="max_issues",
                    help="Max number of issues to fetch")
    c2.add_argument("--out",   required=True, help="Path to output issues CSV")

    # Sub-command: summarize
    c3 = subparsers.add_parser("summarize", help="Summarize commits and issues")
    c3.add_argument("--commits", required=True, help="Path to commits CSV file")
    c3.add_argument("--issues",  required=True, help="Path to issues CSV file")

    args = parser.parse_args()

    # Dispatch based on selected command
    if args.command == "fetch-commits":
        df = fetch_commits(args.repo, args.max_commits)
        df.to_csv(args.out, index=False)
        print(f"Saved {len(df)} commits to {args.out}")
    elif args.command == "fetch-issues":
        df = fetch_issues(args.repo, args.state, args.max_issues)
        df.to_csv(args.out, index=False)
        print(f"Saved {len(df)} issues to {args.out}")
    elif args.command == "summarize":
        commits_df = pd.read_csv(args.commits)
        issues_df = pd.read_csv(args.issues)
        merge_and_summarize(commits_df, issues_df)
        
if __name__ == "__main__":
    main()
