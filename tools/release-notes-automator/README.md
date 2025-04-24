# 📝 Release Notes Automator

This tool automates the generation of categorized release notes for the current milestone from GitHub issues and pull requests.

## ✨ Features

- 🔎 Fetches closed issues and PRs from specified GitHub repositories.
- 🏷️ Filters issues by milestone and labels.
- 📂 Categorizes issues based on labels (e.g., ArcBox, HCIBox, Agora).
- 🚀 Includes "Release-Candidate" PRs not linked to any issue.
- 📄 Outputs release notes in Markdown format, grouped by category.
- 📊 Provides a summary and lists excluded issues with reasons.
- 🗂️ Writes logs and a categorized Markdown file for further use.

## ⚙️ Requirements

- 🐍 Python 3.7+
- 📦 `requests` library (`pip install requests`)
- 🔑 GitHub API token (recommended for higher rate limits)

## ▶️ Usage

1. **Set up your environment:**
   - (Optional) Set a GitHub token for higher API rate limits:
     ```sh
     export GITHUB_TOKEN=your_token_here
     ```

2. **Run the script:**
   ```sh
   python generate_release_notes.py
   ```

3. **Outputs:**
   - 🖥️ Console output with colorized summary and categorized release notes.
   - 🗒️ Log file: `tools/release-notes-automator/logs/generate_release_notes.log`
   - 📄 Markdown file: `tools/release-notes-automator/_index_dummy.md`

## 🛠️ Configuration

- **Repositories:** Edit the `REPOS` list in `generate_release_notes.py` to specify which repositories to scan.
- **Labels:** Adjust the `LABELS` list to filter issues by desired labels.
- **Categories:** Update the `CATEGORY_LABELS` mapping to change or add categories.

## ℹ️ Notes

- The script uses the current month and year as the milestone title (e.g., "April 2025").
- Only issues with all specified labels and a linked PR are included.
- Only merged PRs with the "Release-Candidate" label, not linked to any issue, are included in the PR section.

## 🛟 Troubleshooting

- If you hit GitHub API rate limits, set the `GITHUB_TOKEN` environment variable.
- Ensure your milestone titles match the format used in the script.

## 📄 License

See the main repository for license information.
