#!/usr/bin/env python3
"""
Test runner script that properly separates test output from log output.
"""
import unittest
import logging
import sys
import os
import io

def run_tests():
    """Run all tests with proper logging configuration."""
    # Temporarily redirect logging to a string buffer during test execution
    log_capture = io.StringIO()
    root_logger = logging.getLogger()
    
    # Save original handlers and level
    original_handlers = root_logger.handlers.copy()
    original_level = root_logger.level
    
    # Configure root logger to capture all logs to our buffer
    root_logger.handlers = []
    handler = logging.StreamHandler(log_capture)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    
    # Discover and run tests
    print("Running tests...\n")
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    test_result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    
    # Print captured logs with clear separation
    print("\n" + "="*80)
    print("LOG OUTPUT:")
    print("="*80)
    print(log_capture.getvalue())
    
    # Restore original logging configuration
    root_logger.handlers = original_handlers
    root_logger.setLevel(original_level)
    
    return test_result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)