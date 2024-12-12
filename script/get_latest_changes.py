#!/usr/bin/env python
import re
import sys
from pathlib import Path
from string import Template

CHANGELOG_PATH = Path("CHANGELOG.md")
LATEST_CHANGES_PATTERN = re.compile(
    r"(## (?P<version>\d+\.\d+\.\d+) \(\d{4}-\d{2}-\d{2}\)\n\n(?P<content>.+?))(?=\n\n## |\Z)",
    re.DOTALL,
)

CHANGE_TEMPLATE = Template(
    """
# $version

## What's changed

$content
    """
)


def extract_latest_changes() -> str:
    """Extract latest version changes to create release message."""
    changelog_content = CHANGELOG_PATH.read_text()
    latest_changes_match = LATEST_CHANGES_PATTERN.search(changelog_content)

    if not latest_changes_match:
        sys.exit(-1)

    version = latest_changes_match.group("version")
    content = latest_changes_match.group("content")

    return CHANGE_TEMPLATE.substitute(version=version, content=content)


if __name__ == "__main__":
    print(extract_latest_changes())
