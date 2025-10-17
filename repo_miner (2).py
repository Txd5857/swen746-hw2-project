#!/usr/bin/env python3
"""
repo_miner.py

A command-line tool to:
  1) Fetch and normalize commit data from GitHub
  2) Fetch and normalize issue data from GitHub
  3) Merge data and print summary metrics

Sub-commands:
  - fetch-commits
  - fetch-issues
  - summarize
"""

import os
import argparse
import pandas as pd
from github import Github

# def fetch_commits(repo_name: str, max_commits: int = None) -> pd.DataFrame:
#     """
#     Fetch up to `max_commits` from the specified GitHub repository.
#     Returns a DataFrame with columns: sha, author, email, date, message.
#     """


# def fetch_issues(repo_name: str, state: str = "all", max_issues: int = None) -> pd.DataFrame:
#     """
#     Fetch up to `max_issues` from the specified GitHub repository (issues only).
#     Returns a DataFrame with columns: id, number, title, user, state, created_at, closed_at, comments.
#     """


def merge_and_summarize(commits_df: pd.DataFrame, issues_df: pd.DataFrame) -> None:
    """
    Takes two DataFrames (commits and issues) and prints:
      - Top 5 committers by commit count
      - Issue close rate (closed/total)
      - Average open duration for closed issues (in days)
    """
    # Copy to avoid modifying original data
    commits = commits_df.copy()
    issues  = issues_df.copy()

    # 1) Normalize date/time columns to pandas datetime
    commits['date']      = pd.to_datetime(commits['date'], errors='coerce')
    # TODO issues['created_at'] = ...
    # issues['closed_at']  = ...

    # 2) Top 5 committers

    # 3) Calculate issue close rate

    # 4) Compute average open duration (days) for closed issues


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
    # c1 = subparsers.add_parser("fetch-commits", help="Fetch commits and save to CSV")
    # c1.add_argument("--repo", required=True, help="Repository in owner/repo format")
    # c1.add_argument("--max",  type=int, dest="max_commits",
    #                 help="Max number of commits to fetch")
    # c1.add_argument("--out",  required=True, help="Path to output commits CSV")

    # Sub-command: fetch-issues
    # c2 = subparsers.add_parser("fetch-issues", help="Fetch issues and save to CSV")
    # c2.add_argument("--repo",  required=True, help="Repository in owner/repo format")
    # c2.add_argument("--state", choices=["all","open","closed"], default="all",
    #                 help="Filter issues by state")
    # c2.add_argument("--max",   type=int, dest="max_issues",
    #                 help="Max number of issues to fetch")
    # c2.add_argument("--out",   required=True, help="Path to output issues CSV")

    # Sub-command: summarize
    c3 = subparsers.add_parser("summarize", help="Summarize commits and issues")
    c3.add_argument("--commits", required=True, help="Path to commits CSV file")
    c3.add_argument("--issues",  required=True, help="Path to issues CSV file")

    args = parser.parse_args()

    # Dispatch based on selected command
    # if args.command == "fetch-commits":
    #     df = fetch_commits(args.repo, args.max_commits)
    #     df.to_csv(args.out, index=False)
    #     print(f"Saved {len(df)} commits to {args.out}")

    # elif args.command == "fetch-issues":
    #     df = fetch_issues(args.repo, args.state, args.max_issues)
    #     df.to_csv(args.out, index=False)
    #     print(f"Saved {len(df)} issues to {args.out}")

    if args.command == "summarize":
        # Read CSVs into DataFrames
        commits_df = pd.read_csv(args.commits)
        issues_df  = pd.read_csv(args.issues)
        # Generate and print the summary
        merge_and_summarize(commits_df, issues_df)

if __name__ == "__main__":
    main()
