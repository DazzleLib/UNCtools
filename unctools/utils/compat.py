"""
Cross-platform compatibility utilities for UNCtools.

This module provides functions and utilities for ensuring consistent behavior
across different operating systems and platforms.
"""

import os
import sys
import platform
import logging
import importlib.util
from typing import Dict, Tuple, List, Optional, Union, Any

# Set up module-level logger
logger = logging.getLogger(__name__)

def is_windows() -> bool:
    """
    Check if running on Windows.
    
    Returns:
        True if running on Windows, False otherwise.
    """
    return os.name == 'nt'

def is_linux() -> bool:
    """
    Check if running on Linux.
    
    Returns:
        True if running on Linux, False otherwise.
    """
    return platform.system() == 'Linux'

def is_macos() -> bool:
    """
    Check if running on macOS.
    
    Returns:
        True if running on macOS, False otherwise.
    """
    return platform.system() == 'Darwin'

def get_platform_info() -> Dict[str, str]:
    """
    Get detailed information about the current platform.
    
    Returns:
        A dictionary with platform information.
    """
    info = {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'architecture': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'python_implementation': platform.python_implementation(),
    }
    
    # Add Windows-specific information if available
    if is_windows():
        try:
            import winreg
            # Get Windows edition
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
                info['windows_edition'] = winreg.QueryValueEx(key, "ProductName")[0]
                info['windows_build'] = winreg.QueryValueEx(key, "CurrentBuildNumber")[0]
                try:
                    info['windows_display_version'] = winreg.QueryValueEx(key, "DisplayVersion")[0]
                except:
                    pass  # Not available on older Windows versions
        except:
            logger.debug("Could not retrieve detailed Windows information")
    
    return info

def is_module_available(module_name: str) -> bool:
    """
    Check if a module is available without importing it or triggering warnings.
    
    Args:
        module_name: Name of the module to check
        
    Returns:
        True if the module is available, False otherwise
    """
    spec = importlib.util.find_spec(module_name)
    return spec is not None

def safe_import(module_name: str, default=None):
    """
    Safely import a module, returning a default value if the import fails.
    
    This is useful for optional dependencies where you want to gracefully
    handle missing modules without warnings or errors.
    
    Args:
        module_name: Name of the module to import
        default: Default value to return if the import fails (default: None)
        
    Returns:
        The imported module if successful, or the default value if the import fails
    """
    if is_module_available(module_name):
        try:
            return importlib.import_module(module_name)
        except ImportError:
            pass
    return default

def path_separator() -> str:
    """
    Get the path separator for the current platform.
    
    Returns:
        The path separator character ('\\' on Windows, '/' elsewhere).
    """
    return '\\' if is_windows() else '/'

def normalize_path_separators(path: str) -> str:
    """
    Normalize path separators for the current platform.
    
    Args:
        path: The path to normalize.
        
    Returns:
        The path with normalized separators.
    """
    separator = path_separator()
    if separator == '\\':
        # On Windows, convert forward slashes to backslashes
        return path.replace('/', '\\')
    else:
        # On Unix-like systems, convert backslashes to forward slashes
        return path.replace('\\', '/')

def get_home_directory() -> str:
    """
    Get the user's home directory in a cross-platform way.
    
    Returns:
        The path to the home directory.
    """
    return os.path.expanduser("~")

def get_temp_directory() -> str:
    """
    Get the system's temporary directory in a cross-platform way.
    
    Returns:
        The path to the temporary directory.
    """
    return os.path.normpath(os.path.abspath(os.environ.get('TEMP') or 
                                            os.environ.get('TMP') or 
                                            os.path.join(os.path.expanduser("~"), '.tmp')))

def get_app_data_directory(app_name: str = "unctools") -> str:
    """
    Get the application data directory in a cross-platform way.
    
    Args:
        app_name: The name of the application.
        
    Returns:
        The path to the application data directory.
    """
    if is_windows():
        # On Windows, use %APPDATA%
        base_dir = os.environ.get('APPDATA', os.path.expanduser("~"))
    elif is_macos():
        # On macOS, use ~/Library/Application Support
        base_dir = os.path.join(os.path.expanduser("~"), 'Library', 'Application Support')
    else:
        # On Linux and other platforms, use ~/.config
        base_dir = os.path.join(os.path.expanduser("~"), '.config')
    
    app_dir = os.path.join(base_dir, app_name)
    
    # Ensure the directory exists
    os.makedirs(app_dir, exist_ok=True)
    
    return app_dir

def get_long_path_prefix() -> str:
    """
    Get the prefix for accessing long paths on Windows.
    
    On Windows, paths longer than MAX_PATH (260 characters) require a special prefix.
    This function returns the appropriate prefix for the current platform.
    
    Returns:
        The long path prefix ('\\\\?\\' on Windows, empty string elsewhere).
    """
    if is_windows():
        return '\\\\?\\'
    return ''

def apply_long_path_prefix(path: str) -> str:
    """
    Apply the long path prefix to a path if necessary.
    
    Args:
        path: The path to modify.
        
    Returns:
        The path with the long path prefix if needed.
    """
    if is_windows() and not path.startswith('\\\\?\\'):
        # Check if path is already in UNC format
        if path.startswith('\\\\'):
            # For UNC paths, use \\?\UNC\server\share
            return '\\\\?\\UNC\\' + path[2:]
        else:
            # For regular paths, just add \\?\
            return '\\\\?\\' + path
    return path

def supports_symlinks() -> bool:
    """
    Check if the current platform supports symbolic links.
    
    Returns:
        True if symbolic links are supported, False otherwise.
    """
    if is_windows():
        # On Windows, symlinks are available in Vista+ but require extra privileges
        try:
            # Check Windows version
            windows_version = tuple(map(int, platform.version().split('.')))
            if windows_version >= (6, 0):  # Vista+
                # Check for administrator privileges
                import ctypes
                return bool(ctypes.windll.shell32.IsUserAnAdmin())
            return False
        except:
            return False
    else:
        # On Unix-like systems, symlinks are generally available
        return True

def has_admin_privileges() -> bool:
    """
    Check if the current process has administrator/root privileges.
    
    Returns:
        True if the process has admin privileges, False otherwise.
    """
    if is_windows():
        try:
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except:
            return False
    else:
        # On Unix-like systems, check for root (UID 0)
        return os.geteuid() == 0 if hasattr(os, 'geteuid') else False

# path_exists_case_sensitive and get_case_sensitive_path were REMOVED in
# 0.2.0 (STACK-MAP D8): path-case canonicalization is format-normalization
# work and lives in dazzle-filekit (merged with its fix_path_case).
