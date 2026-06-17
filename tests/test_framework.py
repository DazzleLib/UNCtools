"""
Test framework for UNCtools.

This module provides common utilities and fixtures for testing UNCtools.
"""

import os
import sys
import logging
import platform
from typing import Dict, List, Tuple, Any, Optional, Callable

# Configure test logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class TestResult:
    """Container for test results."""

    __test__ = False  # custom-runner container, not a pytest test class
    
    def __init__(self):
        self.passed = []
        self.failed = []
        self.skipped = []
        self.total = 0
    
    def add_pass(self, test_name: str, message: Optional[str] = None):
        """Add a passed test."""
        self.passed.append((test_name, message))
        self.total += 1
    
    def add_fail(self, test_name: str, message: Optional[str] = None):
        """Add a failed test."""
        self.failed.append((test_name, message))
        self.total += 1
    
    def add_skip(self, test_name: str, message: Optional[str] = None):
        """Add a skipped test."""
        self.skipped.append((test_name, message))
        self.total += 1
    
    def get_summary(self) -> str:
        """Get a summary of the test results."""
        passed = len(self.passed)
        failed = len(self.failed)
        skipped = len(self.skipped)
        
        summary = [
            f"Tests run: {self.total}",
            f"Passed: {passed} ({passed/self.total*100:.1f}% of total)" if self.total > 0 else "Passed: 0 (0.0%)",
            f"Failed: {failed} ({failed/self.total*100:.1f}% of total)" if self.total > 0 else "Failed: 0 (0.0%)",
            f"Skipped: {skipped} ({skipped/self.total*100:.1f}% of total)" if self.total > 0 else "Skipped: 0 (0.0%)"
        ]
        
        return "\n".join(summary)
    
    def is_success(self) -> bool:
        """Check if all tests passed."""
        return len(self.failed) == 0

class TestSuite:
    """A suite of tests."""

    __test__ = False  # custom standalone runner, not a pytest test class
    
    def __init__(self, name: str):
        self.name = name
        self.tests = []
        self.setup_fn = None
        self.teardown_fn = None
    
    def add_test(self, fn: Callable, name: Optional[str] = None):
        """Add a test function to the suite."""
        test_name = name or fn.__name__
        self.tests.append((test_name, fn))
    
    def set_setup(self, fn: Callable):
        """Set the setup function for the suite."""
        self.setup_fn = fn
    
    def set_teardown(self, fn: Callable):
        """Set the teardown function for the suite."""
        self.teardown_fn = fn
    
    def run(self) -> TestResult:
        """Run all tests in the suite."""
        print(f"\n[TEST SUITE] {self.name}")
        print("=" * 80)
        
        result = TestResult()
        
        # Run tests
        for test_name, test_fn in self.tests:
            print(f"[TEST] {test_name}... ", end="")
            
            # Run setup if defined
            setup_data = None
            try:
                if self.setup_fn:
                    setup_data = self.setup_fn()
            except Exception as e:
                print(f"FAIL (setup error: {e})")
                result.add_fail(test_name, f"Setup error: {e}")
                continue
            
            # Run test
            try:
                if setup_data is not None:
                    test_fn(setup_data)
                else:
                    test_fn()
                print("PASS")
                result.add_pass(test_name)
            except SkipTest as e:
                print(f"SKIP ({e})")
                result.add_skip(test_name, str(e))
            except AssertionError as e:
                print(f"FAIL (assertion: {e})")
                result.add_fail(test_name, f"Assertion error: {e}")
            except Exception as e:
                print(f"FAIL (error: {e})")
                result.add_fail(test_name, f"Error: {e}")
            
            # Run teardown if defined
            try:
                if self.teardown_fn:
                    if setup_data is not None:
                        self.teardown_fn(setup_data)
                    else:
                        self.teardown_fn()
            except Exception as e:
                print(f"Warning: Teardown error: {e}")
        
        # Print summary
        print("\nSummary:")
        print(result.get_summary())
        
        return result

