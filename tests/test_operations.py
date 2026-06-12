#!/usr/bin/env python3
"""
Tests for the unctools.operations module using the test framework.
"""

import os
import sys
import tempfile
import logging
import shutil
from pathlib import Path
from unittest import mock

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import test framework
from tests.test_framework import (
    TestSuite, assert_true, assert_false, assert_equal, 
    assert_not_equal, assert_is_none, assert_is_not_none,
    skip_if_not_windows, skip_if_windows, skip_if_no_module,
    run_test_suites, SkipTest
)

# Import UNCtools
import unctools
# 0.2.0 (STACK-MAP D7): content-I/O wrappers were deleted; survivors moved
# to their layer-correct homes. Tests import from the new locations.
from unctools.converter import (
    batch_convert, get_unc_path_elements, build_unc_path
)
from unctools.detector import (
    file_exists, is_path_accessible, find_accessible_path
)
from unctools.detector import is_unc_path, PATH_TYPE_UNC

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Test data
TEST_UNC_PATH = "\\\\server\\share\\folder\\file.txt"
TEST_LOCAL_PATH = "C:\\Users\\username\\Documents\\file.txt"

class TestEnvironment:
    """Manages a temporary test environment with files."""
    
    def __init__(self):
        """Initialize the test environment."""
        self.temp_dir = None
        self.test_files = []
        self.output_dir = None
    
    def setup(self):
        """Set up the test environment."""
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix='unctools_test_')
        
        # Create an output directory for copy tests
        self.output_dir = os.path.join(self.temp_dir, 'output')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create test files
        self._create_test_files()
        
        # Return self for convenience
        return self
    
    def teardown(self):
        """Clean up the test environment."""
        # Remove the temporary directory
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None
            self.test_files = []
            self.output_dir = None
    
    def _create_test_files(self):
        """Create test files in the temporary directory."""
        # Create files with different content
        file_paths = []
        
        # Create a simple text file
        text_file = os.path.join(self.temp_dir, 'text_file.txt')
        with open(text_file, 'w') as f:
            f.write('This is a test file.')
        file_paths.append(text_file)
        
        # Create a nested directory
        nested_dir = os.path.join(self.temp_dir, 'nested')
        os.makedirs(nested_dir, exist_ok=True)
        
        # Create a file in the nested directory
        nested_file = os.path.join(nested_dir, 'nested_file.txt')
        with open(nested_file, 'w') as f:
            f.write('This is a nested file.')
        file_paths.append(nested_file)
        
        # Create binary file
        binary_file = os.path.join(self.temp_dir, 'binary_file.bin')
        with open(binary_file, 'wb') as f:
            f.write(b'\x00\x01\x02\x03\x04')
        file_paths.append(binary_file)
        
        # Create multiple text files for batch operations
        #for i in range(3):
        #    batch_file = os.path.join(self.temp_dir, f'batch_file_{i}.txt')
        #    with open(batch_file, 'w') as f:
        #        f.write(f'This is batch file {i}.')
        #    file_paths.append(batch_file)
        
        # Store the file paths
        self.test_files = file_paths
        
        return file_paths

# Create test suite setup and teardown functions
def setup_test_environment():
    """Set up a test environment for tests."""
    env = TestEnvironment()
    return env.setup()

def teardown_test_environment(env=None):
    """Clean up the test environment."""
    if env:
        env.teardown()


