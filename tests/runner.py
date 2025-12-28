"""Test runner for the analytics dashboard.

This module provides functions to run the test suite and report results
in the Streamlit dashboard.
"""
import subprocess
import sys
from pathlib import Path
from typing import Tuple, List


def run_tests() -> Tuple[bool, str]:
    """
    Run pytest test suite and return results.

    Returns:
        Tuple of (success: bool, output: str) where success is True if all tests passed
    """
    project_root = Path(__file__).parent.parent
    test_dir = project_root / "tests"

    if not test_dir.exists():
        return True, "No tests directory found"

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_dir), "-q", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(project_root),
        )

        output = result.stdout + result.stderr
        success = result.returncode == 0

        return success, output

    except subprocess.TimeoutExpired:
        return False, "Test suite timed out after 30 seconds"
    except Exception as e:
        return False, f"Error running tests: {str(e)}"


def validate_imports() -> Tuple[bool, str]:
    """
    Validate that all required imports are available.

    Returns:
        Tuple of (success: bool, message: str)
    """
    required_packages = [
        "streamlit",
        "pandas",
        "numpy",
        "kloppy",
        "requests",
        "rapidfuzz",
        "matplotlib",
        "plotly",
        "mplsoccer",
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    if missing:
        return False, f"Missing required packages: {', '.join(missing)}"

    return True, "All required packages available"
