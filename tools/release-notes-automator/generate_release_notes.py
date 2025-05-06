import requests
from datetime import datetime
import os

# List of GitHub repositories to pull release notes from.
# Format: "owner/repo"
REPOS = [
    "microsoft/azure_arc"
]

# Static filter values for GitHub API queries
LABELS = ["Issue-Addressed", "Bug-Issue"]  # Add more labels as needed
MILESTONE_TITLE = datetime.now().strftime("%B %Y")  # Current month/year as milestone title, e.g., "April 2025"

# Optional: Add GitHub token for higher rate limits.
# You can set the token via the GITHUB_TOKEN environment variable.
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

# Mapping of label keywords to human-readable category headers for release notes
CATEGORY_LABELS = {
    "ArcBox": "Jumpstart ArcBox",
    "HCIBox": "Jumpstart HCIBox",
    "Agora": "Jumpstart Agora"
}

def safe_github_request(*args, **kwargs):
    """
    Wrapper for requests.get that handles GitHub rate limiting gracefully.
    Prints a clear error if rate limit is exceeded.
    """
    try:
        response = requests.get(*args, **kwargs)
        response.raise_for_status()
        return response
    except requests.exceptions.HTTPError as e:
        # If rate limit is exceeded, print a helpful message and exit
        if hasattr(e.response, "status_code") and e.response.status_code == 403 and "rate limit" in e.response.text.lower():
            print("\033[91mERROR: GitHub API rate limit exceeded. Please set a GITHUB_TOKEN environment variable for higher limits.\033[0m")
            print("See: https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting")
            exit(1)
        raise

def get_repo_milestone_number(repo, title):
    """
    Fetch the milestone number for a given repo and milestone title.
    Returns the milestone number if found, else None.
    """
    url = f"https://api.github.com/repos/{repo}/milestones"
    response = safe_github_request(url, headers=HEADERS)
    for milestone in response.json():
        if milestone["title"] == title:
            return milestone["number"]
    return None

def get_closed_issues(repo, milestone_number):
    """
    Retrieve all closed issues for a given repo and milestone number,
    filtered by the static labels. Handles pagination.
    Returns a list of issue objects.
    """
    issues = []
    page = 1
    labels_param = ",".join(LABELS)
    while True:
        url = f"https://api.github.com/repos/{repo}/issues"
        params = {
            "state": "closed",
            "milestone": milestone_number,
            "labels": labels_param,
            "per_page": 100,
            "page": page
        }
        response = safe_github_request(url, headers=HEADERS, params=params)
        data = response.json()
        if not data:
            break
        # Ensure all labels are present (GitHub API 'labels' param is AND for issues, but double-check)
        for issue in data:
            if all(label in [lbl["name"] for lbl in issue.get("labels", [])] for label in LABELS):
                issues.append(issue)
        page += 1
    return issues

def has_linked_pr(repo, issue_number):
    """
    Check if a given issue has a linked pull request.
    Looks for 'connected' events without a commit_id (indicating a PR link).
    Returns True if a linked PR is found, else False.
    """
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/events"
    response = safe_github_request(url, headers=HEADERS)
    events = response.json()
    for event in events:
        if event["event"] == "connected" and event.get("commit_id") is None:
            # "connected" event with no commit_id = likely a PR, not a commit link
            return True
    return False

def format_issue(issue):
    """
    Format an issue as a Markdown list item with a link.
    Example: - [Issue title #123](https://github.com/owner/repo/issues/123)
    """
    title = issue["title"].strip()
    number = issue["number"]
    url = issue["html_url"]
    return f"- [{title} #{number}]({url})"

def get_all_closed_issues(repo):
    """
    Retrieve all closed issues for a given repo, regardless of milestone or label.
    Used to find issues that are not included in the release notes.
    """
    issues = []
    page = 1
    while True:
        url = f"https://api.github.com/repos/{repo}/issues"
        params = {
            "state": "closed",
            "per_page": 100,
            "page": page
        }
        response = safe_github_request(url, headers=HEADERS, params=params)
        data = response.json()
        if not data:
            break
        issues.extend(data)
        page += 1
    return issues

def categorize_issue(issue):
    """
    Returns the category header for the issue based on its labels.
    If no category label is found, returns None.
    """
    issue_labels = [lbl["name"] for lbl in issue.get("labels", [])]
    for label, header in CATEGORY_LABELS.items():
        if label in issue_labels:
            return header
    return None

