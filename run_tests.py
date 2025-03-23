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
    )
    cov.start()

    start_time = time.time()
    
    # Discover and run tests
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(test_dir, pattern=pattern)
    
    if parallel and sys.platform != 'win32':  # Parallel execution not well supported on Windows
        cpu_count = multiprocessing.cpu_count()
        worker_count = max(2, cpu_count - 1)  # Leave one CPU free
        runner = unittest.TextTestRunner(verbosity=2)
        
        print(f"Running tests in parallel using {worker_count} workers...\n")
        
        # Use concurrent.futures for parallel test execution
        import concurrent.futures
        
        # Split the test suite into individual test cases
        test_cases = []
        for suite in test_suite:
            for test_case in suite:
                test_cases.append(test_case)
        
        # Run tests in parallel
        with concurrent.futures.ProcessPoolExecutor(max_workers=worker_count) as executor:
            futures = [executor.submit(runner.run, [test_case]) for test_case in test_cases]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Aggregate results
        failures = []
        errors = []
        tests_run = 0
        skipped = []
        
        for result in results:
            failures.extend(result.failures)
            errors.extend(result.errors)
            tests_run += result.testsRun
            if hasattr(result, 'skipped'):
                skipped.extend(result.skipped)
        
        # Create a mock TestResult object to return
        mock_result = unittest.TestResult()
        mock_result.failures = failures
        mock_result.errors = errors
        mock_result.testsRun = tests_run
        if hasattr(mock_result, 'skipped'):
            mock_result.skipped = skipped
        
        result = mock_result
    else:
        # Run tests sequentially
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(test_suite)
    
    elapsed_time = time.time() - start_time
    
    # Stop coverage measurement
    cov.stop()
    cov.save()
    
    if show_report:
        print(f'\nTest Run Completed in {elapsed_time:.2f} seconds')
        print(f'Tests Run: {result.testsRun}')
        print(f'Errors: {len(result.errors)}')
        print(f'Failures: {len(result.failures)}')
        if hasattr(result, 'skipped'):
            print(f'Skipped: {len(result.skipped)}')
        
        print('\nCoverage Summary:')
        cov.report()
    
    # Generate HTML report
    if generate_html:
        html_dir = 'coverage_html'
        cov.html_report(directory=html_dir)
        print(f"\nHTML coverage report generated in {os.path.abspath(html_dir)}")
    
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