#!/usr/bin/env python
"""
Test runner for GitHub Contribution Hack

This script runs all tests and generates a coverage report.
"""
import os
import sys
import argparse
import unittest
import coverage
import time
from typing import Dict, Any, List, Optional
import multiprocessing

def run_tests_with_coverage(
    show_report: bool = True,
    generate_html: bool = True,
    parallel: bool = True,
    test_dir: str = 'tests',
    source_files: Optional[List[str]] = None,
    pattern: str = 'test_*.py'
) -> unittest.TestResult:
    """Run all tests with coverage reporting
    
    Args:
        show_report: Whether to show the coverage report in the console
        generate_html: Whether to generate HTML coverage report
        parallel: Whether to run tests in parallel
        test_dir: Directory containing the tests
        source_files: List of source files to measure coverage for, defaults to main modules
        pattern: Pattern for discovering test files
    
    Returns:
        TestResult object containing test results
    """
    # Set default source files if none provided
    if source_files is None:
        source_files = ['mcp_integration.py', 'main.py', 'retry.py', 'error_handler.py']
    
    # Start coverage measurement
    cov = coverage.Coverage(
        source=source_files,
        omit=['*/__pycache__/*', '*/tests/*', '*/venv/*'],
        include=['*.py'],  # Include all Python files
        data_file='.coverage'
    )
    cov.start()

    start_time = time.time()
    
    # For proper coverage collection, use pytest for test running
    import pytest
    
    # Build pytest arguments
    pytest_args = ['-v', test_dir]
    
    # If parallel is enabled, add xdist arguments for parallelization
    if parallel and sys.platform != 'win32':  # Parallel execution not well supported on Windows
        try:
            import pytest_xdist
            cpu_count = multiprocessing.cpu_count()
            worker_count = max(2, cpu_count - 1)  # Leave one CPU free
            pytest_args.extend(['-xvs', f'-n={worker_count}'])
            print(f"Running tests in parallel using {worker_count} workers...\n")
        except ImportError:
            print("pytest-xdist not installed, running tests sequentially")
    
    # Capture the output of pytest in a result variable
    exit_code = pytest.main(pytest_args)
    
    # Create a mock TestResult to maintain compatibility
    result = unittest.TestResult()
    result.wasSuccessful = lambda: exit_code == 0
    result.testsRun = -1  # We don't know the exact count
    
    elapsed_time = time.time() - start_time
    
    # Stop coverage measurement
    cov.stop()
    cov.save()
    
    if show_report:
        print(f'\nTest Run Completed in {elapsed_time:.2f} seconds')
        try:
            print('\nCoverage Summary:')
            cov.report()
        except Exception as e:
            print(f"Error generating coverage report: {e}")
    
    # Generate HTML report
    if generate_html:
        try:
            html_dir = 'coverage_html'
            cov.html_report(directory=html_dir)
            print(f"\nHTML coverage report generated in {os.path.abspath(html_dir)}")
        except Exception as e:
            print(f"Error generating HTML coverage report: {e}")
    
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run GitHub Contribution Hack tests with coverage')
    parser.add_argument('--no-report', action='store_true', help='Do not show coverage report')
    parser.add_argument('--no-html', action='store_true', help='Do not generate HTML coverage report')
    parser.add_argument('--no-parallel', action='store_true', help='Do not run tests in parallel')
    parser.add_argument('--test-dir', default='tests', help='Directory containing tests')
    parser.add_argument('--pattern', default='test_*.py', help='Pattern for test discovery')
    parser.add_argument('--source', nargs='+', help='Source files to measure coverage for')
    args = parser.parse_args()
    
    print("Running GitHub Contribution Hack tests with coverage...\n")
    
    result = run_tests_with_coverage(
        show_report=not args.no_report,
        generate_html=not args.no_html,
        parallel=not args.no_parallel,
        test_dir=args.test_dir,
        source_files=args.source,
        pattern=args.pattern
    )
    
    # Return non-zero exit code if tests failed
    if not result.wasSuccessful():
        sys.exit(1) 