def test_file_exists(env):
    """Test file_exists function."""
    # Test with an existing file
    test_file = env.test_files[0]
    assert_true(file_exists(test_file), "Existing file should be detected")
    
    # Test with a non-existent file
    non_existent = os.path.join(env.temp_dir, 'non_existent.txt')
    assert_false(file_exists(non_existent), "Non-existent file should not be detected")
    
    # Test with a directory
    assert_true(file_exists(env.temp_dir), "Directory should be detected as existing")
    
    # Test with convert_paths behavior
    # Mock convert_to_local and convert_to_unc to return alternate paths
    # and os.path.exists to return True for the converted path
    
    def mock_convert_to_local(path):
        return Path(str(path) + ".local")
    
    def mock_convert_to_unc(path):
        return Path(str(path) + ".unc")
    
    def mock_is_unc_path(path):
        path_str = str(path)  # Convert Path to string before checking
        return path_str.startswith("\\\\") or path_str.startswith("//")
    
    def mock_exists(path):
        return str(path).endswith(".local") or str(path).endswith(".unc")
    
    with mock.patch('unctools.converter.convert_to_local', side_effect=mock_convert_to_local), \
         mock.patch('unctools.converter.convert_to_unc', side_effect=mock_convert_to_unc), \
         mock.patch('unctools.detector.is_unc_path', side_effect=mock_is_unc_path), \
         mock.patch('os.path.exists', side_effect=mock_exists):
        
        # Test with a UNC path (should try convert_to_local)
        assert_true(file_exists(TEST_UNC_PATH, check_both_paths=True), 
                   "UNC path should be detected via local path conversion")
        
        # Test with a local path (should try convert_to_unc)
        assert_true(file_exists(TEST_LOCAL_PATH, check_both_paths=True), 
                   "Local path should be detected via UNC path conversion")


def test_batch_convert(env):
    """Test batch_convert function."""
    # Get a list of test files
    test_files = env.test_files[:3]  # Take the first 3 files
    
    # Mock convert_to_local and convert_to_unc to return predictable results
    def mock_convert_to_local(path):
        return Path(str(path) + ".local")
    
    def mock_convert_to_unc(path):
        return Path(str(path) + ".unc")
    
    with mock.patch('unctools.converter.convert_to_local', side_effect=mock_convert_to_local), \
         mock.patch('unctools.converter.convert_to_unc', side_effect=mock_convert_to_unc):
        
        # Test batch convert to UNC
        results = batch_convert([str(f) for f in test_files], to_unc=True)
        
        # Verify results
        assert_equal(len(results), len(test_files), 
                    "Should have results for all input files")
        
        for original, converted in results.items():
            assert_equal(converted, original + ".unc", 
                        f"Converted path for {original} should end with .unc")
        
        # Test batch convert to local
        results = batch_convert([str(f) for f in test_files], to_unc=False)
        
        # Verify results
        assert_equal(len(results), len(test_files), 
                    "Should have results for all input files")
        
        for original, converted in results.items():
            assert_equal(converted, original + ".local", 
                        f"Converted path for {original} should end with .local")



def test_get_unc_path_elements(env):
    """Test get_unc_path_elements function."""
    # Test with a valid UNC path
    result = get_unc_path_elements(TEST_UNC_PATH)
    assert_equal(result, ("server", "share", "folder\\file.txt"), 
                "Should extract the correct components")
    
    # Test with a UNC path without a relative path
    result = get_unc_path_elements("\\\\server\\share")
    assert_equal(result, ("server", "share", ""), 
                "Should extract the correct components without relative path")
    
    # Test with a non-UNC path
    result = get_unc_path_elements(TEST_LOCAL_PATH)
    assert_is_none(result, "Should return None for non-UNC path")
    
    # Test with forward slashes
    result = get_unc_path_elements("//server/share/folder/file.txt")
    assert_equal(result, ("server", "share", "folder/file.txt"), 
                "Should extract the correct components with forward slashes")

def test_build_unc_path(env=None):
    """Test build_unc_path function."""
    # Note: This function doesn't need the env parameter but should accept it
    # for consistency with other test functions.
    
    # Test with all components
    result = build_unc_path("server", "share", "folder\\file.txt")
    assert_equal(result, "\\\\server\\share\\folder\\file.txt", 
                "Should build the correct UNC path")
    
    # Test without relative path
    result = build_unc_path("server", "share")
    assert_equal(result, "\\\\server\\share", 
                "Should build the correct UNC path without relative path")
    
    # Test with empty relative path
    result = build_unc_path("server", "share", "")
    assert_equal(result, "\\\\server\\share", 
                "Should build the correct UNC path with empty relative path")
    
    # Test with relative path that starts with backslash
    result = build_unc_path("server", "share", "\\folder\\file.txt")
    assert_equal(result, "\\\\server\\share\\folder\\file.txt", 
                "Should build the correct UNC path and handle leading backslash")

