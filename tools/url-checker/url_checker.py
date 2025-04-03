# =============================================================================
# URL Checker for Markdown Files
# =============================================================================
# This script scans all Markdown files in a repository for URLs and checks
# whether they are valid. It handles both absolute URLs (http/https) and
# relative file paths, providing a detailed report of broken links.
# =============================================================================

import os
import re
import requests
import subprocess
from urllib.parse import urljoin, urlparse
from datetime import datetime
import ipaddress
from colorama import init
import sys
import argparse

# Initialize colorama for Windows compatibility and force color output in GitHub Actions
init(strip=False, convert=False)

# =============================================================================
# CONFIGURATION
# =============================================================================

# ANSI color codes for terminal output
class Colors:
    OKGREEN = '\033[92m'  # Green for success
    FAIL = '\033[91m'     # Red for errors
    INFO = '\033[96m'     # Cyan for neutral/informational
    NEUTRAL = '\033[93m'  # Yellow for "no links found" category
    SPECIAL = '\033[95m'  # Magenta for "categories with no broken links"
    ENDC = '\033[0m'

def get_repo_root():
    """Find the root directory of the Git repository."""
    try:
        return subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip()
    except subprocess.CalledProcessError:
        return '.'  # Default to current directory if not in a Git repo

# Script configuration settings
REPO_PATH = get_repo_root()
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, 'logs')

# Create logs directory and handle any errors gracefully
try:
    os.makedirs(LOG_DIR, exist_ok=True)
    print(f"Logs will be saved to: {LOG_DIR}")
except Exception as e:
    print(f"Warning: Could not create logs directory: {e}")
    LOG_DIR = SCRIPT_DIR  # Fallback to script directory
    print(f"Using fallback log directory: {LOG_DIR}")

TIMEOUT = 15  # Request timeout in seconds - increase this if you get many timeout errors
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; LinkChecker/1.0)"}  # Browser-like user agent

# File types to check - maps extensions to descriptive names
SUPPORTED_FILE_TYPES = {
    # Existing file types
    '.md': 'Markdown',
    '.html': 'HTML',
    '.htm': 'HTML',
    '.js': 'JavaScript',
    '.jsx': 'React',
    '.ts': 'TypeScript',
    '.tsx': 'React TypeScript',
    '.py': 'Python',
    '.css': 'CSS',
    '.scss': 'SCSS',
    '.json': 'JSON',
    '.yaml': 'YAML',
    '.yml': 'YAML',
    '.xml': 'XML',
    '.cs': 'C#',
    '.java': 'Java',
    '.txt': 'Text',
    '.rst': 'reStructuredText',
    
    # Shell/Bash scripting
    '.sh': 'Shell',
    '.bash': 'Bash',
    '.zsh': 'ZShell',
    '.ksh': 'KornShell',
    
    # PowerShell
    '.ps1': 'PowerShell',
    '.psm1': 'PowerShell Module',
    '.psd1': 'PowerShell Data',
    
    # Windows batch/command
    '.bat': 'Batch',
    '.cmd': 'Command',
    
    # Other scripting languages
    '.pl': 'Perl',
    '.pm': 'Perl Module',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.r': 'R',
    '.R': 'R',
    '.lua': 'Lua',
    '.tcl': 'Tcl',
    '.groovy': 'Groovy',
    '.awk': 'Awk',
    '.sed': 'Sed',
    
    # Configuration files
    '.ini': 'INI',
    '.conf': 'Config',
    '.cfg': 'Config',
    '.toml': 'TOML',
    '.env': 'Environment',
}

# Regular expressions for URL detection and processing
# Markdown link pattern
MD_URL_REGEX = re.compile(r'\[.*?\]\((.*?)\)')  # Finds markdown links: [text](url)

# HTML link patterns
HTML_HREF_REGEX = re.compile(r'<a[^>]+href=["\'](.*?)["\']', re.IGNORECASE)
HTML_SRC_REGEX = re.compile(r'<(?:img|script|iframe)[^>]+src=["\'](.*?)["\']', re.IGNORECASE)
HTML_LINK_HREF_REGEX = re.compile(r'<link[^>]+href=["\'](.*?)["\']', re.IGNORECASE)
HTML_META_CONTENT_REGEX = re.compile(r'<meta[^>]+content=["\'](.*?)["\']', re.IGNORECASE)

# CSS url() pattern
CSS_URL_REGEX = re.compile(r'url\(["\']?(.*?)["\']?\)', re.IGNORECASE)

# JavaScript/TypeScript URL patterns
JS_URL_REGEX = re.compile(r'(?:(?:\'|")(?:https?://|/|\.\.?/)[^\s\'">]+(?:\'|")|import\s+(?:.+from\s+)?[\'"]([^\'"]+)[\'"])')

# Python URL patterns
PY_URL_REGEX = re.compile(r'(?:\'|")((?:https?://|/|\.\.?/)[^\s\'"]+)(?:\'|")')
PY_IMPORT_REGEX = re.compile(r'(?:from|import)\s+([a-zA-Z0-9_.]+)')

# JSON/YAML URL patterns
JSON_URL_REGEX = re.compile(r'(?:\'|")((?:https?://|/|\.\.?/)[^\s\'"]+)(?:\'|")')

# XML URL patterns
XML_URL_REGEX = re.compile(r'(?:href|src|url)=["\'](.*?)["\']', re.IGNORECASE)

# Shell/Bash URL patterns - matches URLs in quotes, wget/curl commands, etc.
SHELL_URL_REGEX = re.compile(r'(?:(?:\'|")((?:https?://|/|\.\.?/)[^\s\'"]+)(?:\'|")|(?:wget|curl)\s+(?:-[a-zA-Z]+\s+)*(?:\'|")?([^\s\'"]+)(?:\'|")?)')

# PowerShell URL patterns - matches URLs in quotes, as parameters, etc.
PS_URL_REGEX = re.compile(r'(?:(?:\'|")((?:https?://|/|\.\.?/)[^\s\'"]+)(?:\'|")|(?:Invoke-WebRequest|Invoke-RestMethod)\s+(?:-[a-zA-Z]+\s+)*(?:\'|")?([^\s\'"]+)(?:\'|")?)')

# Batch/CMD URL patterns
BATCH_URL_REGEX = re.compile(r'(?:(?:https?://|/|\.\.?/)[^\s\'"]+)')

# Perl/Ruby patterns (similar to Python)
SCRIPT_URL_REGEX = re.compile(r'(?:\'|")((?:https?://|/|\.\.?/)[^\s\'"]+)(?:\'|")')

# Config file patterns (ini, env, etc.) - looks for URLs after = or : characters
CONFIG_URL_REGEX = re.compile(r'(?:=|:)\s*[\'"]?((?:https?://|/|\.\.?/)[^\s\'"]+)[\'"]?')

EMAIL_REGEX = re.compile(r'^mailto:')  # Detects email links
ANSI_ESCAPE_REGEX = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')  # For stripping color codes
HEADER_LINK_REGEX = re.compile(r'#[-\w]+$')  # Matches markdown header links like #header-name

# URLs to skip checking - add frequently timing out domains here
KNOWN_VALID_DOMAINS = [
    "learn.microsoft.com",
    "whatismyip.com",
    "www.linkedin.com",
    "linkedin.com",
    "icanhazip.com",
    "shell.azure.com",
    "aka.ms",               # Microsoft's URL shortener
    "go.microsoft.com",     # Another Microsoft URL shortener
    "api.fabric.microsoft.com",  # Microsoft Fabric API
    "dashboards.kusto.windows.net", # Microsoft Kusto dashboards
    "api.powerbi.com",      # PowerBI API domain
    "analysis.windows.net",  # Power BI analysis domain
    "api.kusto.windows.net", # Kusto API
    # Add more domains to skip here as needed
]

# Add a list of domains that may have certificate issues but should be considered valid
TRUSTED_DOMAINS_WITH_CERT_ISSUES = [
    "jumpstartcdn-",        # Azure Front Door CDN domains used by aka.ms redirects
    "azurefd.net",          # Azure Front Door domain
]

