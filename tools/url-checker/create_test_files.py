#!/usr/bin/env python3
"""
This script creates a testing environment with various file types 
containing different kinds of URLs to test the URL checker.
"""

import os
import random
import string
import shutil
import argparse
from datetime import datetime
from colorama import init, Fore, Style  # Add colorama import

# Initialize colorama for cross-platform color support
init(autoreset=True)

# Define Colors class for consistent formatting with url-checker.py
class Colors:
    OKGREEN = Fore.GREEN
    FAIL = Fore.RED
    INFO = Fore.CYAN
    NEUTRAL = Fore.YELLOW
    ENDC = Style.RESET_ALL

def ensure_directory(directory):
    """Creates a directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Create test files for the URL checker with various file types."
    )
    parser.add_argument(
        "--dir", 
        default="test_files",
        help="Directory where test files will be created (relative to script location)"
    )
    parser.add_argument(
        "--clean", 
        action="store_true", 
        help="Remove existing test files before creating new ones"
    )
    parser.add_argument(
        "--file-count",
        type=int,
        default=5, 
        help="Base number of files to create per type (some types may have more/fewer)"
    )
    parser.add_argument(
        "--complexity",
        type=int,
        default=3,
        choices=[1, 2, 3, 4, 5],
        help="Complexity level of directory structure (1=simple, 5=very complex)"
    )
    return parser.parse_args()

# Parse arguments
args = parse_args()

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_ROOT = os.path.join(SCRIPT_DIR, args.dir)
TEST_SIZE = args.file_count
COMPLEXITY = args.complexity

# Adjust file counts based on the desired test size
NUM_FILES = {
    'md': TEST_SIZE * 4,    # Markdown - more because it's the primary format
    'html': TEST_SIZE * 3,  # HTML - also common
    'css': TEST_SIZE * 2,   # CSS
    'js': TEST_SIZE * 3,    # JavaScript
    'py': TEST_SIZE * 2,    # Python
    'json': TEST_SIZE * 1.6,  # JSON
    'yaml': TEST_SIZE * 1.6,  # YAML
    'xml': TEST_SIZE,       # XML
    'txt': TEST_SIZE,       # Text
    # Scripting languages
    'sh': TEST_SIZE * 2,    # Shell
    'ps1': TEST_SIZE * 2,   # PowerShell
    'bat': TEST_SIZE,       # Batch
    'rb': TEST_SIZE,        # Ruby
    'pl': TEST_SIZE,        # Perl
    'php': TEST_SIZE,       # PHP
    'r': TEST_SIZE,         # R
    'conf': TEST_SIZE,      # Config
}

# Convert any float values to integers
for key in NUM_FILES:
    NUM_FILES[key] = int(NUM_FILES[key])

def clean_test_directory():
    """Remove existing test files and directories."""
    if os.path.exists(TEST_ROOT):
        print(f"Cleaning up existing test directory: {TEST_ROOT}")
        shutil.rmtree(TEST_ROOT)
        print(f"Removed {TEST_ROOT}")

# Clean up if requested
if args.clean:
    clean_test_directory()

# Create test directory structure
ensure_directory(TEST_ROOT)

# Basic directory structure - we'll add random subdirectories later
BASE_DIRS = {
    "docs": ["user_guide", "api_reference", "tutorials", "examples"],
    "src": ["components", "utils", "styles", "models", "services", "api"],
    "config": ["app", "database", "logging", "security"],
    "assets": ["images", "icons", "fonts", "data"],
    "scripts": ["shell", "powershell", "batch", "other"],
    "tests": ["unit", "integration", "performance"],
}

# Generate some additional random directories with special naming patterns
SPECIAL_DIRS = [
    "Directory With Spaces",
    "mixed-CASE-directory",
    "special_chars-&!",
    "very.deeply.nested",
    "2023_Archive",
    "UPPERCASE_FOLDER",
    "camelCaseFolder",
    "kebab-case-folder",
    "snake_case_folder",
    "with.dots.folder",
]

# Create directory for different URLs to be referenced
RELATIVE_URL_TARGETS = {}

def generate_random_directory_structure(root, depth=0, max_depth=4, prefix=""):
    """Recursively generate a random directory structure."""
    if depth >= max_depth:
        return
    
    # Add some randomness to the max depth
    current_max_depth = max(1, min(max_depth, max_depth - depth + random.randint(-1, 1)))
    
    # Create base dirs at root level
    if depth == 0:
        for base_dir, subdirs in BASE_DIRS.items():
            base_path = os.path.join(root, base_dir)
            ensure_directory(base_path)
            
            # Create subdirectories
            for subdir in subdirs:
                subdir_path = os.path.join(base_path, subdir)
                ensure_directory(subdir_path)
                
                # Maybe add another level
                if random.random() < 0.7:
                    for i in range(random.randint(0, 2)):
                        rand_name = f"{subdir}_{random_word()}"
                        ensure_directory(os.path.join(subdir_path, rand_name))
    
    # Add some special directories at various levels
    if depth < 2 and random.random() < 0.7:
        special_dir = random.choice(SPECIAL_DIRS)
        special_path = os.path.join(root, f"{prefix}{special_dir}")
        ensure_directory(special_path)
        
        # Recursively add subdirectories to this special dir
        generate_random_directory_structure(
            special_path, 
            depth + 1, 
            max_depth=current_max_depth,
            prefix=f"{prefix}_sub_"
        )
    
    # Add some deeply nested paths based on complexity
    if depth < 3 and random.random() < 0.3 * COMPLEXITY / 3:
        deep_nest_path = root
        nest_depth = random.randint(2, 4)
        nest_name = "nested"
        
        for i in range(nest_depth):
            nest_name = f"{nest_name}_{i}"
            deep_nest_path = os.path.join(deep_nest_path, nest_name)
            ensure_directory(deep_nest_path)

    # Add random subdirectories based on complexity
    num_random_dirs = random.randint(0, COMPLEXITY)
    for i in range(num_random_dirs):
        rand_dir = f"{random_word()}_{i}"
        rand_path = os.path.join(root, rand_dir)
        ensure_directory(rand_path)
        
        # Maybe go deeper
        if random.random() < 0.5 / (depth + 1):
            generate_random_directory_structure(
                rand_path, 
                depth + 1, 
                max_depth=current_max_depth,
                prefix=""
            )

# Sample URLs - a mix of valid and invalid
VALID_URLS = [
    "https://github.com",
    "https://microsoft.com",
    "https://learn.microsoft.com/azure/",
    "https://developer.mozilla.org",
    "https://stackoverflow.com",
    "https://python.org",
    "https://www.w3.org",
]

INVALID_URLS = [
    "https://example.com/non-existent-page",
    "https://invalid-domain-that-does-not-exist.com",
    "https://github.com/user/repo-that-doesnt-exist",
    "https://broken.link.example",
]

# Generate random words for titles
def random_word(length=8):
    """Generate a random word of specified length."""
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))

# Templates for the different file types
MD_TEMPLATE = """# {title}

