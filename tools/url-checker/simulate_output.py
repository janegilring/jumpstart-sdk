#!/usr/bin/env python3
"""
Script to simulate the output of url_checker.py without actually checking URLs.
This is useful for testing the output formatting and appearance.
"""

import random
from datetime import datetime, timedelta
from colorama import init, Fore, Style

# Initialize colorama for cross-platform color support
init(autoreset=True)

# ANSI color codes for terminal output (copied from url_checker.py)
class Colors:
    OKGREEN = '\033[92m'  # Green for success
    FAIL = '\033[91m'     # Red for errors
    INFO = '\033[96m'     # Cyan for neutral/informational
    NEUTRAL = '\033[93m'  # Yellow for "no links found" category
    SPECIAL = '\033[95m'  # Magenta for "categories with no broken links"
    ENDC = '\033[0m'

def simulate_url_checker_output():
    """Simulate the console output of the URL checker."""
    # Simulate timestamps and runtime
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    runtime_duration = timedelta(minutes=3, seconds=42)
    runtime_seconds = runtime_duration.total_seconds()
    runtime_str = f"{runtime_seconds/60:.2f} minutes ({runtime_duration})"
    
    # Simulate file counts
    files_checked = random.randint(50, 200)
    print(f"Starting URL check on {files_checked} files...")
    
    # Simulate URL extraction and checking
    for i in range(5):
        print(f"Processing Markdown file: /path/to/sample_{i}.md")
        print(f"Found {random.randint(2, 15)} URLs in Markdown file: /path/to/sample_{i}.md")
    
    print("...")  # Indicate more processing output is truncated
    
    # FIXED VALUES - Not random - to ensure consistent demonstrations
    # Always show specific categories in each section:
    # - SVG URLs: ALWAYS in NO LINKS FOUND
    # - Root-relative & Header links: ALWAYS in CATEGORIES WITH NO BROKEN LINKS
    # - Absolute, Relative, Image URLs: ALWAYS in BROKEN LINKS
    
    # Links with broken entries
    broken_absolute = 3            # Always have broken absolute URLs
    broken_relative_without = 2    # Always have broken relative URLs without anchors
    broken_relative_with = 1       # Always have broken relative URLs with anchors
    broken_image = 2               # Always have broken image URLs
    
    # Links with zero broken but some OK entries
    broken_root = 0                # No broken root-relative URLs
    broken_header = 0              # No broken header links
    ok_root = 10                   # Some OK root-relative URLs
    ok_header = 7                  # Some OK header links
    
    # Links with no entries at all
    broken_svg = 0                 # No broken SVG URLs
    ok_svg = 0                     # No OK SVG URLs

    # Other OK entries
    ok_absolute = random.randint(20, 50)
    ok_relative = random.randint(30, 70)
    ok_image = random.randint(10, 30)
    
    total_broken = (broken_absolute + broken_relative_with + broken_relative_without + 
                    broken_root + broken_image + broken_svg + broken_header)
    total_ok = ok_absolute + ok_relative + ok_root + ok_image + ok_svg + ok_header
    total_links = total_broken + total_ok
    
    log_file = f"logs/broken_urls_{timestamp}.log"
    
    # Generate consistent report data
    # Create lists to track each category type
    no_links_types = ["SVG URLs"]  # Always show SVG URLs in NO LINKS FOUND
    
    zero_broken_types = [         # Always show these in CATEGORIES WITH NO BROKEN LINKS
        f"Root-relative URLs: {ok_root} OK links",
        f"Header links: {ok_header} OK links"
    ]
    
    broken_types = [              # Always show these in BROKEN LINKS
        f"Absolute URLs: {broken_absolute}",
        f"Relative URLs without anchors: {broken_relative_without}",
        f"Relative URLs with anchors: {broken_relative_with}",
        f"Image URLs: {broken_image}"
    ]
    
    # Simulate the results output
    print(f"Check complete. See {log_file} for details.")
    
    print(f"\nLog generated on: {timestamp}")
    print(f"{Colors.INFO}Runtime: {runtime_str}{Colors.ENDC}")
    print(f"Runtime duration: {runtime_duration}")
    print(f"Total broken absolute URLs: {broken_absolute}")
    print(f"Total broken relative URLs (without anchors): {broken_relative_without}")
    print(f"Total broken relative URLs (with anchors): {broken_relative_with}")
    print(f"Total OK absolute URLs: {ok_absolute}")
    print(f"Total OK relative URLs: {ok_relative}")
    print(f"Total broken root-relative URLs: {broken_root}")
    print(f"Total OK root-relative URLs: {ok_root}")
    print(f"Total broken image URLs: {broken_image}")
    print(f"Total OK image URLs: {ok_image}")
    print(f"Total broken SVG URLs: {broken_svg}")
    print(f"Total OK SVG URLs: {ok_svg}")
    print(f"Total broken header links: {broken_header}")
    print(f"Total OK header links: {ok_header}")
    
    # Sample URL listings
    print(f"\n=== Broken Absolute URLs ({broken_absolute} links found) ===")
    if broken_absolute > 0:
        for i in range(min(3, broken_absolute)):
            print(f"{Colors.FAIL}[BROKEN ABSOLUTE] https://example.com/broken-link-{i} - Status Code: 404 (in file: /path/to/file_{i}.md){Colors.ENDC}")
        if broken_absolute > 3:
            print(f"{Colors.FAIL}... and {broken_absolute - 3} more broken absolute URLs{Colors.ENDC}")
    else:
        print("No broken absolute URLs found.")
    
    # More sample sections would follow - showing just a few for brevity
    print(f"\n=== OK Image URLs ({ok_image} links found) ===")
    if ok_image > 0:
        for i in range(min(3, ok_image)):
            print(f"{Colors.OKGREEN}[OK IMAGE] /path/to/images/image_{i}.png{Colors.ENDC}")
        if ok_image > 3:
            print(f"{Colors.OKGREEN}... and {ok_image - 3} more OK image URLs{Colors.ENDC}")
    else:
        print("No image URLs found.")
    
    # Summary section with emoji in different colors
    print(f"\n{Colors.INFO}═════════════════════════════════════════════════════════{Colors.ENDC}")
    print(f"{Colors.INFO}📊  LINK VALIDATION SUMMARY ({total_links} links checked){Colors.ENDC}")
    print(f"{Colors.INFO}═════════════════════════════════════════════════════════{Colors.ENDC}")
    print()
    
    # Always show broken links section if there are any broken links
    if total_broken > 0:
        print(f"{Colors.FAIL}❌  BROKEN LINKS: {total_broken}{Colors.ENDC}")
        for category in broken_types:
            print(f"{Colors.FAIL}   • {category}{Colors.ENDC}")
        print()
    else:
        print(f"{Colors.OKGREEN}✅  BROKEN LINKS: 0 (All links are valid!){Colors.ENDC}")
        print()
    
    # Show categories with no links found - just show the number without "categories"
    if no_links_types:
        print(f"{Colors.NEUTRAL}📭  NO LINKS FOUND: {len(no_links_types)}{Colors.ENDC}")
        for category in no_links_types:
            print(f"{Colors.NEUTRAL}   • {category}{Colors.ENDC}")
        print()
    
    # Show categories with no broken links but with OK links - use SPECIAL color (magenta)
    if zero_broken_types:
        print(f"{Colors.SPECIAL}🔍  CATEGORIES WITH NO BROKEN LINKS: {len(zero_broken_types)}{Colors.ENDC}")
        for category in zero_broken_types:
            print(f"{Colors.SPECIAL}   • {category}{Colors.ENDC}")
        print()
    
    # OK links count
    print(f"{Colors.OKGREEN}✅  OK LINKS: {total_ok}{Colors.ENDC}")
    print()

    # Add runtime to console summary with emoji - use the same color as the section headers
    print(f"{Colors.INFO}⏱️  RUNTIME: {runtime_str}{Colors.ENDC}")
    print()

    # Add a message about where the log file is saved - use the same color as the section headers
    print(f"{Colors.INFO}📄 FULL LOGS: {log_file}{Colors.ENDC}")
    print()

    # Exit message
    if total_broken > 0:
        print(f"{Colors.FAIL}❌  Broken links were found. Check the logs for details.{Colors.ENDC}")
    else:
        print(f"{Colors.OKGREEN}✅  All links are valid!{Colors.ENDC}")

if __name__ == "__main__":
    simulate_url_checker_output()