def get_closed_prs(repo, milestone_number):
    """
    Retrieve all closed PRs for a given repo and milestone number,
    filtered by the 'Release-Candidate' label. Handles pagination.
    Only returns PRs that are:
      - Closed and merged
      - Not linked to any issue
      - Belong to the current milestone
      - Have the "Release-Candidate" label
    """
    prs = []
    page = 1
    while True:
        url = f"https://api.github.com/repos/{repo}/pulls"
        params = {
            "state": "closed",
            "per_page": 100,
            "page": page
        }
        response = safe_github_request(url, headers=HEADERS, params=params)
        data = response.json()
        if not data:
            break
        for pr in data:
            # Only consider PRs that are closed and merged
            if pr.get("state") != "closed" or not pr.get("merged_at"):
                continue
            # Must have milestone and match the current milestone number
            pr_milestone = pr.get("milestone")
            if not pr_milestone or pr_milestone.get("number") != milestone_number:
                continue
            # Must have the "Release-Candidate" label
            pr_labels = [lbl["name"] for lbl in pr.get("labels", [])]
            if "Release-Candidate" not in pr_labels:
                continue
            # Check for linked issues via timeline events
            pr_number = pr["number"]
            events_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/events"
            events_resp = safe_github_request(events_url, headers=HEADERS)
            events = events_resp.json()
            linked_issue = any(
                e["event"] == "connected" and e.get("commit_id") is None and e.get("source", {}).get("type") == "issue"
                for e in events
            )
            if not linked_issue:
                prs.append(pr)
        page += 1
    return prs

def format_pr(pr):
    """
    Format a PR as a Markdown list item with a link.
    Example: - [PR title #123](https://github.com/owner/repo/pull/123)
    """
    title = pr["title"].strip()
    number = pr["number"]
    url = pr["html_url"]
    return f"- [PR: {title} #{number}]({url})"

