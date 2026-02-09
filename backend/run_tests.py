#!/usr/bin/env python
"""
Simple test runner script for StudyNotesManager backend tests.
"""
import sys
import subprocess
import argparse


def run_tests(test_type="all", verbose=False, coverage=False):
    """
    Run tests using pytest.

    Args:
        test_type: Type of tests to run (all, unit, integration, e2e)
        verbose: Enable verbose output
        coverage: Generate coverage report
    """
    cmd = ["pytest"]

    # Add marker filter
    if test_type != "all":
        cmd.extend(["-m", test_type])

    # Add verbose flag
    if verbose:
        cmd.append("-v")

    # Add coverage
    if coverage:
        cmd.extend(["--cov=app", "--cov-report=html", "--cov-report=term"])

    # Run tests
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run StudyNotesManager tests")
    parser.add_argument(
        "test_type",
        nargs="?",
        default="all",
        choices=["all", "unit", "integration", "e2e"],
        help="Type of tests to run"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "-c", "--coverage",
        action="store_true",
        help="Generate coverage report"
    )

    args = parser.parse_args()

    exit_code = run_tests(args.test_type, args.verbose, args.coverage)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
