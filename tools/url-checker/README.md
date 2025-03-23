# URL Checker

![Version](https://img.shields.io/badge/version-1.3.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)

A robust URL validation tool that scans codebase files for links and verifies their validity. The tool handles both absolute URLs (http/https) and relative file paths across multiple file types, providing detailed reports with color-coded output.

## 📋 Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Helper Tools](#helper-tools)
- [Output Format](#output-format)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## ✨ Features

- **Comprehensive Link Validation**
  - Absolute URLs (http/https)
  - Relative file paths with smart path resolution
  - Root-relative paths (starting with `/`)
  - Image and SVG links
  - Markdown header links (`#section-name`)
  - Cross-file links with anchors

- **Multi-Language Support** - Detects URLs in over 25 file types:
  - Markdown (.md)
  - HTML (.html, .htm)
  - CSS/SCSS (.css, .scss)
  - JavaScript/TypeScript (.js, .jsx, .ts, .tsx)
  - Python (.py)
  - Shell scripts (.sh, .bash, .zsh)
  - PowerShell (.ps1, .psm1, .psd1)
  - Configuration files (.json, .yaml, .yml, .toml, .env)
  - And many more...

- **Smart Path Resolution**
  - Case-insensitive path matching
  - Directory index detection (_index.md, README.md)
  - Parent directory traversal
  - Special character handling

- **Detailed Reporting**
  - Color-coded console output
  - Categorized link results
  - Comprehensive log files
  - Runtime performance metrics

## 🧰 Requirements

- Python 3.8 or higher
- Required packages:
  - `requests` - For HTTP requests
  - `colorama` - For colored terminal output

```bash
pip install requests colorama
```

## 🚀 Installation

Clone the repository or download the URL checker tool:

```bash
git clone https://github.com/username/jumpstart-sdk.git
cd jumpstart-sdk/tools/url-checker
```

## 💻 Basic Usage

Run the URL checker from the repository root to scan all supported files:

```bash
python tools/url-checker/url_checker.py
```

### Command Line Options

```bash
# Check files in a specific directory
python url_checker.py --dir=docs

# Use a custom timeout for HTTP requests
python url_checker.py --timeout=30
```

## 🛠️ Helper Tools

The URL checker comes with two companion tools to help with testing and visualization:

### 1. Test File Generator (`create_test_files.py`)

Creates a realistic directory structure with various file types containing different kinds of URLs for testing purposes.

```bash
# Create test files with default settings
python create_test_files.py

# Create a more complex test environment
python create_test_files.py --complexity=5 --file-count=10

# Clean up test files when done
python create_test_files.py --clean
```

Options:
- `--dir=NAME` - Directory where test files will be created (default: "test_files")
- `--clean` - Remove existing test files instead of creating new ones
- `--file-count=N` - Base number of files per type (default: 5)
- `--complexity=N` - Directory structure complexity level 1-5 (default: 3)

### 2. Output Simulator (`simulate_output.py`)

Demonstrates what the URL checker's output will look like without actually checking any URLs.

```bash
python simulate_output.py
```

This is useful for:
- Testing the formatting and appearance of output
- Demonstrating the tool to others
- Testing terminal color compatibility

## 📊 Output Format

The URL checker provides categorized output in both the console and log files:

### Console Output Example

```
═════════════════════════════════════════════════════════
📊  LINK VALIDATION SUMMARY (156 links checked)
═════════════════════════════════════════════════════════

❌  BROKEN LINKS: 8
   • Absolute URLs: 3
   • Relative URLs without anchors: 2
   • Relative URLs with anchors: 1
   • Image URLs: 2

📭  NO LINKS FOUND: 1
   • SVG URLs

🔍  CATEGORIES WITH NO BROKEN LINKS: 2
   • Root-relative URLs: 10 OK links
   • Header links: 7 OK links

✅  OK LINKS: 148

⏱️  RUNTIME: 3.70 minutes (0:03:42)

📄 FULL LOGS: logs/broken_urls_2023-10-20_15-30-45.log

❌  Broken links were found. Check the logs for details.
```

### Log Files

Detailed logs are saved to the `logs` directory with timestamps, containing:

- Full details of all checked URLs
- Status codes for broken absolute URLs
- File paths for broken relative URLs
- Categorized summaries
- Runtime statistics

## ⚙️ Configuration

### Known Valid Domains

Add domains that should be considered valid without checking:

```python
# In url_checker.py
KNOWN_VALID_DOMAINS = [
    "learn.microsoft.com",
    "icanhazip.com",
    # Add more domains to skip
]
```

### Timeout Settings

Adjust the HTTP request timeout:

```python
# In url_checker.py
TIMEOUT = 15  # Timeout in seconds
```

Or use the command-line option:

```bash
python url_checker.py --timeout=30
```

### File Extensions

Modify the `SUPPORTED_FILE_TYPES` dictionary to control which file types are checked.

## 🔍 Troubleshooting

### Timeout Issues

If you encounter many timeout errors:
1. Increase the timeout value: `--timeout=30`
2. Add problematic domains to `KNOWN_VALID_DOMAINS`

### False Positives

Some URLs may be incorrectly marked as broken due to:
- Server-side rate limiting
- Temporary server issues
- Authentication requirements

For trusted domains that may have connectivity issues, add them to `KNOWN_VALID_DOMAINS`.

### Relative Path Issues

If relative URLs are incorrectly reported as broken:
1. Check case sensitivity (important on Linux/macOS)
2. Verify directory separators (`/` not `\`)
3. Check parent directory traversal notation (`../`)

## 🔄 Testing Workflow

A typical testing workflow using the helper tools:

1. Generate test files: `python create_test_files.py`
2. Check only those files: `python url_checker.py --dir=test_files`
3. Clean up when finished: `python create_test_files.py --clean`

## 📋 Exit Codes

The URL checker returns the following exit codes:

- `0` - All URLs are valid (no broken links found)
- `1` - At least one broken link was found

This makes the tool suitable for use in CI/CD pipelines where you might want to fail a build when broken links are detected.