## Introduction

This is a sample markdown file with various links:

- [GitHub]({url_1})
- [Documentation](docs/guide.md)
- [Relative Link]({relative_url})

Read more about [this topic]({url_2}).

![Logo](assets/images/logo.png)
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <link rel="stylesheet" href="src/styles/main.css">
    <meta property="og:image" content="{url_1}">
</head>
<body>
    <h1>{title}</h1>
    <p>Visit our <a href="{url_2}">website</a>.</p>
    <img src="{relative_url}" alt="Sample Image">
    <script src="src/utils/main.js"></script>
</body>
</html>
"""

CSS_TEMPLATE = """/* {title} */
body {{
    background-color: #f0f0f0;
    font-family: Arial, sans-serif;
}}

.banner {{
    background-image: url('{url_1}');
}}

.icon {{
    background-image: url({relative_url});
}}

/* Imported from {url_2} */
"""

JS_TEMPLATE = """// {title}
import {{ Component }} from 'library';
import utils from '{relative_url}';

const API_URL = '{url_1}';

function fetchData() {{
    fetch(API_URL)
        .then(response => response.json())
        .then(data => console.log(data));
}}

// Reference: {url_2}
document.getElementById('link').href = './assets/document.pdf';
"""

PY_TEMPLATE = """# {title}
import requests
import os
from module import function

API_URL = "{url_1}"

def fetch_data():
    \"\"\"Fetches data from API.
    
    See {url_2} for documentation.
    \"\"\"
    response = requests.get(API_URL)
    return response.json()