# Function to detect false positive URLs that should be skipped
def is_false_positive(url):
    """Check if a URL is a known false positive pattern that should be skipped."""
    # Skip direct domain matches first (most efficient check)
    try:
        parsed_url = urlparse(url)
        if parsed_url.netloc in KNOWN_VALID_DOMAINS:
            print(f"Skipping trusted domain URL: {url}")
            return True
    except:
        pass  # Continue with other checks if parsing fails

    # Simple string patterns that should be skipped
    simple_skip_patterns = [
        "http://\\", 
        "http:\\", 
        "http://\\\\", 
        "http:\\\\\\", 
        "https://\\", 
        "https://\\\\"
    ]
    
    for pattern in simple_skip_patterns:
        if pattern in url:
            print(f"Skipping URL with backslashes: {url}")
            return True
    
    # Template Base URL patterns
    template_patterns = [
        r'\(\$templateBaseUrl',
        r'\(\$env:templateBaseUrl',
        r'\(\$Using:templateBaseUrl',
        r'\$Env:templateBaseUrl',  # PowerShell environment variable syntax
    ]
    
    # Storage account and GitHub patterns
    placeholder_patterns = [
        r'https://\{STORAGEACCOUNT\}\.blob\.core\.windows\.net/',
        r'https://\$githubPat@github\.com/\$githubUser/\$appsRepo\.git',
        r'http://\$URL:\$PORT',
        r'https://\$\(\$HCIBoxConfig\.WACVMName\)\.',
        r'https://\$stagingStorageAccountName\.blob\.core\.windows\.net/\$containerName/config',
    ]
    
    # PowerShell variable names that look like URLs or paths but aren't actual URLs
    powershell_variable_patterns = [
        r'\$websiteUrls',          # Variable holding website URLs
        r'\$websiteUrls\[',        # With array indexing
        r'\$websiteUrls\.',        # With property/method access
        r'\$mqttExplorerReleasesUrl', # MQTT Explorer releases URL variable
        r'\$mqttExplorerReleaseDownloadUrl', # MQTT Explorer download URL variable
        r'\$terminalDownloadUri',   # Terminal download URI variable
        r'\$uri',                  # Generic URI variable
        r'\$url',                  # Generic URL variable
        r'\$downloadUrl',          # Download URL variable
        r'\$aksEEReleasesUrl',     # AKS EE releases URL variable
        r'\$AKSEEReleaseDownloadUrl', # AKS EE download URL variable
        r'\$localPathStorageUrl',  # Local path storage URL variable
        r'\$acsadeployYamlUrl',    # ACSA deploy YAML URL variable
        r'\$aksEEk3sUrl',          # AKS EE K3s URL variable
        r'\$githubApiUrl',         # GitHub API URL variable
        r'\$fabricHeaders',        # Fabric API headers variable
        r'\$_',                    # PowerShell automatic variable for current pipeline object
    ]
    
    # Script files and commands that appear to be URLs but aren't
    script_file_patterns = [
        r'get_helm\.sh',           # Helm installation script
        r'http://\\',              # Escaped backslash in URL (not a real URL)
        r'http://\\\\',            # Multiple escaped backslashes in URL
        r'http://\\\\\S*',         # Multiple escaped backslashes with any additional characters
        r'https://\\\\\S*',        # Multiple escaped backslashes with HTTPS
    ]
    
    # Escaped backslashes in URLs or JSON path patterns - expanded patterns
    escaped_backslash_patterns = [
        r'http://\\+',             # One or more backslashes after http://
        r'https://\\+',            # One or more backslashes after https://
        r'http:\\+',               # Backslashes without forward slashes
        r'https:\\+',              # Backslashes without forward slashes
        r'http://\\\\\S*',         # Multiple escaped backslashes with any additional characters 
        r'http://\\',              # Single backslash
        r'http:/\\',               # Malformed backslash
        r'https://\\',             # HTTPS with backslash
    ]
    
    # Template variable patterns (JavaScript-style ${var} and shell-style $var)
    template_variable_patterns = [
        r'http://\${[^}]+}', # ${variable} format
        r'https://\${[^}]+}',
        r'http://\${[^}]+}:[0-9]+', # With port
        r'https://\${[^}]+}:[0-9]+',
        r'http://\${[^}]+}:[0-9]+/\w+', # With path after port
        r'https://\${[^}]+}:[0-9]+/\w+',
        r'http://\$[a-zA-Z0-9_]+', # $variable format (without braces)
        r'https://\$[a-zA-Z0-9_]+',
        r'http://\$[a-zA-Z0-9_]+:[0-9]+', # With port
        r'https://\$[a-zA-Z0-9_]+:[0-9]+',
        r'https://\$[a-zA-Z0-9_]+/\w+', # With path (no port)
        r'https://\${[^}]+}/\w+', # With path (no port) for braced variables
        r'https://[^/]+/\$[a-zA-Z0-9_]+', # Variable in path
        r'https://[^/]+/\${[^}]+}', # Braced variable in path
        r'https://\$Env:[a-zA-Z0-9_]+', # PowerShell Env variables in URLs
        r'https://\$env:[a-zA-Z0-9_]+', # PowerShell env variables in URLs (lowercase)
    ]
    
    # Query string variable patterns
    query_variable_patterns = [
        r'https://[^?]+\?[^=]+=\$[a-zA-Z0-9_]+',  # https://example.com?param=$variable
        r'https://[^?]+\?[^=]+=\${[^}]+}',        # https://example.com?param=${variable}
    ]
    
    # XML namespace URLs that aren't meant to be accessed directly
    xml_namespace_urls = [
        'http://www.w3.org/2000/svg',
        'http://www.w3.org/1999/xlink',
    ]
    
    # Special placeholder hostnames (typically used in configs/templates)
    placeholder_hostnames = [
        r'influxPlaceholder',
    ]
    
    # Patterns for specific GitHub raw URLs that are placeholders
    github_raw_urls = [
        r'https://raw\.githubusercontent\.com/microsoft/azure_arc/main/azure_jumpstart_ag/',
        r'https://raw\.githubusercontent\.com/microsoft/azure_arc/main/.+/'
    ]
    
    # Local script file patterns that shouldn't be checked as URLs
    local_script_patterns = [
        r'^\.\/[a-zA-Z0-9_-]+\.sh$',         # ./script.sh
        r'^\.\/[a-zA-Z0-9_-]+\.ps1$',        # ./script.ps1
        r'^\.\/[a-zA-Z0-9_-]+\.bat$',        # ./script.bat
        r'^\.\/[a-zA-Z0-9_-]+\.cmd$',        # ./script.cmd
        r'\.\/akri\.sh$',                    # ./akri.sh specifically
    ]
    
    # GitHub API URL patterns with variables
    github_api_variable_patterns = [
        r'\$gitHubAPIBaseUri\/repos\/\$githubUser\/\$appsRepo',
        r'\$gitHubAPIBaseUri\/repos\/[^\/]+\/[^\/]+',
        r'\$githubApiUrl',
        r'api\.github\.com\/repos\/\$[a-zA-Z0-9_]+\/',
    ]
    
    # Additional Management API domains that are valid but often give auth errors
    management_api_domains = [
        r'management\.core\.windows\.net',
    ]
    
    # HTTP verbs that are commonly used in PowerShell scripts and not actual URLs
    http_verbs = [
        r'^Get$', 
        r'^POST$',
        r'^GET$',
        r'^PUT$',
        r'^PATCH$',
        r'^DELETE$',
        r'^OPTIONS$',
        r'^HEAD$',
        r'^CONNECT$',
        r'^TRACE$',
        r'^Post$'
    ]
    
    # Check for standalone HTTP verbs
    for verb in http_verbs:
        if re.match(verb, url):
            print(f"Skipping HTTP verb: {url}")
            return True
    
    # Check for placeholder hostnames
    for hostname in placeholder_hostnames:
        if re.search(rf'https?://{hostname}(?::[0-9]+)?/?', url, re.IGNORECASE):
            print(f"Skipping placeholder hostname URL: {url}")
            return True
    
    # Check for specific GitHub raw URLs that are placeholders
    for pattern in github_raw_urls:
        if re.search(pattern, url):
            print(f"Skipping GitHub raw placeholder URL: {url}")
            return True
    
    # Check if URL matches any of the template patterns
    for pattern in template_patterns:
        if re.search(pattern, url):
            print(f"Skipping false positive template URL: {url}")
            return True
    
    # Check if URL matches any of the placeholder patterns
    for pattern in placeholder_patterns:
        if re.search(pattern, url):
            print(f"Skipping false positive placeholder URL: {url}")
            return True
    
    # Check if URL matches any of the PowerShell variable patterns
    for pattern in powershell_variable_patterns:
        if re.search(pattern, url):
            print(f"Skipping PowerShell variable URL: {url}")
            return True
    
    # Check if URL matches any of the script file patterns
    for pattern in script_file_patterns:
        if re.search(pattern, url):
            print(f"Skipping script file or command URL: {url}")
            return True
            
    # Check if URL matches escaped backslash patterns
    for pattern in escaped_backslash_patterns:
        if re.search(pattern, url):
            print(f"Skipping escaped backslash URL pattern: {url}")
            return True
    
    # Check if URL matches any of the template variable patterns
    for pattern in template_variable_patterns:
        if re.search(pattern, url):
            print(f"Skipping template variable URL: {url}")
            return True
    
    # Check if URL matches any of the query variable patterns
    for pattern in query_variable_patterns:
        if re.search(pattern, url):
            print(f"Skipping query variable URL: {url}")
            return True
    
    # Check for local script file patterns
    for pattern in local_script_patterns:
        if re.search(pattern, url):
            print(f"Skipping local script file: {url}")
            return True
    
    # Check for GitHub API URL variable patterns
    for pattern in github_api_variable_patterns:
        if re.search(pattern, url):
            print(f"Skipping GitHub API URL variable: {url}")
            return True
    
    # Check if URL contains management API domains
    for domain in management_api_domains:
        if re.search(domain, url):
            print(f"Skipping management API domain: {url}")
            return True
    
    # Check if URL is an XML namespace
    if url in xml_namespace_urls or url.startswith('http://www.w3.org/2000/svg') or url.startswith('http://www.w3.org/1999/xlink'):
        print(f"Skipping XML namespace URL: {url}")
        return True
    
    # Additional check for specific URLs that we know are problematic
    hardcoded_urls_to_skip = [
        "https://api.fabric.microsoft.com",
        "https://api.powerbi.com",
        "https://dashboards.kusto.windows.net",
        "https://api.kusto.windows.net",
        "https://analysis.windows.net",
        "https://wabi-us-central-b-primary-redirect.analysis.windows.net",
        "https://raw.githubusercontent.com/microsoft/azure_arc/main/azure_jumpstart_ag/",
        "http://influxPlaceholder:8086",
        "https://management.core.windows.net/", # Azure Management API
    ]
    
    if url in hardcoded_urls_to_skip:
        print(f"Skipping hardcoded URL: {url}")
        return True
            
    return False