def main():
    """
    Main function to generate release notes for the current milestone.
    Prints the formatted release notes and a summary.
    Also lists issues not included in the release notes, with reasons.
    """
    # ANSI color codes for pretty console output
    COLOR_RESET = "\033[0m"
    COLOR_GREEN = "\033[92m"
    COLOR_YELLOW = "\033[93m"
    COLOR_RED = "\033[91m"
    COLOR_CYAN = "\033[96m"
    COLOR_BOLD = "\033[1m"

    # Initialize log and output containers
    log_lines = []  # Collect log output (without color codes)

    month_heading = f"## {MILESTONE_TITLE}\n"
    output_lines = [f"\033[1m## {MILESTONE_TITLE}\033[0m\n"]  # colored for console
    log_output_lines = [month_heading]  # plain for log file
    total_issues = 0
    total_prs = 0  # <-- FIX: Initialize total_prs before use
    excluded_issues = []  # List of (issue, [reasons]) tuples

    # For categorized markdown output
    categorized_issues = {header: [] for header in CATEGORY_LABELS.values()}
    uncategorized_issues = []
    categorized_prs = []  # For PRs matching the new criteria

    print(f"\033[96m🔎 Generating release notes for: \033[1m{MILESTONE_TITLE}\033[0m\n")
    log_lines.append(f"🔎 Generating release notes for: {MILESTONE_TITLE}\n")

    # Remove per-repo "✅ {issue_count} issues added." output and log
    for repo in REPOS:
        print(f"\033[96m➡️  Checking `{repo}`...\033[0m")
        log_lines.append(f"➡️  Checking `{repo}`...")
        milestone_number = get_repo_milestone_number(repo, MILESTONE_TITLE)
        if not milestone_number:
            print(f"\033[93m   ⚠️  No milestone '{MILESTONE_TITLE}' found.\033[0m")
            log_lines.append(f"   ⚠️  No milestone '{MILESTONE_TITLE}' found.")
            continue

        # Get all closed issues for this repo (for summary)
        all_closed_issues = get_all_closed_issues(repo)
        included_issues = get_closed_issues(repo, milestone_number)
        included_issue_numbers = set(issue["number"] for issue in included_issues)

        issue_count = 0
        for issue in included_issues:
            reasons = []
            if "pull_request" in issue:
                reasons.append("Is a pull request, not an issue")
            if not has_linked_pr(repo, issue["number"]):
                reasons.append("No linked pull request")
            if reasons:
                excluded_issues.append((issue, reasons))
                continue
            # Categorize for markdown output
            category = categorize_issue(issue)
            formatted = format_issue(issue)
            if category:
                categorized_issues[category].append(formatted)
            else:
                uncategorized_issues.append(formatted)
            output_lines.append(formatted)
            log_output_lines.append(formatted)
            issue_count += 1
        total_issues += issue_count

        # Find other closed issues not included in the release notes
        for issue in all_closed_issues:
            # Skip PRs
            if "pull_request" in issue:
                continue
            # Already processed above
            if issue["number"] in included_issue_numbers:
                continue
            reasons = []
            if not issue.get("milestone"):
                reasons.append("Issue does not have a milestone")
            elif issue.get("milestone", {}).get("title") != MILESTONE_TITLE:
                reasons.append(f"Issue milestone is '{issue['milestone']['title']}', not '{MILESTONE_TITLE}'")
            missing_labels = [label for label in LABELS if label not in [lbl["name"] for lbl in issue.get("labels", [])]]
            if missing_labels:
                reasons.append(f"Issue does not have label(s): {', '.join(missing_labels)}")
            if not has_linked_pr(repo, issue["number"]):
                reasons.append("No linked pull request")
            if not reasons:
                reasons.append("Unknown exclusion reason")
            excluded_issues.append((issue, reasons))

        # PRs: Only "Release-Candidate" label, current milestone, not linked to any issue
        closed_prs = get_closed_prs(repo, milestone_number)
        for pr in closed_prs:
            categorized_prs.append(format_pr(pr))
        total_prs += len(closed_prs)

    # Output categorized release notes to console and log
    print(f"\n{COLOR_BOLD}📝 Release Notes Output (by Category):{COLOR_RESET}\n")
    log_lines.append("\n📝 Release Notes Output (by Category):\n")
    print(f"# Release Notes\n")
    log_lines.append("# Release Notes\n")
    print(f"## {MILESTONE_TITLE}\n")
    log_lines.append(f"## {MILESTONE_TITLE}\n")
    for header in CATEGORY_LABELS.values():
        print(f"### {header}\n")
        log_lines.append(f"### {header}\n")
        if categorized_issues[header]:
            for line in categorized_issues[header]:
                print(line)
                log_lines.append(line)
        else:
            print("_No issues in this category._")
            log_lines.append("_No issues in this category._")
        print()
        log_lines.append("")
    print("### Uncategorized\n")
    log_lines.append("### Uncategorized\n")
    if uncategorized_issues:
        for line in uncategorized_issues:
            print(line)
            log_lines.append(line)
    else:
        print("_No issues in this category._")
        log_lines.append("_No issues in this category._")
    print()
    log_lines.append("")

    # Add PRs section to both output and log
    print("### Release Candidate Pull Requests with no linked issue\n")
    log_lines.append("### Release Candidate Pull Requests with no linked issue\n")
    if categorized_prs:
        for line in categorized_prs:
            print(line)
            log_lines.append(line)
    else:
        print("_No PRs in this category._")
        log_lines.append("_No PRs in this category._")
    print()
    log_lines.append("")

    # Output summary
    print(f"\n{COLOR_BOLD}📊 Summary:{COLOR_RESET}")
    print(f"   {COLOR_GREEN}🐞 Total issues added: {total_issues}{COLOR_RESET}")
    print(f"   {COLOR_GREEN}🔀 Total PRs added: {total_prs}{COLOR_RESET}")
    log_lines.append("\n📊 Summary:")
    log_lines.append(f"   🐞 Total issues added: {total_issues}")
    log_lines.append(f"   🔀 Total PRs added: {total_prs}")
    if total_issues > 0 or total_prs > 0:
        print(f"   {COLOR_GREEN}🚀 Release notes generated successfully!{COLOR_RESET}")
        log_lines.append("   🚀 Release notes generated successfully!")
    else:
        print(f"   {COLOR_YELLOW}⚠️  No matching issues or PRs found for this milestone.{COLOR_RESET}")
        log_lines.append("   ⚠️  No matching issues or PRs found for this milestone.")

    # Output excluded issues summary (regression fix: always show this)
    if excluded_issues:
        print(f"\n{COLOR_YELLOW}🔎 Issues not added to release notes and ready for your review. These closed issues not included in the release notes. Reason(s) for exclusion are provided:{COLOR_RESET}\n")
        log_lines.append("\n🔎 Issues not added to release notes and ready for your review. These closed issues not included in the release notes. Reason(s) for exclusion are provided:\n")
        for issue, reasons in excluded_issues:
            print(f"   - {COLOR_BOLD}[{issue['title'].strip()} #{issue['number']}]({issue['html_url']}){COLOR_RESET} — {COLOR_RED}{'; '.join(reasons)}{COLOR_RESET}")
            log_lines.append(f"   - [{issue['title'].strip()} #{issue['number']}]({issue['html_url']}) — {'; '.join(reasons)}")
    else:
        print(f"\n{COLOR_GREEN}No excluded issues!{COLOR_RESET}")
        log_lines.append("\nNo excluded issues!")

    # Write log file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(script_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)  # <-- fix: use exist_ok instead of exist_okay
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    log_path = os.path.join(logs_dir, f"{script_name}.log")
    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write("\n".join(log_lines))
    print(f"\n\033[96m📝 Log file written to: {log_path}\033[0m")

    # Write categorized markdown to _index_dummy.md
    dummy_md_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_index_dummy.md")
    with open(dummy_md_path, "w", encoding="utf-8") as f:
        f.write(f"# Release Notes\n\n")
        f.write(f"## {MILESTONE_TITLE}\n\n")
        for header in CATEGORY_LABELS.values():
            f.write(f"### {header}\n\n")
            if categorized_issues[header]:
                for line in categorized_issues[header]:
                    f.write(f"{line}\n")
            else:
                f.write("_No issues in this category._\n")
            f.write("\n")
        f.write("### Uncategorized\n\n")
        if uncategorized_issues:
            for line in uncategorized_issues:
                f.write(f"{line}\n")
        else:
            f.write("_No issues in this category._\n")
        f.write("\n")
        f.write("### Release Candidate Pull Requests with no linked issue\n\n")
        if categorized_prs:
            for line in categorized_prs:
                f.write(f"{line}\n")
        else:
            f.write("_No PRs in this category._\n")
        f.write("\n")
    print(f"\n\033[96m📄 Categorized markdown written to: {dummy_md_path}\033[0m")

if __name__ == "__main__":
    main()
