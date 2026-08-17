#!/usr/bin/env bash
# ==============================================================================
# DigitalAgEdu Primary Release Documentation Validator
# ==============================================================================
set -euo pipefail

VERSION="1.0.0"

echo "=================================================="
echo "Validating DigitalAgEdu Release v${VERSION} Docs"
echo "=================================================="

# 1. Verify required project files
echo "[1/2] Verifying required documentation & governance files..."
REQUIRED_FILES=(
  "LICENSE"
  "README.md"
  "CONTRIBUTING.md"
  "CODE_OF_CONDUCT.md"
  "SECURITY.md"
  "CITATION.cff"
  "CHANGELOG.md"
  ".dockerignore"
  ".github/workflows/repository-health.yml"
  ".github/workflows/secret-scan.yml"
  ".github/ISSUE_TEMPLATE/bug_report.yml"
  ".github/ISSUE_TEMPLATE/feature_request.yml"
  ".github/ISSUE_TEMPLATE/config.yml"
  ".github/PULL_REQUEST_TEMPLATE.md"
  "docs/RELEASE_CHECKLIST.md"
  "docs/MAINTAINER_ROLES.md"
  "docs/RELEASE_NOTES.md"
)

for file in "${REQUIRED_FILES[@]}"; do
  if [ ! -f "$file" ]; then
    echo "[ERROR] Missing required file: $file"
    exit 1
  fi
  echo "  [OK] $file"
done

echo ""
echo "[2/2] Release Documentation Ready!"
echo "To publish this release tag, run:"
echo "  git tag -a v${VERSION} -m \"DigitalAgEdu Primary Release v${VERSION}\""
echo "  git push origin v${VERSION}"
echo "=================================================="
