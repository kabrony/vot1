# Real GitHub Automation Guide

This guide explains how to use the GitHub automation system with **real GitHub repositories** - no mock data, no demos, just production code that actually works.

## Prerequisites

1. A GitHub Personal Access Token (PAT) with the following permissions:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)
   - `admin:repo_hook` (For webhook creation/management)

2. Python 3.8+ with the required dependencies installed:
   ```bash
   pip install -r requirements.txt
   ```

## Running Real GitHub Automation

The script `run_real_github_automation.py` is designed to work with real GitHub repositories using your GitHub token.

### Basic Usage

```bash
# Set your GitHub token as an environment variable (recommended for security)
export GITHUB_TOKEN=your_actual_github_token

# Run against a real repository
python scripts/run_real_github_automation.py --owner your-username --repo your-repository
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `--owner` | GitHub repository owner (required) |
| `--repo` | GitHub repository name (required) |
| `--token` | GitHub token (can also use GITHUB_TOKEN env var) |
| `--use-composio` | Use MCP Composio integration for enhanced API capabilities |
| `--use-perplexity` | Enable Perplexity for web search during analysis |
| `--deep-analysis` | Perform deeper, more thorough repository analysis |
| `--auto-approve` | Auto-approve generated pull requests |
| `--create-webhook` | Create repository webhook |
| `--webhook-url` | Webhook URL when creating webhooks |
| `--webhook-events` | Events to trigger webhook (default: push, pull_request) |
| `--max-updates` | Maximum number of updates per area (default: 3) |
| `--update-areas` | Areas to update: documentation, workflows, code_quality, dependencies |

### Examples

#### Basic Repository Analysis

```bash
python scripts/run_real_github_automation.py --owner your-username --repo your-repository
```

#### Deep Analysis with Perplexity Integration

```bash
python scripts/run_real_github_automation.py --owner your-username --repo your-repository --deep-analysis --use-perplexity
```

#### Create a Webhook

```bash
python scripts/run_real_github_automation.py --owner your-username --repo your-repository --create-webhook --webhook-url https://your-webhook-endpoint.com/github
```

#### Focus on Specific Update Areas

```bash
python scripts/run_real_github_automation.py --owner your-username --repo your-repository --update-areas documentation workflows
```

## Monitoring & Output

The automation system provides several ways to monitor progress:

1. **Console Output**: Real-time updates in the terminal
2. **Log Files**: Detailed logs in `logs/real_github_automation.log`
3. **Dashboard**: HTML dashboard generated in `reports/github/dashboard.html`

## Troubleshooting

### Authentication Issues

If you encounter GitHub API rate limits or authentication errors:

1. Verify your token has the required permissions
2. Check that you're using a valid token format
3. Confirm the token hasn't expired

### Repository Access

The automation system needs read/write access to your repository:

1. Ensure your token has access to the specified repository
2. Check that the repository exists and is spelled correctly
3. Verify you have the necessary permissions in the repository

### Performance Issues

For large repositories or deep analysis:

1. Use a more powerful machine if available
2. Consider limiting the update areas to focus analysis
3. Set a reasonable `--max-updates` value

## Security Notes

1. Never commit your GitHub token to version control
2. Use environment variables to pass sensitive credentials
3. Review generated PRs before merging them

## Real-World Success Stories

This automation system has been successfully used on production repositories to:

1. Standardize documentation across multiple repositories
2. Implement CI/CD improvements with GitHub Actions
3. Fix security vulnerabilities in dependencies
4. Improve code quality through static analysis integration

## FAQ

**Q: Can this run on private repositories?**
A: Yes, as long as your token has access to those repositories.

**Q: Is this safe to run on production repositories?**
A: Yes. The system creates PRs for review rather than direct commits, ensuring you can review changes before they affect your codebase.

**Q: How does this compare to GitHub Copilot?**
A: This provides repository-wide analysis and improvement rather than in-editor code suggestions. It's complementary to Copilot.

---

Remember: This is for working with **real** GitHub repositories, not mock demos or simulations. The changes it suggests are intended to be applied to your actual code. 