class SkipTest(Exception):
    """Exception to skip a test."""
    pass

def skip_if_not_windows(fn):
    """Decorator to skip a test if not running on Windows."""
    def wrapper(*args, **kwargs):
        if os.name != 'nt':
            try:
                import pytest
                pytest.skip("Test only runs on Windows")
            except ImportError:
                raise SkipTest("Test only runs on Windows")
        return fn(*args, **kwargs)
    return wrapper

def skip_if_windows(fn):
    """Decorator to skip a test if running on Windows."""
    def wrapper(*args, **kwargs):
        if os.name == 'nt':
            try:
                import pytest
                pytest.skip("Test only runs on non-Windows platforms")
            except ImportError:
                raise SkipTest("Test only runs on non-Windows platforms")
        return fn(*args, **kwargs)
    return wrapper

def skip_if_no_module(module_name):
    """Decorator to skip a test if a module is not available."""
    def decorator(fn):
        def wrapper(*args, **kwargs):
            try:
                __import__(module_name)
            except ImportError:
                try:
                    import pytest
                    pytest.skip(f"Required module {module_name} not available")
                except ImportError:
                    raise SkipTest(f"Required module {module_name} not available")
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def assert_true(value, message=None):
    """Assert that a value is True."""
    if not value:
        raise AssertionError(message or f"Expected True, got {value}")

def assert_false(value, message=None):
    """Assert that a value is False."""
    if value:
        raise AssertionError(message or f"Expected False, got {value}")

def assert_equal(a, b, message=None):
    """Assert that two values are equal."""
    if a != b:
        raise AssertionError(message or f"Expected {a} == {b}")

def assert_not_equal(a, b, message=None):
    """Assert that two values are not equal."""
    if a == b:
        raise AssertionError(message or f"Expected {a} != {b}")

def assert_is_none(value, message=None):
    """Assert that a value is None."""
    if value is not None:
        raise AssertionError(message or f"Expected None, got {value}")

def assert_is_not_none(value, message=None):
    """Assert that a value is not None."""
    if value is None:
        raise AssertionError(message or "Expected not None, got None")

def assert_raises(exception_type, callable_obj, *args, **kwargs):
    """Assert that a callable raises an exception."""
    try:
        callable_obj(*args, **kwargs)
    except exception_type:
        return
    except Exception as e:
        raise AssertionError(f"Expected {exception_type.__name__}, got {type(e).__name__}: {e}")
    raise AssertionError(f"Expected {exception_type.__name__}, no exception raised")

def get_platform_info():
    """Get information about the current platform."""
    return {
        "os": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "python": platform.python_version(),
        "architecture": platform.machine(),
        "processor": platform.processor()
    }

def run_test_suites(suites):
    """Run multiple test suites."""
    print("\n===== UNCtools Test Framework =====")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {platform.python_version()}")
    print("Running test suites...\n")
    
    total_results = {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "total": 0
    }
    
    all_passed = True
    
    for suite in suites:
        result = suite.run()
        
        total_results["passed"] += len(result.passed)
        total_results["failed"] += len(result.failed)
        total_results["skipped"] += len(result.skipped)
        total_results["total"] += result.total
        
        if not result.is_success():
            all_passed = False
    
    print("\n===== Test Results =====")
    print(f"Total tests: {total_results['total']}")
    print(f"Passed: {total_results['passed']} ({total_results['passed']/total_results['total']*100:.1f}% of total)" if total_results['total'] > 0 else "Passed: 0 (0.0%)")
    print(f"Failed: {total_results['failed']} ({total_results['failed']/total_results['total']*100:.1f}% of total)" if total_results['total'] > 0 else "Failed: 0 (0.0%)")
    print(f"Skipped: {total_results['skipped']} ({total_results['skipped']/total_results['total']*100:.1f}% of total)" if total_results['total'] > 0 else "Skipped: 0 (0.0%)")
    
    if all_passed:
        print("\nALL TESTS PASSED!")
        return 0
    else:
        print("\nSOME TESTS FAILED!")
        return 1