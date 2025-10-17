# Repository Miner - RM1

A Python command-line tool for fetching GitHub repository commit data.

## Setup

1. Clone the repository:
```bash
git clone https://github.com/Txd5857/swen746-hw2-project.git
cd swen746-hw2-project
```

2. Install dependencies:
```bash
pip install pandas PyGithub pytest
```

3. Set up GitHub Personal Access Token:
```bash
# Windows PowerShell:
$env:GITHUB_TOKEN="your_github_token_here"

# macOS/Linux:
export GITHUB_TOKEN="your_github_token_here"
```

### GitHub Token Setup

1. Go to GitHub.com → Settings → Developer settings → Personal access tokens
2. Generate new token (classic) with `repo` scope
3. Copy the token (starts with `ghp_`)

## Usage

### Fetch Commits

Basic usage:
```bash
python -m src.repo_miner fetch-commits --repo owner/repo --out commits.csv
```

With commit limit:
```bash
python -m src.repo_miner fetch-commits --repo octocat/Hello-World --max 5 --out commits.csv
```

---

### RM2: Fetch Issues

Fetch issue data from a GitHub repository and save to CSV.
```bash
python -m src.repo_miner fetch-issues --repo owner/repo [--state all|open|closed] [--max 50] --out issues.csv
```

**Example:**
```bash
python -m src.repo_miner fetch-issues --repo microsoft/vscode --state all --max 100 --out data/issues.csv
```

**Options:**
- `--repo`: Repository in `owner/repo` format (required)
- `--state`: Filter by issue state: `all`, `open`, or `closed` (default: `all`)
- `--max`: Maximum number of issues to fetch (optional)
- `--out`: Output CSV file path (required)

**Output columns:** `id, number, title, user, state, created_at, closed_at, comments, open_duration_days`

**Features:**
- Excludes pull requests
- Dates in ISO-8601 format
- Calculates `open_duration_days` for closed issues

---

### RM3: Summarize

Analyze and summarize commit and issue data from CSV files.
```bash
python -m src.repo_miner summarize --commits commits.csv --issues issues.csv
```

**Example:**
```bash
python -m src.repo_miner summarize --commits data/commits.csv --issues data/issues.csv
```

**Options:**
- `--commits`: Path to commits CSV file (required)
- `--issues`: Path to issues CSV file (required)

**Output Metrics:**
- **Top 5 Committers**: Shows the top 5 contributors by commit count
- **Issue Close Rate**: Percentage of closed issues out of total issues
- **Average Issue Open Duration**: Average time (in days) issues remain open before being closed

#### Sample Results

Analysis of repository (100 commits, 100 issues):
```
============================================================
REPOSITORY SUMMARY
============================================================

Top 5 committers by commit count:
  Matt Bierner: 15 commits
  Benjamin Pasero: 10 commits
  Ladislau Szomoru: 5 commits
  Bryan Chen: 4 commits
  Harald Kirschner: 4 commits

Issue close rate: 0.77 (65/84 closed)

Avg. issue open duration: 0.01 days
  (based on 65 closed issues)

============================================================
```

---

## Testing

Run unit tests:
```bash
python -m pytest tests/test_repo.py -v
```