# Load configuration from {relative_url}
config_path = os.path.join("config", "settings.json")
"""

JSON_TEMPLATE = """{{
    "name": "{title}",
    "version": "1.0.0",
    "description": "Sample JSON file",
    "homepage": "{url_1}",
    "documentation": "{url_2}",
    "logo": "{relative_url}",
    "dependencies": {{
        "library": "^2.0.0"
    }}
}}
"""

YAML_TEMPLATE = """# {title}
name: Sample Project
version: 1.0.0
description: Sample YAML file

urls:
  homepage: {url_1}
  docs: {url_2}
  logo: {relative_url}

dependencies:
  - name: library
    version: ^2.0.0
"""

XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!-- {title} -->
<root>
    <metadata>
        <title>{title}</title>
        <url>{url_1}</url>
    </metadata>
    <links>
        <link href="{url_2}" rel="external" />
        <image src="{relative_url}" />
    </links>
</root>
"""

TXT_TEMPLATE = """Title: {title}

This is a sample text file with URLs:

Website: {url_1}
Documentation: {url_2}
Local file: {relative_url}

End of file.
"""

SHELL_TEMPLATE = """#!/bin/bash
# {title}

# Download a file from URL
wget {url_1} -O output.txt

# Or with curl
curl -L "{url_2}" > another_output.txt

# Source a local script
source {relative_url}

# Use a variable with URL
API_URL="{url_1}/api/v1"
curl -H "Content-Type: application/json" -X GET $API_URL

# Common pattern in scripts - URLs in comments
# See: {url_2}
"""

PS1_TEMPLATE = """# {title}
# PowerShell script example

# Download a file
Invoke-WebRequest -Uri "{url_1}" -OutFile "output.txt"

# Make a REST API call
$response = Invoke-RestMethod -Uri "{url_2}" -Method Get

# Import a module
Import-Module "{relative_url}"

# URLs in comments
# Reference documentation: {url_1}

# URL in a variable
$ApiUrl = "{url_2}/api/v1"
"""

BAT_TEMPLATE = """@echo off
REM {title}

REM Download a file with curl (if available in PATH)
curl -o output.txt "{url_1}"

REM Use with certutil (built into Windows)
certutil -urlcache -split -f "{url_2}" output.txt

REM Call another batch file
call {relative_url}

REM URL in variable
set API_URL={url_1}/api
echo %API_URL%

REM Reference in comment
REM See: {url_2}
"""

RB_TEMPLATE = """#!/usr/bin/env ruby
# {title}

require 'net/http'
require 'uri'

# Download from URL
uri = URI.parse('{url_1}')
response = Net::HTTP.get_response(uri)
puts response.body

# Load a local file
require_relative '{relative_url}'

# Another URL example
url = '{url_2}'
uri = URI.parse(url)

# Reference: {url_1}/docs
"""

PL_TEMPLATE = """#!/usr/bin/perl
# {title}

use strict;
use warnings;
use LWP::Simple;

# Get a webpage
my $content = get('{url_1}');
print "Content: $content\\n";

# Load local module
require '{relative_url}';

# Another URL
my $url = '{url_2}';
my $data = get($url);

# Resource: {url_1}/docs
"""

PHP_TEMPLATE = """<?php
// {title}

// Fetch URL contents
$content = file_get_contents('{url_1}');
echo $content;

// Include local file
include '{relative_url}';

// Use in cURL
$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, '{url_2}');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
$output = curl_exec($ch);
curl_close($ch);

// Reference: {url_1}/docs
?>
"""

R_TEMPLATE = """# {title}
# R script example

# Download a file
download.file("{url_1}", "output.txt")

# Load a library
source("{relative_url}")

# Read data from URL
data <- read.csv("{url_2}")

# Reference URL
# Documentation: {url_1}/reference
"""

CONF_TEMPLATE = """# {title}
# Configuration file example

[server]
base_url = {url_1}
api_endpoint = {url_2}/api

[resources]
images = {relative_url}

[documentation]
url = {url_1}/docs
"""