# Image file extensions to identify image links
IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.ico']
# SVG files get special treatment
SVG_EXTENSIONS = ['.svg']

# Parse command line arguments
def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Check URLs in files for validity."
    )
    parser.add_argument(
        "--dir", 
        help="Only check files in this directory (relative to script location)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=TIMEOUT,
        help=f"Timeout in seconds for HTTP requests (default: {TIMEOUT})"
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="Folders to exclude from checking (can specify multiple paths)"
    )
    return parser.parse_args()

# =============================================================================
# FILE & URL PROCESSING FUNCTIONS
# =============================================================================

def find_files_to_check(exclude_folders=None):
    """
    Find all supported files in the repository, skipping 'archive' folders
    and any user-specified excluded folders.
    
    Args:
        exclude_folders: List of folder paths to exclude
        
    Returns:
        List of file paths to check
    """
    if exclude_folders is None:
        exclude_folders = []
    
    # Convert exclude_folders to absolute paths for easier comparison
    abs_exclude_folders = []
    for folder in exclude_folders:
        if os.path.isabs(folder):
            abs_exclude_folders.append(os.path.normpath(folder))
        else:
            abs_exclude_folders.append(os.path.normpath(os.path.join(REPO_PATH, folder)))
    
    if exclude_folders:
        print(f"Excluding folders: {', '.join(exclude_folders)}")
    
    files_to_check = []
    for root, dirs, files in os.walk(REPO_PATH):
        # Skip 'archive' folders, hidden directories, and excluded folders
        dirs[:] = [d for d in dirs if d.lower() != 'archive' and not d.startswith('.')]
        
        # Check if the current directory should be excluded
        if any(os.path.abspath(root).startswith(excluded) for excluded in abs_exclude_folders):
            print(f"Skipping excluded directory: {root}")
            dirs[:] = []  # Skip all subdirectories
            continue
        
        for file in files:
            file_ext = os.path.splitext(file)[1].lower()
            # Check if this is a supported file type
            if file_ext in SUPPORTED_FILE_TYPES:
                files_to_check.append(os.path.join(root, file))
    
    return files_to_check

def find_files_in_directory(directory, exclude_folders=None):
    """
    Find all supported files in the given directory, excluding specified folders.
    
    Args:
        directory: Directory to search in
        exclude_folders: List of folder paths to exclude
        
    Returns:
        List of file paths to check
    """
    if exclude_folders is None:
        exclude_folders = []
        
    # Convert exclude_folders to absolute paths for easier comparison
    abs_exclude_folders = []
    for folder in exclude_folders:
        if os.path.isabs(folder):
            abs_exclude_folders.append(os.path.normpath(folder))
        else:
            abs_exclude_folders.append(os.path.normpath(os.path.join(directory, folder)))
    
    files_to_check = []
    for root, dirs, files in os.walk(directory):
        # Check if the current directory should be excluded
        if any(os.path.abspath(root).startswith(excluded) for excluded in abs_exclude_folders):
            print(f"Skipping excluded directory: {root}")
            dirs[:] = []  # Skip all subdirectories
            continue
            
        for file in files:
            file_ext = os.path.splitext(file)[1].lower()
            # Check if this is a supported file type
            if file_ext in SUPPORTED_FILE_TYPES:
                files_to_check.append(os.path.join(root, file))
    return files_to_check

def extract_urls_by_file_type(file_path):
    """Extract URLs from a file based on its extension."""
    file_ext = os.path.splitext(file_path)[1].lower()
    
    urls = []
    file_type = SUPPORTED_FILE_TYPES.get(file_ext, 'Unknown')
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Markdown files
            if file_ext == '.md':
                # Use the existing markdown link extraction
                with open(file_path, 'r', encoding='utf-8') as md_file:
                    for line in md_file:
                        matches = MD_URL_REGEX.findall(line)
                        # Strip quotes from URLs
                        cleaned_matches = [match.strip('"\'') for match in matches]
                        urls.extend(cleaned_matches)
            
            # HTML files
            elif file_ext in ['.html', '.htm']:
                urls.extend([url for url in HTML_HREF_REGEX.findall(content) if url])
                urls.extend([url for url in HTML_SRC_REGEX.findall(content) if url])
                urls.extend([url for url in HTML_LINK_HREF_REGEX.findall(content) if url])
                urls.extend([url for url in HTML_META_CONTENT_REGEX.findall(content) if url and (url.startswith('http') or url.startswith('/') or url.startswith('.'))])
            
            # CSS files
            elif file_ext in ['.css', '.scss']:
                urls.extend([url for url in CSS_URL_REGEX.findall(content) if url])
            
            # JavaScript/TypeScript files
            elif file_ext in ['.js', '.jsx', '.ts', '.tsx']:
                js_matches = JS_URL_REGEX.findall(content)
                # Handle the case where we have groups in the regex
                for match in js_matches:
                    if isinstance(match, tuple):
                        urls.extend([m for m in match if m])
                    else:
                        urls.append(match)
            
            # Python files
            elif file_ext == '.py':
                urls.extend([url for url in PY_URL_REGEX.findall(content) if url])
                # Python imports are special - we don't check these as URLs but could in the future
            
            # JSON/YAML files
            elif file_ext in ['.json', '.yaml', '.yml']:
                urls.extend([url for url in JSON_URL_REGEX.findall(content) if url])
            
            # XML files
            elif file_ext == '.xml':
                urls.extend([url for url in XML_URL_REGEX.findall(content) if url])
                
            # Shell/Bash scripts
            elif file_ext in ['.sh', '.bash', '.zsh', '.ksh']:
                shell_matches = SHELL_URL_REGEX.findall(content)
                for match in shell_matches:
                    if isinstance(match, tuple):
                        urls.extend([m for m in match if m])
                    else:
                        urls.append(match)
            
            # PowerShell scripts
            elif file_ext in ['.ps1', '.psm1', '.psd1']:
                ps_matches = PS_URL_REGEX.findall(content)
                for match in ps_matches:
                    if isinstance(match, tuple):
                        urls.extend([m for m in match if m])
                    else:
                        urls.append(match)
                        
            # Batch/CMD scripts
            elif file_ext in ['.bat', '.cmd']:
                urls.extend([url for url in BATCH_URL_REGEX.findall(content) if url])
                
            # Perl/Ruby/Other scripting languages
            elif file_ext in ['.pl', '.pm', '.rb', '.php', '.lua', '.tcl', '.groovy', '.awk', '.r', '.R']:
                urls.extend([url for url in SCRIPT_URL_REGEX.findall(content) if url])
                
            # Configuration files
            elif file_ext in ['.ini', '.conf', '.cfg', '.toml', '.env']:
                urls.extend([url for url in CONFIG_URL_REGEX.findall(content) if url])
            
            # For other file types, use a generic approach to find http(s) URLs
            else:
                generic_url_regex = re.compile(r'(?:https?://[^\s\'">]+)')
                urls.extend([url for url in generic_url_regex.findall(content) if url])
            
            print(f"Found {len(urls)} URLs in {file_type} file: {file_path}")
            
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
    
    return urls

def extract_urls(file_path):
    """Extract all URLs from a file using the appropriate method based on file type."""
    return extract_urls_by_file_type(file_path)

