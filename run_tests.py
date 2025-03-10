#!/usr/bin/env python
"""
Test runner for GitHub Contribution Hack

This script runs all tests and generates a coverage report.
"""
import os
import sys
import unittest
import coverage

def run_tests_with_coverage():
    """Run all tests with coverage reporting"""
    # Start coverage measurement
    cov = coverage.Coverage(
        source=['mcp_integration.py', 'main.py'],
        omit=['*/__pycache__/*', '*/tests/*', '*/venv/*'],
    )
    cov.start()

    # Discover and run tests
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Stop coverage measurement and report
    cov.stop()
    cov.save()
    
    print('\nCoverage Summary:')
    cov.report()
    
    # Generate HTML report
    cov.html_report(directory='coverage_html')
    print(f"\nHTML coverage report generated in {os.path.abspath('coverage_html')}")
    
    return result

if __name__ == '__main__':
    print("Running GitHub Contribution Hack tests with coverage...\n")
    
    result = run_tests_with_coverage()
    
    # Return non-zero exit code if tests failed
    if not result.wasSuccessful():
        sys.exit(1) 