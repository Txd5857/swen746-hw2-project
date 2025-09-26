# tests/test_repo_miner.py

import os
import pandas as pd
import pytest
from datetime import datetime, timedelta
from src.repo_miner import fetch_commits

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