def extract_headers(md_file):
    """Extract all headers from a markdown file and convert to slug format for link validation."""
    headers = []
    # Only attempt to extract headers from markdown files
    if not md_file.lower().endswith('.md'):
        print(f"Warning: Attempted to extract headers from non-markdown file: {md_file}")
        return headers
        
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip().startswith('#'):
                    # Extract the header text (remove the # and any leading/trailing whitespace)
                    header_text = line.lstrip('#').strip()
                    
                    # Convert to lowercase
                    header_text_lower = header_text.lower()
                    
                    # Remove markdown formatting (bold, italic, code)
                    header_text_clean = re.sub(r'[*_`]', '', header_text_lower)
                    
                    # Create slug: keep only alphanumeric chars and hyphens, replace spaces with hyphens
                    header_slug = re.sub(r'[^\w\- ]', '', header_text_clean)
                    header_slug = re.sub(r'\s+', '-', header_slug)
                    
                    # Add to the list of headers
                    headers.append(header_slug)
                    print(f"Found header: '{header_text}' -> slug: '{header_slug}'")
    except Exception as e:
        print(f"Warning: Could not extract headers from {md_file}: {str(e)}")
    return headers

def is_ip_based_url(url):
    """Check if a URL uses an IP address instead of a domain name."""
    try:
        host = urlparse(url).hostname
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False

# Define a list of temporary error status codes
TEMPORARY_ERROR_CODES = [502, 503, 504, 429]  # Added 429 (Too Many Requests)

def check_absolute_url(url, md_file=None, retries=3):
    """
    Check if an absolute URL (http/https) is reachable.
    
    Args:
        url: The URL to check
        md_file: Source markdown file containing this URL
        retries: Number of attempts before giving up
        
    Returns:
        Log entry string with result
    """
    # Extract domain from URL for domain-based verification
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    is_trusted_domain = domain in KNOWN_VALID_DOMAINS
    
    print(f"Checking absolute URL: {url}")
    print(f"Domain: {domain}, Trusted: {is_trusted_domain}")
    
    attempt = 0
    while attempt < retries:
        try:
            # Make the request with configured timeout
            response = requests.get(url, headers=HEADERS, allow_redirects=True, timeout=TIMEOUT, stream=True)
            
            if response.status_code < 400:
                log_entry = f"{Colors.OKGREEN}[OK ABSOLUTE] {url}{Colors.ENDC}"
                print(log_entry)
                return log_entry
            elif response.status_code in TEMPORARY_ERROR_CODES:
                # For temporary errors, handle differently based on trusted status
                print(f"Status Code {response.status_code} for {url}. Retrying... ({attempt + 1}/{retries})")
                attempt += 1
                
                if attempt >= retries:
                    file_info = f" (in file: {md_file})" if md_file else ""
                    
                    if is_trusted_domain:
                        # For trusted domains, mark as OK even with temporary errors
                        log_entry = f"{Colors.OKGREEN}[OK ABSOLUTE] {url} (trusted domain with temporary status code: {response.status_code}){file_info}{Colors.ENDC}"
                        print(log_entry)
                        return log_entry
                    else:
                        # For non-trusted domains, still mark as broken but note it might be temporary
                        log_entry = f"{Colors.FAIL}[BROKEN ABSOLUTE] {url} - Temporary error: {response.status_code}{file_info}{Colors.ENDC}"
                        print(log_entry)
                        return log_entry
            else:
                file_info = f" (in file: {md_file})" if md_file else ""
                # For non-temporary errors, mark as broken even for trusted domains
                log_entry = f"{Colors.FAIL}[BROKEN ABSOLUTE] {url} - Status Code: {response.status_code}{file_info}{Colors.ENDC}"
                print(log_entry)
                return log_entry
                
        except requests.RequestException as e:
            file_info = f" (in file: {md_file})" if md_file else ""
            
            # For connection errors on trusted domains, consider as temporarily unavailable
            if is_trusted_domain and isinstance(e, (
                requests.Timeout, 
                requests.ConnectionError,
                requests.TooManyRedirects
            )):
                # Last retry and it's a trusted domain with connection issues
                if attempt >= retries - 1:
                    log_entry = f"{Colors.OKGREEN}[OK ABSOLUTE] {url} (trusted domain, connection issue: {type(e).__name__}){file_info}{Colors.ENDC}"
                    print(log_entry)
                    return log_entry
            
            # Special handling for certificate errors on trusted domains
            if isinstance(e, requests.exceptions.SSLError):
                if any(trusted_domain in domain for trusted_domain in TRUSTED_DOMAINS_WITH_CERT_ISSUES) or any(trusted_domain in url for trusted_domain in TRUSTED_DOMAINS_WITH_CERT_ISSUES):
                    log_entry = f"{Colors.OKGREEN}[OK ABSOLUTE] {url} (trusted domain with certificate issue){file_info}{Colors.ENDC}"
                    print(log_entry)
                    return log_entry
            
            log_entry = f"{Colors.FAIL}[BROKEN ABSOLUTE] {url} - Error: {e}{file_info}{Colors.ENDC}"
            print(log_entry)
            attempt += 1
            if attempt < retries:
                print(f"Retrying... ({attempt}/{retries})")
            else:
                return log_entry

def find_case_insensitive_path(path):
    """
    Tries to find an existing path with case-insensitive matching.
    Useful for systems where the filesystem is case-sensitive but the URLs might not match case.
    
    Args:
        path: The path to check
        
    Returns:
        The correct path if found with different case, None otherwise
    """
    # If the path exists exactly as provided, no need to search
    if os.path.exists(path):
        return path
    
    # Not found, try to match case-insensitively
    dirname, basename = os.path.split(path)
    
    # If the directory doesn't exist, we can't check its contents
    if not os.path.isdir(dirname):
        return None

    try:
        # Check if a case-insensitive match exists in the parent directory
        for entry in os.listdir(dirname):
            if entry.lower() == basename.lower():
                return os.path.join(dirname, entry)
    except (PermissionError, FileNotFoundError):
        pass
            
    return None

def find_path_case_insensitive(base_path, rel_path):
    """
    Find a path with case-insensitive matching, handling multi-level paths.
    
    Args:
        base_path: Starting directory for the search
        rel_path: Relative path to find (can include multiple directories)
        
    Returns:
        Full corrected path if found, None otherwise
    """
    # Handle empty path
    if not rel_path:
        return base_path
    
    # Split the path into components, handling both forward and back slashes
    path_parts = re.split(r'[/\\]', rel_path)
    path_parts = [part for part in path_parts if part]  # Remove empty parts
    
    current_path = base_path
    print(f"Starting case-insensitive path search from: {current_path}")
    print(f"Looking for path components: {path_parts}")
    
    # Process each path component
    for i, part in enumerate(path_parts):
        # Skip if the component is '.' (current directory)
        if part == '.':
            continue
        
        # Handle '..' (parent directory) - just use it directly as it doesn't need case correction
        if part == '..':
            current_path = os.path.dirname(current_path)
            print(f"Going up to parent directory: {current_path}")
            continue
        
        # Try to find a case-insensitive match for this component
        found = False
        try:
            if os.path.exists(os.path.join(current_path, part)):
                # Exact match exists, use it directly
                current_path = os.path.join(current_path, part)
                found = True
                print(f"Exact match found for '{part}': {current_path}")
            else:
                # Try case-insensitive match
                for entry in os.listdir(current_path):
                    if entry.lower() == part.lower():
                        current_path = os.path.join(current_path, entry)
                        found = True
                        print(f"Case-insensitive match found for '{part}': {entry} at {current_path}")
                        break
        except (PermissionError, FileNotFoundError, NotADirectoryError) as e:
            print(f"Error accessing {current_path}: {str(e)}")
            return None
        
        if not found:
            print(f"No match found for component '{part}' in {current_path}")
            return None
    
    # Add trailing slash if the original path had one
    if rel_path.endswith('/') and not current_path.endswith(os.sep):
        current_path += os.sep
    
    print(f"Final resolved path: {current_path}")
    return current_path

