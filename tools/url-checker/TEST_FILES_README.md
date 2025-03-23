# URL Checker Test File Generator

This document provides detailed information about the `create_test_files.py` script, which generates test environments for validating the URL checker.

## Overview

The test file generator creates a realistic directory structure containing a variety of file types with different kinds of URLs (absolute, relative, valid, invalid). This allows you to thoroughly test the URL checker's ability to handle complex scenarios.

## Requirements

- Python 3.8 or higher
- Required dependencies:
  - `colorama` - For colored terminal output

```bash
pip install colorama
```

## Quick Start

```bash
# Create test files with default settings
python create_test_files.py

# Run URL checker on test files
python url_checker.py --dir=test_files

# Clean up when done
python create_test_files.py --clean
```

## Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--dir` | "test_files" | Directory where test files will be created |
| `--clean` | False | Remove existing test files before creating new ones |
| `--file-count` | 5 | Base number of files per type (actual counts vary by file type) |
| `--complexity` | 3 | Directory structure complexity level (1=simple, 5=very complex) |

## Complexity Levels

The `--complexity` parameter controls how complex and nested the directory structure will be:

- **Level 1**: Simple, flat structure with minimal nesting and few special directories
- **Level 2**: Basic structure with standard project directories and moderate nesting
- **Level 3**: Moderate complexity with deeper nesting and some special directories (default)
- **Level 4**: Complex structure with deep nesting and many special directories
- **Level 5**: Very complex with deep nesting, special characters, unusual directory names, and complex relative paths

Higher complexity levels generate more:
- Deeply nested directories (up to 5+ levels deep)
- Special directories with spaces and special characters
- Random subdirectories with varied naming conventions
- Complex relative URLs with parent directory traversal

## Generated Files & URLs

Each file type uses a template that includes:

1. **Absolute URLs**:
   - Valid URLs to common websites (GitHub, Microsoft, etc.)
   - Invalid URLs to non-existent domains/pages

2. **Relative URLs**:
   - Direct paths (`docs/guide.md`)
   - Paths with current directory notation (`./images/logo.png`)
   - Parent directory traversal (`../config/settings.json`)
   - Directory paths ending with `/`
   - Deliberately broken paths for negative testing

## Directory Structure

The generator creates a project-like structure at the base level:

## Output Features

The test file generator provides enhanced terminal output with:

- Color-coded summary information (using colorama)
- Categorized file and URL statistics
- Emoji indicators for better visibility
- Progress updates during file creation

Example terminal output:

```
================================================================================
TEST ENVIRONMENT SUMMARY
================================================================================

📁 DIRECTORY STRUCTURE:
  • Total directories: 42
  • Maximum directory depth: 5 levels
  • Special directories: 7 (with spaces, special characters, etc.)
    Examples: Directory With Spaces, mixed-CASE-directory, special_chars-&!

📄 FILE STATISTICS:
  • Total files created: 156
  • Files by type:
    - .md: 28 files
    - .html: 18 files
    - .js: 15 files
    - .py: 12 files
    - .sh: 10 files
    // ...more file types...

🔗 URL VARIATIONS:
  • Direct paths: ~62 URLs
  • Dot-prefixed paths (./): ~31 URLs
  • Parent traversal (../): ~31 URLs
  • Directory paths (ending with /): ~15 URLs
  • Invalid paths (for testing): ~15 URLs

🧪 TEST CONFIGURATION:
  • Complexity level: 3/5
  • Base file count: 5 per type

🚀 NEXT STEPS:
  • Run URL checker on test files only:
    python url_checker.py --dir=test_files
  • Clean up when done:
    python create_test_files.py --dir=test_files --clean
```

## Compatibility

The test file generator is compatible with:
- Windows, macOS, and Linux operating systems
- Both colored and non-colored terminals (using colorama for cross-platform support)
- CI/CD environments like GitHub Actions

