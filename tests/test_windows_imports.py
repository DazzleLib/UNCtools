#!/usr/bin/env python3
"""
Tests for the unctools.windows module imports.

This test script specifically checks the import behavior of Windows-specific modules
to ensure they're properly handled on both Windows and non-Windows platforms.
"""

import os
import sys
import logging
import importlib
from pathlib import Path
from unittest import mock

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import test framework
from tests.test_framework import (
    TestSuite, assert_true, assert_false, assert_equal, 
    assert_not_equal, assert_is_none, assert_is_not_none,
    skip_if_not_windows, skip_if_windows, skip_if_no_module,
    run_test_suites
)

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_module_imports():
    """Test basic module import behavior."""
    # Test importing the unctools package
    import unctools
    assert_is_not_none(unctools, "unctools package should be importable")
    
    # Test importing core modules
    from unctools import converter, detector
    assert_is_not_none(converter, "converter module should be importable")
    assert_is_not_none(detector, "detector module should be importable")
    
    # Test importing utility modules
    from unctools.utils import compat, logger, validation
    assert_is_not_none(compat, "compat module should be importable")
    assert_is_not_none(logger, "logger module should be importable")
    assert_is_not_none(validation, "validation module should be importable")

@skip_if_not_windows
def test_windows_module_imports():
    """Test Windows-specific module imports on Windows."""
    # Test importing the windows module
    import unctools.windows
    assert_is_not_none(unctools.windows, "windows module should be importable on Windows")
    
    # Test importing Windows-specific modules
    from unctools.windows import registry, network, security
    assert_is_not_none(registry, "registry module should be importable on Windows")
    assert_is_not_none(network, "network module should be importable on Windows")
    assert_is_not_none(security, "security module should be importable on Windows")
    
    # Test main API functions are available
    assert_is_not_none(unctools.fix_security_zone, "fix_security_zone should be available")
    assert_is_not_none(unctools.add_to_intranet_zone, "add_to_intranet_zone should be available")

@skip_if_windows
def test_windows_module_imports_non_windows():
    """Test Windows-specific module imports on non-Windows platforms."""
    # Test importing the windows module
    # This should succeed but provide stub functions
    import unctools.windows
    assert_is_not_none(unctools.windows, "windows module should be importable on non-Windows")
    
    # Test that stub functions are provided
    assert_is_not_none(unctools.fix_security_zone, "fix_security_zone stub should be available")
    assert_is_not_none(unctools.add_to_intranet_zone, "add_to_intranet_zone stub should be available")
    
    # Test that stub functions return False
    assert_false(unctools.fix_security_zone("server"), 
               "fix_security_zone stub should return False")
    assert_false(unctools.add_to_intranet_zone("server"), 
               "add_to_intranet_zone stub should return False")

def test_win32net_availability():
    """Test win32net module availability checking."""
    # Function to check if a module can be imported
    def can_import(module_name):
        try:
            importlib.import_module(module_name)
            return True
        except ImportError:
            return False
    
    # Check if win32net can be imported
    win32net_available = can_import('win32net')
    
    # Import converter module
    import unctools.converter
    
    # Check HAVE_WIN32NET flag
    if os.name == 'nt' and win32net_available:
        # Should be True on Windows with win32net installed
        assert_true(unctools.converter.HAVE_WIN32NET, 
                  "HAVE_WIN32NET should be True on Windows with win32net installed")
    else:
        # Should be False on non-Windows or without win32net
        assert_false(unctools.converter.HAVE_WIN32NET, 
                   "HAVE_WIN32NET should be False on non-Windows or without win32net")
    
    # Test refresh_mappings behavior
    mappings = unctools.converter.refresh_mappings()
    assert_is_not_none(mappings, "refresh_mappings should not return None")
    assert_equal(type(mappings), dict, "refresh_mappings should return a dictionary")

def test_windows_fallbacks():
    """Test fallback behavior for Windows-specific functionality."""
    # Import necessary modules
    import unctools.converter
    import unctools.detector
    
    # Create a UNCConverter instance
    converter = unctools.converter.UNCConverter()
    
    # Test converter methods
    local_path = converter.convert_to_local("\\\\server\\share\\file.txt")
    assert_is_not_none(local_path, "convert_to_local should not return None")
    
    unc_path = converter.convert_to_unc("Z:\\file.txt")
    assert_is_not_none(unc_path, "convert_to_unc should not return None")
    
    # Test detector functions
    is_unc = unctools.detector.is_unc_path("\\\\server\\share\\file.txt")
    assert_true(is_unc, "is_unc_path should work")
    
    path_type = unctools.detector.classify_path_origin("\\\\server\\share\\file.txt")
    assert_equal(path_type, unctools.detector.PATH_TYPE_UNC,
                "classify_path_origin should identify UNC paths")

def test_module_import_warnings():
    """Test that no unexpected import warnings are generated."""
    # Import logging to capture warnings
    import io
    import logging
    
    # Create a string IO object to capture log output
    log_capture = io.StringIO()
    
    # Configure logging to capture debug messages
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    
    logger = logging.getLogger("unctools")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    
    # Force reload of modules to generate import messages
    import importlib
    for module_name in [
        'unctools.converter', 
        'unctools.detector', 
    ]:
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
    
    # Get captured log
    log_output = log_capture.getvalue()
    
    # Check for specific warning messages
    if os.name != 'nt':
        # On non-Windows, we expect no win32net warnings
        assert_false("win32net module not available" in log_output, 
                   "No win32net warnings should be shown on non-Windows")
    
    # Unexpected warnings
    assert_false("Failed to get network mappings" in log_output, 
               "No 'Failed to get network mappings' warnings should be shown")
    
    # Clean up
    logger.removeHandler(handler)

def run_tests():
    """Run all Windows import tests."""
    suite = TestSuite("UNCtools Windows Import Tests")
    
    # Add tests
    suite.add_test(test_module_imports)
    suite.add_test(test_windows_module_imports)
    suite.add_test(test_windows_module_imports_non_windows)
    suite.add_test(test_win32net_availability)
    suite.add_test(test_windows_fallbacks)
    suite.add_test(test_module_import_warnings)
    
    # Run suite
    run_test_suites([suite])

if __name__ == "__main__":
    run_tests()
