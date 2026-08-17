#!/usr/bin/env python3
"""
DigitalAgEdu Primary Release Validation Tool (v1.0.0)
Verifies that all required governance, security, and release documentation files are present.
"""

import os
import sys

VERSION = "1.0.0"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REQUIRED_FILES = [
    "LICENSE",
    "README.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "CITATION.cff",
    "CHANGELOG.md",
    ".dockerignore",
    ".github/workflows/repository-health.yml",
    ".github/workflows/secret-scan.yml",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/PULL_REQUEST_TEMPLATE.md",
    "docs/RELEASE_CHECKLIST.md",
    "docs/MAINTAINER_ROLES.md",
    "docs/RELEASE_NOTES.md",
]

def check_files():
    print(f"\n[1/2] Checking Required Governance & Release Documentation for v{VERSION}...")
    missing = []
    for rel_path in REQUIRED_FILES:
        full_path = os.path.join(REPO_ROOT, rel_path)
        if not os.path.exists(full_path):
            print(f"  [MISSING] {rel_path}")
            missing.append(rel_path)
        else:
            print(f"  [OK] {rel_path}")
            
    if missing:
        print(f"\n[FAILED] {len(missing)} required documentation files are missing.")
        return False
    print(f"  -> All {len(REQUIRED_FILES)} required documentation files verified successfully!")
    return True

def summary():
    print("\n[2/2] Release Readiness Summary:")
    print("  Version: " + VERSION)
    print("  Status:  Ready for Primary Release Tagging")
    print("\nTo tag and publish this release on GitHub, execute:")
    print(f"  git tag -a v{VERSION} -m \"DigitalAgEdu Primary Release v{VERSION}\"")
    print(f"  git push origin v{VERSION}\n")

def main():
    print(f"==================================================")
    print(f"DigitalAgEdu Release Documentation Validator (v{VERSION})")
    print(f"==================================================")
    
    files_ok = check_files()
    if not files_ok:
        sys.exit(1)
        
    summary()

if __name__ == "__main__":
    main()
