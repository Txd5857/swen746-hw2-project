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
## Testing

Run unit tests:
```bash
python -m pytest tests/test_repo.py -v
```