def check_relative_url(url, md_file):
    """
    Check if a relative file path exists in the filesystem.
    
    Args:
        url: Relative path to check
        md_file: Source markdown file containing this path
        
    Returns:
        Tuple containing: (log_entry, is_image, is_svg, is_root_relative, has_anchor)
    """
    # Flag to track if URL has an anchor
    has_anchor = '#' in url
    anchor_text = None
    
    # Handle header links (e.g., #section-name or file.md#section-name)
    if has_anchor and md_file.lower().endswith('.md'):
        base_url, anchor = url.split('#', 1)
        anchor_text = anchor
        # If it's a same-page link (just #header)
        if not base_url:
            headers = extract_headers(md_file)
            if anchor in headers:
                log_entry = f"{Colors.OKGREEN}[OK HEADER] #{anchor} (header in {md_file}){Colors.ENDC}"
                print(log_entry)
                return log_entry, False, False, False, has_anchor
            else:
                log_entry = f"{Colors.FAIL}[BROKEN HEADER] #{anchor} (header not found in {md_file}){Colors.ENDC}"
                print(f"Available headers in {md_file}: {', '.join(headers)}")
                print(log_entry)
                return log_entry, False, False, False, has_anchor
        else:
            # Construct the target path based on the base_url
            target_file = os.path.join(os.path.dirname(md_file), base_url)
            
            # Handle the case where the base_url points to a directory
            if os.path.isdir(target_file):
                print(f"Base URL {base_url} points to a directory: {target_file}")
                # Check if an _index.md file exists in the directory
                index_file = os.path.join(target_file, "_index.md")
                if os.path.exists(index_file):
                    log_entry = f"{Colors.OKGREEN}[OK RELATIVE] {index_file}#{anchor} (directory with _index.md, anchor not validated){Colors.ENDC}"
                    print(log_entry)
                    return log_entry, False, False, False, has_anchor
                
                # Also check for other common index files
                for index_name in ["index.md", "README.md"]:
                    index_file = os.path.join(target_file, index_name)
                    if os.path.exists(index_file):
                        log_entry = f"{Colors.OKGREEN}[OK RELATIVE] {index_file}#{anchor} (directory with {index_name}, anchor not validated){Colors.ENDC}"
                        print(log_entry)
                        return log_entry, False, False, False, has_anchor
            
            # Check if file exists without case sensitivity
            case_insensitive_path = find_path_case_insensitive(os.path.dirname(md_file), base_url)
            if case_insensitive_path and os.path.exists(case_insensitive_path):
                # Found with case-insensitive match
                if os.path.isdir(case_insensitive_path):
                    # It's a directory, check for index files
                    for index_name in ["_index.md", "index.md", "README.md"]:
                        index_file = os.path.join(case_insensitive_path, index_name)
                        if os.path.exists(index_file):
                            log_entry = f"{Colors.OKGREEN}[OK RELATIVE] {index_file}#{anchor} (directory with {index_name}, case-insensitive match, anchor not validated){Colors.ENDC}"
                            print(log_entry)
                            return log_entry, False, False, False, has_anchor
                else:
                    # It's a file
                    log_entry = f"{Colors.OKGREEN}[OK RELATIVE] {case_insensitive_path}#{anchor} (file exists, case-insensitive match, anchor not validated){Colors.ENDC}"
                    print(log_entry)
                    return log_entry, False, False, False, has_anchor
            
            # Original check if file exists (case sensitive)
            if os.path.exists(target_file):
                log_entry = f"{Colors.OKGREEN}[OK RELATIVE] {target_file}#{anchor} (file exists, anchor not validated){Colors.ENDC}"
                print(log_entry)
                return log_entry, False, False, False, has_anchor
            else:
                log_entry = f"{Colors.FAIL}[BROKEN RELATIVE WITH ANCHOR] {target_file}#{anchor} (file not found){Colors.ENDC}"
                print(log_entry)
                return log_entry, False, False, False, has_anchor
                
    # Handle hash in URL for non-markdown source files
    elif has_anchor:
        base_url, anchor = url.split('#', 1)
        anchor_text = anchor
        # For non-markdown file links with anchors, we just check if the file exists
        if not base_url:
            # Same-file anchor in non-markdown file, we can't validate this
            log_entry = f"{Colors.OKGREEN}[OK HEADER] #{anchor} (in non-markdown file {md_file}){Colors.ENDC}"
            print(log_entry)
            return log_entry, False, False, False, has_anchor
        else:
            target_file = os.path.join(os.path.dirname(md_file), base_url)
            if os.path.exists(target_file):
                log_entry = f"{Colors.OKGREEN}[OK RELATIVE] {target_file}#{anchor} (file exists, anchor not validated){Colors.ENDC}"
                print(log_entry)
                return log_entry, False, False, False, has_anchor
            else:
                log_entry = f"{Colors.FAIL}[BROKEN RELATIVE WITH ANCHOR] {target_file}#{anchor} (file not found){Colors.ENDC}"
                print(log_entry)
                return log_entry, False, False, False, has_anchor

    # Check if it's an SVG file
    is_svg = any(url.lower().endswith(ext) for ext in SVG_EXTENSIONS)
    # Check if it's an image file
    is_image = not is_svg and any(url.lower().endswith(ext) for ext in IMAGE_EXTENSIONS)
    
    # Handle root-relative URLs (starting with /)
    is_root_relative = url.startswith('/')
    if is_root_relative:
        # URLs starting with / are relative to repo root, not the current file
        file_path = os.path.join(REPO_PATH, url[1:])  # Remove leading / and join with repo root
        print(f"Root-relative path detected. Checking against repo root: {file_path}")
    else:
        # Regular document-relative URL
        file_path = os.path.join(os.path.dirname(md_file), url)
    
    file_type = "SVG" if is_svg else "image" if is_image else "root-relative" if is_root_relative else "relative"
    print(f"Checking {file_type} URL: {file_path}")
    
    # -- New Approach: Handle case sensitivity more robustly --
    # Check if path exists directly
    path_exists = os.path.exists(file_path)
    
    # If path doesn't exist, try case-insensitive matching
    if not path_exists:
        print(f"Path not found: {file_path}")
        print(f"Trying case-insensitive path resolution...")
        
        # For directory URLs (ending with /)
        if url.endswith('/'):
            # Split the file_path into components
            path_parts = os.path.normpath(file_path).split(os.sep)
            
            # Start from an existing directory
            current = os.path.dirname(md_file) if not is_root_relative else REPO_PATH
            built_path = current
            
            # Process each segment of the relative path
            rel_segments = url.rstrip('/').split('/')
            print(f"Processing relative segments: {rel_segments}")
            
            for segment in rel_segments:
                if segment == '..':
                    # Go up one directory
                    current = os.path.dirname(current)
                    built_path = current
                    print(f"Going up to parent: {current}")
                elif segment == '.':
                    # Stay in current directory
                    continue
                else:
                    # Try to find a case-insensitive match for this segment
                    if os.path.exists(os.path.join(current, segment)):
                        # Exact case match
                        current = os.path.join(current, segment)
                        built_path = current
                        print(f"Exact match found: {segment}")
                    else:
                        found = False
                        try:
                            for item in os.listdir(current):
                                if item.lower() == segment.lower():
                                    current = os.path.join(current, item)
                                    built_path = current
                                    print(f"Case-insensitive match found: {segment} -> {item}")
                                    found = True
                                    break
                        except (PermissionError, FileNotFoundError, NotADirectoryError) as e:
                            print(f"Error accessing {current}: {str(e)}")
                        
                        if not found:
                            print(f"No match found for segment: {segment} in {current}")
                            break
            
            if os.path.exists(built_path):
                file_path = built_path
                path_exists = True
                print(f"Successfully resolved case-insensitive path: {built_path}")
                
                # Check for default files in the directory
                if os.path.isdir(built_path):
                    for default_file in ['_index.md', 'index.md', 'README.md']:
                        default_path = os.path.join(built_path, default_file)
                        if os.path.exists(default_path):
                            file_path = default_path
                            print(f"Found default file: {default_path}")
                            break
    
    # If path still doesn't exist and it's a directory URL, try to check for markdown files
    if not path_exists and url.endswith('/') and os.path.isdir(os.path.dirname(file_path)):
        try:
            md_files = [f for f in os.listdir(file_path) if f.endswith('.md')]
            if md_files:
                path_exists = True
                file_path = os.path.join(file_path, md_files[0])  # Use the first markdown file found
                print(f"Directory contains markdown files: {', '.join(md_files)}")
            else:
                print(f"Directory exists but contains no markdown files")
        except PermissionError:
            print(f"Permission error accessing directory: {file_path}")
        except FileNotFoundError:
            print(f"Directory doesn't exist: {file_path}")
    
    if path_exists:
        if is_svg:
            log_entry = f"{Colors.OKGREEN}[OK SVG] {file_path}{Colors.ENDC}"
        elif is_image:
            log_entry = f"{Colors.OKGREEN}[OK IMAGE] {file_path}{Colors.ENDC}"
        elif is_root_relative:
            log_entry = f"{Colors.OKGREEN}[OK ROOT-RELATIVE] {file_path} (root-relative path: {url}){Colors.ENDC}"
        else:
            log_entry = f"{Colors.OKGREEN}[OK RELATIVE] {file_path}{Colors.ENDC}"
        print(log_entry)
        return log_entry, is_image, is_svg, is_root_relative, has_anchor
    else:
        if is_svg:
            log_entry = f"{Colors.FAIL}[BROKEN SVG] {file_path} (SVG in {md_file}){Colors.ENDC}"
        elif is_image:
            log_entry = f"{Colors.FAIL}[BROKEN IMAGE] {file_path} (image in {md_file}){Colors.ENDC}"
        elif is_root_relative:
            log_entry = f"{Colors.FAIL}[BROKEN ROOT-RELATIVE] {file_path} (root-relative path: {url} in {md_file}){Colors.ENDC}"
        else:
            # Update the log message to indicate whether the URL has an anchor or not
            if has_anchor:
                log_entry = f"{Colors.FAIL}[BROKEN RELATIVE WITH ANCHOR] {url} (relative path in {md_file}){Colors.ENDC}"
            else:
                log_entry = f"{Colors.FAIL}[BROKEN RELATIVE WITHOUT ANCHOR] {url} (relative path in {md_file}){Colors.ENDC}"
        print(log_entry)
        return log_entry, is_image, is_svg, is_root_relative, has_anchor

