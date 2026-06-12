#!/usr/bin/env python3
"""
Tests for the unctools.converter module using the test framework.
"""

import os
import sys
import logging
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import test framework
from tests.test_framework import (
    TestSuite, assert_true, assert_false, assert_equal, 
    assert_not_equal, assert_is_none, assert_is_not_none,
    skip_if_not_windows, skip_if_windows, skip_if_no_module,
    run_test_suites
)

# Import UNCtools
import unctools
from unctools.converter import (
    UNCConverter, convert_to_local, convert_to_unc,
    parse_unc_path, join_unc_path
)

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Test UNC paths
TEST_UNC_PATH = "\\\\server\\share\\folder\\file.txt"
TEST_LOCAL_PATH = "Z:\\folder\\file.txt"
TEST_SERVER = "server"
TEST_SHARE = "share"
TEST_REL_PATH = "folder\\file.txt"

def create_mock_mappings():
    """Create a UNCConverter with mock mappings."""
    # Create converter with refresh_on_init=False to avoid actual system calls
    converter = UNCConverter(refresh_on_init=False)
    
    # Set up mock mappings
    converter._mapping = {
        "\\\\server\\share": "Z:\\",
        "\\\\fileserver\\public": "Y:\\",
        "\\\\nas\\backup": "X:\\"
    }
    converter._reverse_mapping = {
        "Z:": "\\\\server\\share",
        "Y:": "\\\\fileserver\\public",
        "X:": "\\\\nas\\backup"
    }
    
    return converter

def test_converter_init():
    """Test UNCConverter initialization."""
    # Test with refresh_on_init=False
    converter = UNCConverter(refresh_on_init=False)
    assert_is_not_none(converter)
    assert_equal(converter._mapping, {})
    
    # Test with mock mappings
    converter = create_mock_mappings()
    assert_is_not_none(converter)
    assert_not_equal(converter._mapping, {})
    assert_equal(len(converter._mapping), 3)

def test_get_mappings():
    """Test get_mappings method."""
    converter = create_mock_mappings()
    mappings = converter.get_mappings()
    
    # Check mappings
    assert_equal(mappings, converter._mapping)
    
    # Ensure it's a copy
    mappings["test"] = "test"
    assert_true("test" not in converter.get_mappings())

def test_get_reverse_mappings():
    """Test get_reverse_mappings method."""
    converter = create_mock_mappings()
    mappings = converter.get_reverse_mappings()
    
    # Check mappings
    assert_equal(mappings, converter._reverse_mapping)
    
    # Ensure it's a copy
    mappings["test"] = "test"
    assert_true("test" not in converter.get_reverse_mappings())

def test_convert_to_local():
    """Test convert_to_local method."""
    converter = create_mock_mappings()
    
    # Test conversion of a UNC path
    result = converter.convert_to_local(TEST_UNC_PATH)
    assert_equal(result, Path(TEST_LOCAL_PATH))
    
    # Test with a path that doesn't match any mapping
    unmapped_path = "\\\\unknown\\share\\file.txt"
    result = converter.convert_to_local(unmapped_path)
    assert_equal(result, Path(unmapped_path))
    
    # Test with a local path (should return unchanged)
    local_path = "C:\\folder\\file.txt"
    result = converter.convert_to_local(local_path)
    assert_equal(result, Path(local_path))
    
    # Test with different path formats
    unc_with_slashes = "//server/share/folder/file.txt"
    result = converter.convert_to_local(unc_with_slashes)
    assert_equal(result, Path(TEST_LOCAL_PATH))

@pytest.mark.skipif(os.name != 'nt', reason="Windows-specific test - UNC paths and drive letters are Windows concepts")
def test_convert_to_unc():
    """Test convert_to_unc method."""
    converter = create_mock_mappings()
    
    # Test conversion of a local path
    result = converter.convert_to_unc(TEST_LOCAL_PATH)
    assert_equal(result, Path(TEST_UNC_PATH))
    
    # Test with a path that doesn't match any mapping
    unmapped_path = "C:\\folder\\file.txt"
    result = converter.convert_to_unc(unmapped_path)
    assert_equal(result, Path(unmapped_path))
    
    # Test with a UNC path (should return unchanged)
    result = converter.convert_to_unc(TEST_UNC_PATH)
    assert_equal(result, Path(TEST_UNC_PATH))
    
    # Test with drive letter variations
    result = converter.convert_to_unc("z:/folder/file.txt")
    assert_equal(result, Path(TEST_UNC_PATH))
    
    # Test with drive letter only
    result = converter.convert_to_unc("Z:")
    assert_equal(result, Path("\\\\server\\share"))

def test_module_functions():
    """Test module-level functions."""
    # These just test the function signatures/interfaces since they call the global converter
    
    # Test convert_to_local
    path = convert_to_local(TEST_UNC_PATH)
    assert_is_not_none(path)
    
    # Test convert_to_unc
    path = convert_to_unc(TEST_LOCAL_PATH)
    assert_is_not_none(path)
    
    # normalize_path was removed in 0.2.0 (D4) -- the explicit converts ARE the API

def test_parse_unc_path():
    """Test parse_unc_path function."""
    # Test with a valid UNC path
    result = parse_unc_path(TEST_UNC_PATH)
    assert_is_not_none(result)
    assert_equal(result, (TEST_SERVER, TEST_SHARE, TEST_REL_PATH))
    
    # Test with a UNC path with no relative path
    result = parse_unc_path("\\\\server\\share")
    assert_is_not_none(result)
    assert_equal(result, (TEST_SERVER, TEST_SHARE, ""))
    
    # Test with a non-UNC path
    result = parse_unc_path(TEST_LOCAL_PATH)
    assert_is_none(result)
    
    # Test with a UNC path using forward slashes
    result = parse_unc_path("//server/share/folder/file.txt")
    assert_is_not_none(result)
    assert_equal(result, (TEST_SERVER, TEST_SHARE, TEST_REL_PATH))

def test_join_unc_path():
    """Test join_unc_path function."""
    # Test with all components
    result = join_unc_path(TEST_SERVER, TEST_SHARE, TEST_REL_PATH)
    assert_equal(result, TEST_UNC_PATH)
    
    # Test without relative path
    result = join_unc_path(TEST_SERVER, TEST_SHARE)
    assert_equal(result, "\\\\server\\share")
    
    # Test with empty relative path
    result = join_unc_path(TEST_SERVER, TEST_SHARE, "")
    assert_equal(result, "\\\\server\\share")
    
    # Test with relative path that starts with backslash
    result = join_unc_path(TEST_SERVER, TEST_SHARE, "\\folder\\file.txt")
    assert_equal(result, TEST_UNC_PATH)

def run_tests():
    """Run all converter tests."""
    suite = TestSuite("UNCtools Converter Tests")
    
    # Add tests
    suite.add_test(test_converter_init)
    suite.add_test(test_get_mappings)
    suite.add_test(test_get_reverse_mappings)
    suite.add_test(test_convert_to_local)
    suite.add_test(test_convert_to_unc)
    suite.add_test(test_module_functions)
    suite.add_test(test_parse_unc_path)
    suite.add_test(test_join_unc_path)
    
    # Run suite
    run_test_suites([suite])

if __name__ == "__main__":
    run_tests()
