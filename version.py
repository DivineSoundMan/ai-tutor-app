"""
App version information.

Follows semantic versioning: MAJOR.MINOR.PATCH
- MAJOR: breaking changes (new UI layout, API changes)
- MINOR: new features (e.g. admin service control, versioning)
- PATCH: bug fixes (e.g. Ollama auto-start fix)
"""

import os
import subprocess

APP_VERSION = os.environ.get("APP_VERSION", "1.1.0")
BUILD_DATE = "2026-02-15"


def get_git_hash() -> str:
    """Return short git commit hash, or empty string if unavailable."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            timeout=3,
        ).decode().strip()
    except Exception:
        return ""


GIT_HASH = get_git_hash()

VERSION_STRING = f"v{APP_VERSION}"
if GIT_HASH:
    VERSION_STRING += f" ({GIT_HASH})"