def strip_ansi_escape_codes(text):
    """Remove ANSI color codes from text (for clean log files)."""
    return ANSI_ESCAPE_REGEX.sub('', text)

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    # Parse arguments
    args = parse_arguments()
    
    # Override timeout if provided
    global TIMEOUT
    if args.timeout:
        TIMEOUT = args.timeout
        print(f"Using custom timeout: {TIMEOUT} seconds")
    
    # Lists to track results
    broken_absolute_urls = []
    ok_absolute_urls = []
    broken_relative_urls_with_anchor = []
    broken_relative_urls_without_anchor = []
    ok_relative_urls = []
    broken_image_urls = []
    ok_image_urls = []
    broken_svg_urls = []
    ok_svg_urls = []
    broken_header_urls = []
    ok_header_urls = []
    broken_root_relative_urls = []
    ok_root_relative_urls = []
    no_links_types = []
    
    # If a specific directory is provided, only check files there
    if args.dir:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        test_dir = os.path.join(script_dir, args.dir)
        print(f"Only checking files in test directory: {test_dir}")
        files_to_check = find_files_in_directory(test_dir, args.exclude)
    else:
        files_to_check = find_files_to_check(args.exclude)
    
    # Create log file with timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_file_with_timestamp = os.path.join(LOG_DIR, f'broken_urls_{timestamp}.log')
    
    print(f"Starting URL check on {len(files_to_check)} files...")
    start_time = datetime.now()
    
    # Process all files and URLs - write to log in real-time for monitoring
    with open(log_file_with_timestamp, 'w', encoding='utf-8') as log:
        log.write(f"URL Checker Results\n\n")
        log.write(f"Log generated on: {timestamp}\n")
        log.write("Processing URLs in real-time...\n\n")
        log.flush()
        
        for file_path in files_to_check:
            file_ext = os.path.splitext(file_path)[1].lower()
            file_type = SUPPORTED_FILE_TYPES.get(file_ext, 'Unknown')
            print(f"Processing {file_type} file: {file_path}")
            urls = extract_urls(file_path)
            
            for url in urls:
                # Skip email links
                if EMAIL_REGEX.match(url):
                    print(f"Skipping email URL: {url}")
                    continue
                
                # Skip localhost and IP-based URLs
                if url.startswith("http://localhost") or is_ip_based_url(url):
                    print(f"Skipping localhost or IP-based URL: {url}")
                    continue
                
                # Skip false positive URLs
                if is_false_positive(url):
                    continue
                
                # Add error handling for URL parsing
                try:
                    # Check URL based on whether it's absolute or relative
                    parsed_url = urlparse(url)
                    if parsed_url.scheme in ('http', 'https'):
                        # It's an absolute URL - pass the file path to track source
                        log_entry = check_absolute_url(url, file_path)
                        if "[OK ABSOLUTE]" in log_entry:
                            ok_absolute_urls.append(log_entry)
                        else:
                            broken_absolute_urls.append(log_entry)
                    else:
                        # Strip quotes before further processing to avoid false positives
                        url_clean = url.strip('"\'')
                        
                        try:
                            parsed_clean = urlparse(url_clean)
                            
                            # Check again if it's actually an absolute URL after stripping quotes
                            if parsed_clean.scheme in ('http', 'https'):
                                # Skip false positive URLs after cleaning
                                if is_false_positive(url_clean):
                                    continue
                                log_entry = check_absolute_url(url_clean, file_path)
                                if "[OK ABSOLUTE]" in log_entry:
                                    ok_absolute_urls.append(log_entry)
                                else:
                                    broken_absolute_urls.append(log_entry)
                            else:
                                # It's a relative URL, image, SVG, root-relative, or header link
                                log_entry, is_image, is_svg, is_root_relative, has_anchor = check_relative_url(url, file_path)
                                
                                # ...existing categorization code...
                                if "[BROKEN HEADER]" in log_entry:
                                    broken_header_urls.append(log_entry)
                                elif "[OK HEADER]" in log_entry:
                                    ok_header_urls.append(log_entry)
                                elif is_svg:
                                    if "[OK SVG]" in log_entry:
                                        ok_svg_urls.append(log_entry)
                                    else:
                                        broken_svg_urls.append(log_entry)
                                elif is_image:
                                    if "[OK IMAGE]" in log_entry:
                                        ok_image_urls.append(log_entry)
                                    else:
                                        broken_image_urls.append(log_entry)
                                elif is_root_relative:
                                    if "[OK ROOT-RELATIVE]" in log_entry:
                                        ok_root_relative_urls.append(log_entry)
                                    else:
                                        broken_root_relative_urls.append(log_entry)
                                else:
                                    if "[OK RELATIVE]" in log_entry:
                                        ok_relative_urls.append(log_entry)
                                    else:
                                        # Use the new log message format for categorization
                                        if "[BROKEN RELATIVE WITH ANCHOR]" in log_entry:
                                            broken_relative_urls_with_anchor.append(log_entry)
                                        elif "[BROKEN RELATIVE WITHOUT ANCHOR]" in log_entry:
                                            broken_relative_urls_without_anchor.append(log_entry)
                        
                        except ValueError as e:
                            # Handle URL parsing errors for the cleaned URL
                            error_message = str(e)
                            log_entry = f"{Colors.FAIL}[MALFORMED URL] {url_clean} - Error: {error_message} (in file: {file_path}){Colors.ENDC}"
                            print(log_entry)
                            broken_absolute_urls.append(log_entry)
                
                except ValueError as e:
                    # Handle URL parsing errors
                    error_message = str(e)
                    if "Invalid IPv6 URL" in error_message:
                        log_entry = f"{Colors.FAIL}[MALFORMED URL] {url} - Invalid IPv6 URL format (in file: {file_path}){Colors.ENDC}"
                    else:
                        log_entry = f"{Colors.FAIL}[MALFORMED URL] {url} - Error: {error_message} (in file: {file_path}){Colors.ENDC}"
                    print(log_entry)
                    broken_absolute_urls.append(log_entry)
                
                # Write to log file (real-time monitoring)
                log.write(strip_ansi_escape_codes(log_entry) + "\n")
                log.flush()
    
    # Calculate runtime
    end_time = datetime.now()
    runtime_duration = end_time - start_time
    runtime_seconds = runtime_duration.total_seconds()
    
    # Create a human-readable runtime string
    if runtime_seconds < 60:
        runtime_str = f"{runtime_seconds:.2f} seconds"
    elif runtime_seconds < 3600:
        runtime_str = f"{runtime_seconds/60:.2f} minutes ({runtime_duration})"
    else:
        runtime_str = f"{runtime_seconds/3600:.2f} hours ({runtime_duration})"
    
    # Write the log file with organized results
    with open(log_file_with_timestamp, 'w', encoding='utf-8') as log:
        log.write(f"URL Checker Results\n\n")
        log.write(f"Log generated on: {timestamp}\n")
        log.write(f"Runtime: {runtime_str}\n")
        log.write(f"Runtime duration: {runtime_duration}\n\n")
        
        # Write broken sections first (most important)
        log.write(f"=== Broken Absolute URLs ({len(broken_absolute_urls)} links found) ===\n\n")
        if broken_absolute_urls:
            log.write("\n".join(strip_ansi_escape_codes(url) for url in broken_absolute_urls) + "\n\n")
        else:
            log.write("No broken absolute URLs found.\n\n")
        
        log.write(f"=== Broken Relative URLs Without Anchors ({len(broken_relative_urls_without_anchor)} links found) ===\n\n")
        if broken_relative_urls_without_anchor:
            log.write("\n".join(strip_ansi_escape_codes(url) for url in broken_relative_urls_without_anchor) + "\n\n")
        else:
            log.write("No broken relative URLs without anchors found.\n\n")
        
        log.write(f"=== Broken Relative URLs With Anchors ({len(broken_relative_urls_with_anchor)} links found) ===\n\n")
        if broken_relative_urls_with_anchor:
            log.write("\n".join(strip_ansi_escape_codes(url) for url in broken_relative_urls_with_anchor) + "\n\n")
        else:
            log.write("No broken relative URLs with anchors found.\n\n")
        
        log.write(f"=== Broken Root-Relative URLs ({len(broken_root_relative_urls)} links found) ===\n\n")
        if broken_root_relative_urls:
            log.write("\n".join(strip_ansi_escape_codes(url) for url in broken_root_relative_urls) + "\n\n")
        else:
            log.write("No broken root-relative URLs found.\n\n")
        
        log.write(f"=== Broken Image URLs ({len(broken_image_urls)} links found) ===\n\n")
        if broken_image_urls:
            log.write("\n".join(strip_ansi_escape_codes(url) for url in broken_image_urls) + "\n\n")
        else:
            log.write("No broken image URLs found.\n\n")
        
        log.write(f"=== Broken SVG URLs ({len(broken_svg_urls)} links found) ===\n\n")
        if broken_svg_urls:
            log.write("\n".join(strip_ansi_escape_codes(url) for url in broken_svg_urls) + "\n\n")
        else:
            log.write("No broken SVG URLs found.\n\n")
        
        log.write(f"=== Broken Header Links ({len(broken_header_urls)} links found) ===\n\n")
        if broken_header_urls:
            log.write("\n".join(strip_ansi_escape_codes(url) for url in broken_header_urls) + "\n\n")
        else:
            log.write("No broken header links found.\n\n")
        
        log.write(f"=== OK Absolute URLs ({len(ok_absolute_urls)} links found) ===\n\n")
        if ok_absolute_urls:
            log.write("\n".join(strip_ansi_escape_codes(url) for url in ok_absolute_urls) + "\n\n")
        else:
            log.write("No absolute URLs found.\n\n")
        
        log.write(f"=== OK Relative URLs ({len(ok_relative_urls)} links found) ===\n\n")
        if ok_relative_urls:
            log.write("\n".join(strip_ansi_escape_codes(url) for url in ok_relative_urls) + "\n\n")
        else:
            log.write("No relative URLs found.\n\n")
        
        log.write(f"=== OK Root-Relative URLs ({len(ok_root_relative_urls)} links found) ===\n\n")
        if ok_root_relative_urls:
            log.write("\n".join(strip_ansi_escape_codes(url) for url in ok_root_relative_urls) + "\n\n")
        else:
            log.write("No root-relative URLs found.\n\n")
        
        log.write(f"=== OK Image URLs ({len(ok_image_urls)} links found) ===\n\n")
        if ok_image_urls:
            log.write("\n".join(strip_ansi_escape_codes(url) for url in ok_image_urls) + "\n\n")
        else:
            log.write("No image URLs found.\n\n")
        
        log.write(f"=== OK SVG URLs ({len(ok_svg_urls)} links found) ===\n\n")
        if ok_svg_urls:
            log.write("\n".join(strip_ansi_escape_codes(url) for url in ok_svg_urls) + "\n\n")
        else:
            log.write("No SVG URLs found.\n\n")
        
        log.write(f"=== OK Header Links ({len(ok_header_urls)} links found) ===\n\n")
        if ok_header_urls:
            log.write("\n".join(strip_ansi_escape_codes(url) for url in ok_header_urls) + "\n\n")
        else:
            log.write("No header links found.\n\n")
        
        # Add summary with improved informative title and hierarchical format
        total_broken = (len(broken_absolute_urls) + 
                        len(broken_relative_urls_with_anchor) + 
                        len(broken_relative_urls_without_anchor) + 
                        len(broken_root_relative_urls) + 
                        len(broken_image_urls) + 
                        len(broken_svg_urls) + 
                        len(broken_header_urls)
                        )
        
        total_ok = len(ok_absolute_urls) + len(ok_relative_urls) + len(ok_root_relative_urls) + len(ok_image_urls) + len(ok_svg_urls) + len(ok_header_urls)
        total_links = total_broken + total_ok
        
        # Updated categorization logic
        no_links_types = []  # Categories with no links at all (neither broken nor OK)
        zero_broken_types = []  # Categories with OK links but no broken links
        broken_types = []  # Categories with broken links
        
        # Absolute URLs
        if len(broken_absolute_urls) == 0 and len(ok_absolute_urls) == 0:
            no_links_types.append(("Absolute URLs", 0))
        elif len(broken_absolute_urls) == 0:
            zero_broken_types.append(("Absolute URLs", len(ok_absolute_urls)))
        else:
            broken_types.append(("Absolute URLs", len(broken_absolute_urls)))
            
        # Relative URLs without anchors and with anchors combined
        if len(broken_relative_urls_without_anchor) == 0 and len(broken_relative_urls_with_anchor) == 0 and len(ok_relative_urls) == 0:
            no_links_types.append(("Relative URLs", 0))
        elif len(broken_relative_urls_without_anchor) == 0 and len(broken_relative_urls_with_anchor) == 0:
            zero_broken_types.append(("Relative URLs", len(ok_relative_urls)))
        else:
            # Count broken relative URLs with and without anchors separately
            if len(broken_relative_urls_without_anchor) > 0:
                broken_types.append(("Relative URLs without anchors", len(broken_relative_urls_without_anchor)))
            if len(broken_relative_urls_with_anchor) > 0:
                broken_types.append(("Relative URLs with anchors", len(broken_relative_urls_with_anchor)))
                
        # Root-relative URLs
        if len(broken_root_relative_urls) == 0 and len(ok_root_relative_urls) == 0:
            no_links_types.append(("Root-relative URLs", 0))
        elif len(broken_root_relative_urls) == 0:
            zero_broken_types.append(("Root-relative URLs", len(ok_root_relative_urls)))
        else:
            broken_types.append(("Root-relative URLs", len(broken_root_relative_urls)))
            
        # Image URLs
        if len(broken_image_urls) == 0 and len(ok_image_urls) == 0:
            no_links_types.append(("Image URLs", 0))
        elif len(broken_image_urls) == 0:
            zero_broken_types.append(("Image URLs", len(ok_image_urls)))
        else:
            broken_types.append(("Image URLs", len(broken_image_urls)))
            
        # SVG URLs
        if len(broken_svg_urls) == 0 and len(ok_svg_urls) == 0:
            no_links_types.append(("SVG URLs", 0))
        elif len(broken_svg_urls) == 0:
            zero_broken_types.append(("SVG URLs", len(ok_svg_urls)))
        else:
            broken_types.append(("SVG URLs", len(broken_svg_urls)))
            
        # Header links
        if len(broken_header_urls) == 0 and len(ok_header_urls) == 0:
            no_links_types.append(("Header links", 0))
        elif len(broken_header_urls) == 0:
            zero_broken_types.append(("Header links", len(ok_header_urls)))
        else:
            broken_types.append(("Header links", len(broken_header_urls)))
        
        # Write modernized summary to log file
        log.write("\n" + "═" * 80 + "\n")
        log.write(f"📊 LINK VALIDATION SUMMARY ({total_links} links checked)\n")
        log.write("═" * 80 + "\n\n")
        
        # Always show broken links section if there are any broken links
        if total_broken > 0:
            log.write(f"❌ BROKEN LINKS: {total_broken}\n")
            # Only show categories that actually have broken links
            for category, count in broken_types:
                log.write(f"   • {category}: {count}\n")
            log.write("\n")
        else:
            log.write(f"✅ BROKEN LINKS: 0 (All links are valid!)\n\n")
        
        # Show categories with no links found
        if no_links_types:
            log.write(f"📭 NO LINKS FOUND: {len(no_links_types)}\n")
            for category, _ in no_links_types:
                log.write(f"   • {category}\n")
            log.write("\n")
            
        # Show categories with no broken links (but have OK links)
        if zero_broken_types:
            log.write(f"🔍 CATEGORIES WITH NO BROKEN LINKS: {len(zero_broken_types)}\n")
            for category, count in zero_broken_types:
                log.write(f"   • {category}: {count} OK links\n")
            log.write("\n")
            
        log.write(f"✅ OK LINKS: {total_ok}\n\n")
        
        # Add runtime to log summary
        log.write(f"⏱️ RUNTIME: {runtime_str}\n\n")
        
        # Add final conclusion with emoji
        broken_links_found = bool(broken_absolute_urls or broken_relative_urls_with_anchor or broken_relative_urls_without_anchor or
                                 broken_root_relative_urls or broken_image_urls or broken_svg_urls or broken_header_urls)
        if broken_links_found:
            log.write(f"❌ Broken links were found. Check the logs for details.\n")
        else:
            log.write(f"✅ All links are valid!\n")
    
    # Print results to console
    print(f"Check complete. See {log_file_with_timestamp} for details.")
    
    print(f"\nLog generated on: {timestamp}")
    print(f"{Colors.INFO}Runtime: {runtime_str}{Colors.ENDC}")
    print(f"Runtime duration: {runtime_duration}")
    print(f"Total broken absolute URLs: {len(broken_absolute_urls)}")
    print(f"Total broken relative URLs (without anchors): {len(broken_relative_urls_without_anchor)}")
    print(f"Total broken relative URLs (with anchors): {len(broken_relative_urls_with_anchor)}")
    print(f"Total OK absolute URLs: {len(ok_absolute_urls)}")
    print(f"Total OK relative URLs: {len(ok_relative_urls)}")
    print(f"Total broken root-relative URLs: {len(broken_root_relative_urls)}")
    print(f"Total OK root-relative URLs: {len(ok_root_relative_urls)}")
    print(f"Total broken image URLs: {len(broken_image_urls)}")
    print(f"Total OK image URLs: {len(ok_image_urls)}")
    print(f"Total broken SVG URLs: {len(broken_svg_urls)}")
    print(f"Total OK SVG URLs: {len(ok_svg_urls)}")
    print(f"Total broken header links: {len(broken_header_urls)}")
    print(f"Total OK header links: {len(ok_header_urls)}")
    
    # Update these sections to match log file format
    print(f"\n=== Broken Absolute URLs ({len(broken_absolute_urls)} links found) ===")
    if broken_absolute_urls:
        for url in broken_absolute_urls:
            print(f"{Colors.FAIL}{strip_ansi_escape_codes(url)}{Colors.ENDC}")
    else:
        print("No broken absolute URLs found.")
    
    print(f"\n=== Broken Relative URLs Without Anchors ({len(broken_relative_urls_without_anchor)} links found) ===")
    if broken_relative_urls_without_anchor:
        for url in broken_relative_urls_without_anchor:
            print(f"{Colors.FAIL}{strip_ansi_escape_codes(url)}{Colors.ENDC}")
    else:
        print("No broken relative URLs without anchors found.")
        
    print(f"\n=== Broken Relative URLs With Anchors ({len(broken_relative_urls_with_anchor)} links found) ===")
    if broken_relative_urls_with_anchor:
        for url in broken_relative_urls_with_anchor:
            print(f"{Colors.FAIL}{strip_ansi_escape_codes(url)}{Colors.ENDC}")
    else:
        print("No broken relative URLs with anchors found.")
        
    print(f"\n=== Broken Root-Relative URLs ({len(broken_root_relative_urls)} links found) ===")
    if broken_root_relative_urls:
        for url in broken_root_relative_urls:
            print(f"{Colors.FAIL}{strip_ansi_escape_codes(url)}{Colors.ENDC}")
    else:
        print("No broken root-relative URLs found.")

    print(f"\n=== Broken Image URLs ({len(broken_image_urls)} links found) ===")
    if broken_image_urls:
        for url in broken_image_urls:
            print(f"{Colors.FAIL}{strip_ansi_escape_codes(url)}{Colors.ENDC}")
    else:
        print("No broken image URLs found.")

    print(f"\n=== Broken SVG URLs ({len(broken_svg_urls)} links found) ===")
    if broken_svg_urls:
        for url in broken_svg_urls:
            print(f"{Colors.FAIL}{strip_ansi_escape_codes(url)}{Colors.ENDC}")
    else:
        print("No broken SVG URLs found.")

    print(f"\n=== Broken Header Links ({len(broken_header_urls)} links found) ===")
    if broken_header_urls:
        for url in broken_header_urls:
            print(f"{Colors.FAIL}{strip_ansi_escape_codes(url)}{Colors.ENDC}")
    else:
        print("No broken header links found.")

    print(f"\n=== OK Absolute URLs ({len(ok_absolute_urls)} links found) ===")
    if ok_absolute_urls:
        for url in ok_absolute_urls:
            print(f"{Colors.OKGREEN}{strip_ansi_escape_codes(url)}{Colors.ENDC}")
    else:
        print("No absolute URLs found.")

    print(f"\n=== OK Relative URLs ({len(ok_relative_urls)} links found) ===")
    if ok_relative_urls:
        for url in ok_relative_urls:
            print(f"{Colors.OKGREEN}{strip_ansi_escape_codes(url)}{Colors.ENDC}")
    else:
        print("No relative URLs found.")

    print(f"\n=== OK Root-Relative URLs ({len(ok_root_relative_urls)} links found) ===")
    if ok_root_relative_urls:
        for url in ok_root_relative_urls:
            print(f"{Colors.OKGREEN}{strip_ansi_escape_codes(url)}{Colors.ENDC}")
    else:
        print("No root-relative URLs found.")

    print(f"\n=== OK Image URLs ({len(ok_image_urls)} links found) ===")
    if ok_image_urls:
        for url in ok_image_urls:
            print(f"{Colors.OKGREEN}{strip_ansi_escape_codes(url)}{Colors.ENDC}")
    else:
        print("No image URLs found.")

    print(f"\n=== OK SVG URLs ({len(ok_svg_urls)} links found) ===")
    if ok_svg_urls:
        for url in ok_svg_urls:
            print(f"{Colors.OKGREEN}{strip_ansi_escape_codes(url)}{Colors.ENDC}")
    else:
        print("No SVG URLs found.")

    print(f"\n=== OK Header Links ({len(ok_header_urls)} links found) ===")
    if ok_header_urls:
        for url in ok_header_urls:
            print(f"{Colors.OKGREEN}{strip_ansi_escape_codes(url)}{Colors.ENDC}")
    else:
        print("No header links found.")

    # Print modernized summary table with improved title and color coding
    total_broken = (len(broken_absolute_urls) + 
                    len(broken_relative_urls_with_anchor) + 
                    len(broken_relative_urls_without_anchor) + 
                    len(broken_root_relative_urls) + 
                    len(broken_image_urls) + 
                    len(broken_svg_urls) + 
                    len(broken_header_urls))
    
    total_ok = len(ok_absolute_urls) + len(ok_relative_urls) + len(ok_root_relative_urls) + len(ok_image_urls) + len(ok_svg_urls) + len(ok_header_urls)
    total_links = total_broken + total_ok
    
    # Enhanced title with borders - keep this one cyan
    print(f"\n{Colors.INFO}═════════════════════════════════════════════════════════{Colors.ENDC}")
    print(f"{Colors.INFO}📊  LINK VALIDATION SUMMARY ({total_links} links checked){Colors.ENDC}")
    print(f"{Colors.INFO}═════════════════════════════════════════════════════════{Colors.ENDC}")
    print()
    
    # Always show broken links section if there are any broken links
    if total_broken > 0:
        print(f"{Colors.FAIL}❌  BROKEN LINKS: {total_broken}{Colors.ENDC}")
        # Only show categories that actually have broken links
        for category, count in broken_types:
            print(f"{Colors.FAIL}   • {category}: {count}{Colors.ENDC}")
        print()
    else:
        print(f"{Colors.OKGREEN}✅  BROKEN LINKS: 0 (All links are valid!){Colors.ENDC}")
        print()
        
    # Show categories with no links found
    if no_links_types:
        print(f"{Colors.NEUTRAL}📭  NO LINKS FOUND: {len(no_links_types)}{Colors.ENDC}")
        for category, _ in no_links_types:
            print(f"{Colors.NEUTRAL}   • {category}{Colors.ENDC}")
        print()
    
    # Show categories with no broken links but with OK links - use SPECIAL color (magenta)
    if zero_broken_types:
        print(f"{Colors.SPECIAL}🔍  CATEGORIES WITH NO BROKEN LINKS: {len(zero_broken_types)}{Colors.ENDC}")
        for category, count in zero_broken_types:
            print(f"{Colors.SPECIAL}   • {category}: {count} OK links{Colors.ENDC}")
        print()
            
    # Keep this green for consistency with checkmarks
    print(f"{Colors.OKGREEN}✅  OK LINKS: {total_ok}{Colors.ENDC}")
    print()

    # Add runtime to console summary with emoji - use the same color as the section headers
    print(f"{Colors.INFO}⏱️  RUNTIME: {runtime_str}{Colors.ENDC}")
    print()

    # Determine if any broken links were found
    broken_links_found = bool(broken_absolute_urls or broken_relative_urls_with_anchor or broken_relative_urls_without_anchor or broken_root_relative_urls or broken_image_urls or broken_svg_urls or broken_header_urls)

    # Add a message about where the log file is saved - use the same color as the section headers
    print(f"{Colors.INFO}📄 FULL LOGS: {log_file_with_timestamp}{Colors.ENDC}")
    print()

    # Exit with appropriate code and final conclusion
    if broken_links_found:
        print(f"{Colors.FAIL}❌  Broken links were found. Check the logs for details.{Colors.ENDC}")
        sys.exit(1)  # Exit code 1 signals that broken links were found
    else:
        print(f"{Colors.OKGREEN}✅  All links are valid!{Colors.ENDC}")
        sys.exit(0)  # Exit code 0 signals that all links are valid

if __name__ == "__main__":
    main()