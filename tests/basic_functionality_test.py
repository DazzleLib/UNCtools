#!/usr/bin/env python3
"""
Basic functionality test for UNCtools.

This test script performs basic validation of UNCtools functionality.
Run this script to verify that imports, basic functions, and core features
work correctly in your environment.
"""

import os
os.system("chcp 65001 > nul")  # Set console to UTF-8

import sys
import platform
import logging
from pathlib import Path


import unctools
print("UNCTools loaded from:", unctools.__file__)

import sys
print("Python version:", sys.version)

# import tests
# print("tests loaded from:", tests.__file__)


# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def check(condition, message):
    """Check a condition and print the result."""
    if condition:
        print(f"[PASS] {message}")
        return True
    else:
        print(f"[FAIL] {message}")
        return False

def run_tests():
    """Run basic functionality tests."""
    print("\n=== UNCtools Basic Functionality Tests ===\n")
    
    # Step 1: Import the package
    print("Testing imports...")
    try:
        import unctools
        check(True, "Import unctools")
    except ImportError as e:
        check(False, f"Import unctools: {e}")
        print("\nFailed to import UNCtools package. Ensure it's installed or available in your Python path.")
        return False
    
    # Step 2: Check version information
    print("\nChecking version information...")
    version = unctools.__version__
    check(version is not None, f"UNCtools version: {version}")
    
    # Step 3: Test core imports
    print("\nTesting core module imports...")
    try:
        from unctools import (
            convert_to_local, convert_to_unc, classify_path_origin,
            is_unc_path, is_network_drive, is_subst_drive,
            file_exists, batch_convert
        )
        check(True, "Import core functions")
    except ImportError as e:
        check(False, f"Import core functions: {e}")
        print("\nFailed to import core UNCtools functions. Package may be incomplete.")
        return False
    
    # Step 4: Test utils imports
    print("\nTesting utils module imports...")
    try:
        from unctools.utils import (
            configure_logging, get_logger,
            is_windows, is_linux, is_macos,
            validate_path, validate_unc_path
        )
        check(True, "Import utils functions")
    except ImportError as e:
        check(False, f"Import utils functions: {e}")
        print("\nFailed to import UNCtools utility functions. Some features may be unavailable.")
    
    # Step 5: Test Windows-specific imports (if on Windows)
    if os.name == 'nt':
        print("\nTesting Windows-specific module imports...")
        try:
            from unctools.windows import (
                fix_security_zone, add_to_intranet_zone,
                create_network_mapping, remove_network_mapping,
                get_file_security, check_access_rights
            )
            check(True, "Import Windows-specific functions")
        except ImportError as e:
            check(False, f"Import Windows-specific functions: {e}")
            print("\nFailed to import Windows-specific functions. Some features may be unavailable.")
    else:
        print("\nSkipping Windows-specific tests on non-Windows platform.")
    
    # Step 6: Test basic functionality
    print("\nTesting basic functionality...")
    
    # Test path detection
    test_path = str(Path.home())
    check(not is_unc_path(test_path), f"is_unc_path({test_path}) should be False")
    
    test_unc_path = r"\\server\share\folder"
    check(is_unc_path(test_unc_path), f"is_unc_path({test_unc_path}) should be True")
    
    # Test origin classification (normalize_path removed in 0.2.0, D4)
    try:
        origin = classify_path_origin(test_path)
        check(True, f"classify_path_origin({test_path}) => {origin}")
    except Exception as e:
        check(False, f"classify_path_origin({test_path}): {e}")
    
    # Test path conversion (just ensure it doesn't error)
    try:
        local_path = convert_to_local(test_unc_path)
        check(True, f"convert_to_local({test_unc_path}) => {local_path}")
    except Exception as e:
        check(False, f"convert_to_local({test_unc_path}): {e}")
    
    try:
        unc_path = convert_to_unc(test_path)
        check(True, f"convert_to_unc({test_path}) => {unc_path}")
    except Exception as e:
        check(False, f"convert_to_unc({test_path}): {e}")
    
    # Test batch conversion
    try:
        result = batch_convert([test_path, test_unc_path], to_unc=True)
        check(len(result) == 2, f"batch_convert() returned {len(result)} results")
    except Exception as e:
        check(False, f"batch_convert(): {e}")
    
    # Test platform detection
    from unctools.utils import get_platform_info
    try:
        platform_info = get_platform_info()
        platform_str = ", ".join(f"{k}: {v}" for k, v in platform_info.items())
        check(True, f"Platform information: {platform_str}")
    except Exception as e:
        check(False, f"get_platform_info(): {e}")
    
    # Step 7: Test file operations with a temporary file
    print("\nTesting file operations with a temporary file...")
    import tempfile
    
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_filename = f.name
            f.write("UNCtools test file")
        
        # Test file_exists probe (safe_open removed in 0.2.0, D7)
        check(file_exists(temp_filename), f"file_exists({temp_filename}) should be True")
        
        # Clean up
        os.unlink(temp_filename)
        check(True, "Temporary file operations completed")
    except Exception as e:
        check(False, f"File operations: {e}")
    
    # All tests completed
    print("\n=== Test Summary ===")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {platform.python_version()}")
    print(f"UNCtools: {version}")
    print("All tests completed. Check the results above for any failures.")
    
    return True

def main():
    """Main function."""
    try:
        success = run_tests()
        if success:
            print("\nBasic functionality tests completed successfully.")
        else:
            print("\nSome basic functionality tests failed.")
            sys.exit(1)
    except Exception as e:
        print(f"\nError running tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()