def test_is_path_accessible(env):
    """Test is_path_accessible function."""
    # Test with an accessible file
    test_file = env.test_files[0]
    assert_true(is_path_accessible(test_file), "File should be accessible")
    
    # Test with an accessible directory
    assert_true(is_path_accessible(env.temp_dir), "Directory should be accessible")
    
    # Test with a non-existent file
    non_existent = os.path.join(env.temp_dir, 'non_existent.txt')
    assert_false(is_path_accessible(non_existent), "Non-existent file should not be accessible")
    
    # Test with convert_paths behavior
    # Mock conversion and path access functions
    def mock_convert_to_local(path):
        return Path(env.test_files[0])  # Return a valid file
    
    def mock_convert_to_unc(path):
        return Path(env.test_files[0])  # Return a valid file
    
    def mock_is_unc_path(path):
        path_str = str(path)
        return path_str.startswith("\\\\") or path_str.startswith("//")
    
    with mock.patch('unctools.converter.convert_to_local', side_effect=mock_convert_to_local), \
         mock.patch('unctools.converter.convert_to_unc', side_effect=mock_convert_to_unc), \
         mock.patch('unctools.detector.is_unc_path', side_effect=mock_is_unc_path):
        
        # Test with a UNC path (should try convert_to_local)
        assert_true(is_path_accessible(TEST_UNC_PATH, check_both_paths=True), 
                   "UNC path should be accessible after conversion")
        
        # Test with a non-UNC path (should try convert_to_unc)
        assert_true(is_path_accessible(non_existent, check_both_paths=True), 
                   "Path should be accessible after conversion")

def test_find_accessible_path(env):
    """Test find_accessible_path function."""
    # Test with an accessible file
    test_file = env.test_files[0]
    path = find_accessible_path(test_file)
    assert_is_not_none(path, "Accessible path should be found")
    assert_equal(str(path), test_file, "Found path should match the original")
    
    # Test with a non-existent file
    non_existent = os.path.join(env.temp_dir, 'non_existent.txt')
    
    # Mock conversion and path access functions
    def mock_convert_to_local(path):
        return Path(env.test_files[0])  # Return a valid file
    
    def mock_convert_to_unc(path):
        return Path(env.test_files[0])  # Return a valid file
    
    def mock_is_unc_path(path):
        path_str = str(path)
        return path_str.startswith("\\\\") or path_str.startswith("//")
    
    def mock_is_path_accessible(path, check_both_paths=True):
        return str(path) == env.test_files[0] or \
               str(path) == str(Path(env.test_files[0]))
    
    with mock.patch('unctools.converter.convert_to_local', side_effect=mock_convert_to_local), \
         mock.patch('unctools.converter.convert_to_unc', side_effect=mock_convert_to_unc), \
         mock.patch('unctools.detector.is_unc_path', side_effect=mock_is_unc_path), \
         mock.patch('unctools.detector.is_path_accessible', side_effect=mock_is_path_accessible):
        
        # Test with a UNC path (should try convert_to_local)
        path = find_accessible_path(TEST_UNC_PATH)
        assert_is_not_none(path, "Accessible path should be found after conversion")
        
        # Test with a non-UNC path (should try convert_to_unc)
        path = find_accessible_path(non_existent)
        assert_is_not_none(path, "Accessible path should be found after conversion")
        
        # Test with a path that can't be made accessible
        with mock.patch('unctools.detector.is_path_accessible', return_value=False):
            path = find_accessible_path(non_existent)
            assert_is_none(path, "No accessible path should be found")



def run_tests():
    """Run all operations tests."""
    suite = TestSuite("UNCtools Operations Tests")
    
    # Set suite setup and teardown
    suite.set_setup(setup_test_environment)
    suite.set_teardown(teardown_test_environment)
    
    # Add tests
    suite.add_test(test_file_exists)
    suite.add_test(test_batch_convert)
    suite.add_test(test_get_unc_path_elements)
    suite.add_test(test_build_unc_path)
    suite.add_test(test_is_path_accessible)
    suite.add_test(test_find_accessible_path)
    
    # Run suite
    return run_test_suites([suite])

if __name__ == "__main__":
    sys.exit(run_tests())