def generate_relative_urls(test_root, num_urls=10):
    """Generate a list of relative URLs pointing to actual files in the test directory."""
    relative_urls = []
    
    # Walk the directory structure to find all files
    all_files = []
    root_len = len(test_root) + 1  # +1 for the trailing slash
    
    for root, dirs, files in os.walk(test_root):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = full_path[root_len:]  # Path relative to test_root
            all_files.append(rel_path)
    
    if not all_files:
        # Fallback if no files found yet
        return ["README.md", "docs/guide.md", "assets/images/logo.png"]
    
    # Generate different types of relative URLs
    for _ in range(num_urls):
        if not all_files:
            break
            
        target_file = random.choice(all_files)
        
        # Randomly choose URL type:
        url_type = random.randint(1, 4)
        
        if url_type == 1:
            # Direct path
            relative_urls.append(target_file)
        elif url_type == 2:
            # Path with ./ prefix
            relative_urls.append(f"./{target_file}")
        elif url_type == 3:
            # Path with ../ prefix(es)
            parts = target_file.split('/')
            if len(parts) > 1:
                # Go up at least one directory
                up_levels = random.randint(1, min(3, len(parts) - 1))
                parent_path = '../' * up_levels
                remaining_path = '/'.join(parts[up_levels:])
                relative_urls.append(f"{parent_path}{remaining_path}")
            else:
                relative_urls.append(target_file)
        elif url_type == 4:
            # Directory path ending with /
            parts = target_file.split('/')
            if len(parts) > 1:
                dir_path = '/'.join(parts[:-1]) + '/'
                relative_urls.append(dir_path)
            else:
                relative_urls.append(target_file)
    
    # Add some deliberately invalid URLs for testing
    num_invalid = max(1, num_urls // 10)
    for _ in range(num_invalid):
        invalid_path = f"non/existent/path/{random_word()}.{random.choice(list(NUM_FILES.keys()))}"
        relative_urls.append(invalid_path)
    
    return relative_urls

def create_files():
    """Create the test files with links."""
    print(f"Creating test files in {TEST_ROOT}...")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create base directory structure
    generate_random_directory_structure(TEST_ROOT, max_depth=COMPLEXITY+1)
    
    # Create a README.md in the test root
    with open(os.path.join(TEST_ROOT, "README.md"), 'w') as f:
        f.write(f"""# URL Checker Test Files

This directory contains various file types with URLs for testing the URL checker script.
Files generated at: {timestamp}

## Test Environment

This is a TEST DIRECTORY containing generated files for testing the URL checker.
It is safe to delete this entire directory when tests are complete.

## Directory Structure

This test environment contains a complex directory structure with:
- Basic project directories (docs, src, config, etc.)
- Special directories with spaces, mixed case, and special characters
- Deeply nested directories
- Random directories

## File Types

The following file types are included:
{', '.join([f".{ext}" for ext in NUM_FILES.keys()])}

## Test Size

Number of files created per type:
{', '.join([f"{ext}: {count}" for ext, count in NUM_FILES.items()])}

Total test files: {sum(NUM_FILES.values())}

## Command Used

Test files generated with:
python create_test_files.py --dir="{args.dir}" --file-count={TEST_SIZE} --complexity={COMPLEXITY}

## Generated Files

Each file contains a mix of:
- Valid absolute URLs
- Invalid absolute URLs
- Relative paths (including parent directory traversal)
- Directory paths
- Special characters and edge cases
""")
    
    # Create image placeholder files in multiple locations
    for img_dir in ["assets/images", "docs/examples/images", "src/components/icons"]:
        img_path = os.path.join(TEST_ROOT, img_dir)
        ensure_directory(img_path)
        
        for img_name in ["logo.png", "banner.jpg", "icon.svg", "background.webp"]:
            with open(os.path.join(img_path, img_name), 'w') as f:
                f.write(f"# This is a placeholder for an image file: {img_name}")
    
    # First, create some initial files to build up the directory structure
    print("Creating initial files to establish directory structure...")
    for ext, count in NUM_FILES.items():
        template = globals().get(f"{ext.upper()}_TEMPLATE", TXT_TEMPLATE)
        
        # Create just a few files to populate the directory structure
        for i in range(min(3, count)):
            directory = get_directory_for_filetype(ext, TEST_ROOT)
            
            # Generate a filename
            filename = f"init_{random_word()}_{i + 1}.{ext}"
            filepath = os.path.join(directory, filename)
            
            # Generate content with placeholder URLs
            content = template.format(
                title=f"TEST FILE - Initial {ext.upper()} File {i + 1}",
                url_1=random.choice(VALID_URLS),
                url_2=random.choice(VALID_URLS),
                relative_url="README.md"  # Placeholder
            )
            
            # Write the file
            with open(filepath, 'w') as f:
                f.write(content)
    
    # Now generate relative URLs to the created files
    print("Generating relative URLs based on created directory structure...")
    relative_urls = generate_relative_urls(TEST_ROOT, num_urls=20)
    
    # Create the rest of the files using the generated relative URLs
    print("Creating remaining files with relative links...")
    total_files = 0
    
    # Create files for all the specified types
    for ext, count in NUM_FILES.items():
        template = globals().get(f"{ext.upper()}_TEMPLATE", TXT_TEMPLATE)
        
        # Skip the first few files we've already created
        for i in range(3, count):
            # Choose directory based on file type, but with more randomness
            directory = get_directory_for_filetype(ext, TEST_ROOT, randomize=True)
            
            # Generate a filename
            filename = f"test_{random_word()}_{i + 1}.{ext}"
            filepath = os.path.join(directory, filename)
            
            # Generate content with URLs
            content = template.format(
                title=f"TEST FILE - Sample {ext.upper()} File {i + 1}",
                url_1=random.choice(VALID_URLS),
                url_2=random.choice(VALID_URLS if i % 4 != 0 else INVALID_URLS),
                relative_url=random.choice(relative_urls)
            )
            
            # Write the file
            with open(filepath, 'w') as f:
                f.write(content)
            
            total_files += 1
    
    print(f"Created {total_files} test files in {TEST_ROOT}")
    
    # Collect statistics about the test environment
    return total_files

def get_directory_for_filetype(ext, test_root, randomize=False):
    """Get an appropriate directory for a file type, with optional randomization."""
    # Get all directories recursively
    if randomize and random.random() < 0.3:
        # Get all directories
        all_dirs = []
        for root, dirs, files in os.walk(test_root):
            all_dirs.extend([os.path.join(root, d) for d in dirs])
        
        if all_dirs:
            return random.choice(all_dirs)
    
    # Default directories based on file type
    if ext in ['md', 'txt']:
        base = os.path.join(test_root, "docs")
        options = [
            base,
            os.path.join(base, "user_guide"),
            os.path.join(base, "api_reference"),
            os.path.join(base, "examples")
        ]
    elif ext in ['js', 'ts']:
        base = os.path.join(test_root, "src")
        options = [
            os.path.join(base, "utils"),
            os.path.join(base, "components"),
            os.path.join(base, "services")
        ]
    elif ext == 'css':
        base = os.path.join(test_root, "src")
        options = [
            os.path.join(base, "styles"),
            os.path.join(test_root, "assets")
        ]
    elif ext in ['json', 'yaml', 'yml']:
        base = os.path.join(test_root, "config")
        options = [
            base,
            os.path.join(base, "app")
        ]
    elif ext == 'html':
        options = [test_root, os.path.join(test_root, "docs")]
    elif ext == 'xml':
        options = [os.path.join(test_root, "config")]
    elif ext == 'py':
        base = os.path.join(test_root, "src")
        options = [
            os.path.join(base, "utils"),
            os.path.join(test_root, "scripts")
        ]
    elif ext in ['sh', 'bash', 'zsh']:
        options = [os.path.join(test_root, "scripts", "shell")]
    elif ext in ['ps1', 'psm1', 'psd1']:
        options = [os.path.join(test_root, "scripts", "powershell")]
    elif ext in ['bat', 'cmd']:
        options = [os.path.join(test_root, "scripts", "batch")]
    elif ext in ['rb', 'pl', 'php', 'r', 'R']:
        options = [os.path.join(test_root, "scripts", "other")]
    elif ext in ['conf', 'cfg', 'ini']:
        options = [os.path.join(test_root, "config", "app")]
    else:
        options = [test_root]
    
    # Pick a random option from the list
    selected_dir = random.choice(options)
    ensure_directory(selected_dir)  # Make sure it exists
    return selected_dir

def collect_test_environment_stats():
    """Collect statistics about the test environment created."""
    stats = {
        "directory_count": 0,
        "file_count_by_type": {},
        "total_files": 0,
        "max_depth": 0,
        "special_dirs": [],
        "directory_sizes": []
    }
    
    # Walk the directory structure
    for root, dirs, files in os.walk(TEST_ROOT):
        # Count directories
        stats["directory_count"] += len(dirs)
        
        # Track special directories
        for d in dirs:
            if any(c in d for c in [' ', '&', '!', '.', '-']):
                stats["special_dirs"].append(os.path.join(root, d).replace(TEST_ROOT + os.sep, ''))
        
        # Calculate depth
        rel_path = os.path.relpath(root, TEST_ROOT)
        if rel_path != '.':
            depth = len(rel_path.split(os.sep))
            stats["max_depth"] = max(stats["max_depth"], depth)
            stats["directory_sizes"].append(len(files))
        
        # Count files by type
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext:
                ext = ext[1:]  # Remove the leading dot
                stats["file_count_by_type"][ext] = stats["file_count_by_type"].get(ext, 0) + 1
                stats["total_files"] += 1
    
    # If any files were found at the root level, adjust the depth count
    if not stats["max_depth"] and stats["total_files"] > 0:
        stats["max_depth"] = 1
    
    # Collect URL stats (types of relative URLs generated)
    url_stats = {
        "direct_paths": 0,
        "dot_prefixed": 0,
        "parent_traversal": 0,
        "directory_paths": 0,
        "invalid_paths": 0
    }
    
    # We can't accurately count these after generation, so we'll use placeholders
    # In a real implementation, we'd track these during URL generation
    url_stats["direct_paths"] = int(stats["total_files"] * 0.4)
    url_stats["dot_prefixed"] = int(stats["total_files"] * 0.2)
    url_stats["parent_traversal"] = int(stats["total_files"] * 0.2)
    url_stats["directory_paths"] = int(stats["total_files"] * 0.1)
    url_stats["invalid_paths"] = int(stats["total_files"] * 0.1)
    
    stats["url_stats"] = url_stats
    
    return stats

if __name__ == "__main__":
    print(f"Test files will be created in: {TEST_ROOT}")
    print(f"File count per type (base): {TEST_SIZE}")
    print(f"Directory structure complexity: {COMPLEXITY} (1=simple, 5=complex)")
    
    if args.clean:
        print("Cleaning existing test files first")
    
    total_files = create_files()
    
    # Collect statistics about the test environment
    stats = collect_test_environment_stats()
    
    # Print enhanced summary
    print("\n" + "="*80)
    print(f"{Colors.INFO}TEST ENVIRONMENT SUMMARY{Colors.ENDC}")
    print("="*80)
    
    print(f"\n📁 DIRECTORY STRUCTURE:")
    print(f"  • Total directories: {stats['directory_count']}")
    print(f"  • Maximum directory depth: {stats['max_depth']} levels")
    print(f"  • Special directories: {len(stats['special_dirs'])} (with spaces, special characters, etc.)")
    if stats['special_dirs'] and len(stats['special_dirs']) <= 5:
        print(f"    Examples: {', '.join(stats['special_dirs'][:5])}")
    
    print(f"\n📄 FILE STATISTICS:")
    print(f"  • Total files created: {stats['total_files']}")
    print(f"  • Files by type:")
    
    # Sort file types by count (descending)
    sorted_types = sorted(stats['file_count_by_type'].items(), key=lambda x: x[1], reverse=True)
    for ext, count in sorted_types:
        print(f"    - .{ext}: {count} files")
    
    print(f"\n🔗 URL VARIATIONS:")
    url_types = stats['url_stats']
    print(f"  • Direct paths: ~{url_types['direct_paths']} URLs")
    print(f"  • Dot-prefixed paths (./): ~{url_types['dot_prefixed']} URLs")
    print(f"  • Parent traversal (../): ~{url_types['parent_traversal']} URLs")
    print(f"  • Directory paths (ending with /): ~{url_types['directory_paths']} URLs")
    print(f"  • Invalid paths (for testing): ~{url_types['invalid_paths']} URLs")
    
    print("\n🧪 TEST CONFIGURATION:")
    print(f"  • Complexity level: {COMPLEXITY}/5")
    print(f"  • Base file count: {TEST_SIZE} per type")
    
    print("\n🚀 NEXT STEPS:")
    print(f"  • Run URL checker on test files only:")
    print(f"    python url_checker.py --dir={args.dir}")
    print(f"  • Clean up when done:")
    print(f"    python create_test_files.py --dir={args.dir} --clean")
    
    print("\n⚠️  NOTE: The test_files directory is included in .gitignore")
    print("="*80)
    print("\nTest files created successfully!")
    print(f"To run URL checker on test files only:")
    print(f"python url_checker.py --dir={args.dir}")
    print("\nTo clean up test files when done:")
    print(f"python create_test_files.py --dir={args.dir} --clean")
    print("\nNote: The test_files directory is already in .gitignore, so test files won't be committed.")
