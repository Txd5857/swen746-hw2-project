# tests/test_repo_miner.py

import os
import pandas as pd
import pytest
from datetime import datetime, timedelta
from src.repo_miner import fetch_commits, fetch_issues

# --- Helpers for dummy GitHub API objects ---

class DummyAuthor:
    def __init__(self, name, email, date):
        self.name = name
        self.email = email
        self.date = date

class DummyCommitCommit:
    def __init__(self, author, message):
        self.author = author
        self.message = message

class DummyCommit:
    def __init__(self, sha, author, email, date, message):
        self.sha = sha
        self.commit = DummyCommitCommit(DummyAuthor(author, email, date), message)

class DummyUser:
    def __init__(self, login):
        self.login = login

class DummyIssue:
    def __init__(self, id_, number, title, user, state, created_at, closed_at, comments, is_pr=False):
        self.id = id_
        self.number = number
        self.title = title
        self.user = DummyUser(user)
        self.state = state
        self.created_at = created_at
        self.closed_at = closed_at
        self.comments = comments
        # attribute only on pull requests
        self.pull_request = DummyUser("pr") if is_pr else None

class DummyRepo:
    def __init__(self, commits, issues=None):  # Make issues optional
        self._commits = commits
        self._issues = issues if issues is not None else []

    def get_commits(self):
        return self._commits

    def get_issues(self, state="all"):
        # filter by state
        if state == "all":
            return self._issues
        return [i for i in self._issues if i.state == state]

_test_repo = None

class DummyGithub:
    def __init__(self, auth=None, login_or_token=None):
        pass
        
    def get_repo(self, repo_name):
        return _test_repo

@pytest.fixture(autouse=True)
def patch_env_and_github(monkeypatch):
    # Set fake token
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    # Patch Github class
    # from github import Github
    monkeypatch.setattr("src.repo_miner.Github", DummyGithub)
    monkeypatch.setattr("src.repo_miner.Auth.Token", lambda x: x)

# Helper global placeholder
# gh_instance = DummyGithub("fake-token")

# --- Tests for fetch_commits ---
# An example test case
def test_fetch_commits_basic():
    global _test_repo
    # Setup dummy commits
    now = datetime.now()
    commits = [
        DummyCommit("sha1", "Alice", "a@example.com", now, "Initial commit\nDetails"),
        DummyCommit("sha2", "Bob", "b@example.com", now - timedelta(days=1), "Bug fix")
    ]
    _test_repo = DummyRepo(commits, [])
    df = fetch_commits("any/repo")
    assert list(df.columns) == ["sha", "author", "email", "date", "message"]
    assert len(df) == 2
    assert df.iloc[0]["message"] == "Initial commit"

def test_fetch_commits_limit():
    global _test_repo
    # More commits than max_commits
    now = datetime.now()
    commits = [
        DummyCommit("sha1", "Alice", "a@example.com", now, "Commit 1"),
        DummyCommit("sha2", "Bob", "b@example.com", now, "Commit 2"),
        DummyCommit("sha3", "Charlie", "c@example.com", now, "Commit 3")
    ]
    _test_repo = DummyRepo(commits, [])  # Add empty issues list
    df = fetch_commits("any/repo", max_commits=2)
    assert len(df) == 2

def test_fetch_commits_empty():
    global _test_repo
    _test_repo = DummyRepo([], [])  # Add both empty commits and issues lists
    df = fetch_commits("any/repo")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0
    assert list(df.columns) == ["sha", "author", "email", "date", "message"]

# --- Tests for fetch_issues ---

def test_fetch_issues_excludes_prs():
    """Test 1: Verify that pull requests are excluded from results"""
    global _test_repo
    now = datetime.now()
    issues = [
        DummyIssue(1, 101, "Real Issue", "alice", "open", now, None, 0, is_pr=False),
        DummyIssue(2, 102, "Pull Request", "bob", "open", now, None, 2, is_pr=True),
        DummyIssue(3, 103, "Another Issue", "charlie", "closed", now - timedelta(days=2), now, 1, is_pr=False)
    ]
    _test_repo = DummyRepo([], issues)
    df = fetch_issues("any/repo", state="all")
    
    # Should only have 2 issues (PRs excluded)
    assert len(df) == 2
    assert df.iloc[0]["title"] == "Real Issue"
    assert df.iloc[1]["title"] == "Another Issue"
    # Verify no PR in results
    assert "Pull Request" not in df["title"].values


def test_fetch_issues_dates_parse_correctly():
    """Test 2: Verify that dates are normalized to ISO-8601 format"""
    global _test_repo
    now = datetime(2025, 9, 25, 14, 30, 0) 
    closed = datetime(2025, 9, 28, 10, 15, 0)
    
    issues = [
        DummyIssue(1, 101, "Issue A", "alice", "open", now, None, 0),
        DummyIssue(2, 102, "Issue B", "bob", "closed", now, closed, 2)
    ]
    _test_repo = DummyRepo([], issues)
    df = fetch_issues("any/repo", state="all")
    
    # Check that dates are ISO-8601 strings
    assert df.iloc[0]["created_at"] == "2025-09-25T14:30:00"
    assert df.iloc[0]["closed_at"] is None 
    
    assert df.iloc[1]["created_at"] == "2025-09-25T14:30:00"
    assert df.iloc[1]["closed_at"] == "2025-09-28T10:15:00"
    
    # Verify ISO-8601 format (contains 'T' separator and proper format)
    assert 'T' in df.iloc[0]["created_at"]
    assert 'T' in df.iloc[1]["closed_at"]


def test_fetch_issues_open_duration_days_accurate():
    """Test 3: Verify that open_duration_days is computed accurately"""
    global _test_repo
    now = datetime(2025, 9, 1, 12, 0, 0)
    
    # Case 1: Issue open for exactly 5 days
    closed_5days = now + timedelta(days=5)
    # Case 2: Issue open for 3.5 days (3 days and 12 hours)
    closed_3_5days = now + timedelta(days=3, hours=12)
    # Case 3: Still open issue (no closed_at)
    
    issues = [
        DummyIssue(1, 101, "5 Day Issue", "alice", "closed", now, closed_5days, 0),
        DummyIssue(2, 102, "3.5 Day Issue", "bob", "closed", now, closed_3_5days, 1),
        DummyIssue(3, 103, "Open Issue", "charlie", "open", now, None, 2)
    ]
    _test_repo = DummyRepo([], issues)
    df = fetch_issues("any/repo", state="all")
    
    # Check open_duration_days calculations
    assert df.iloc[0]["open_duration_days"] == 5.0
    assert df.iloc[1]["open_duration_days"] == 3.5
    assert pd.isna(df.iloc[2]["open_duration_days"])  
    
    # Verify column exists and has correct type
    assert "open_duration_days" in df.columns
