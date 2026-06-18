r"""
Path conversion utilities for UNC paths, network drives, and substituted drives.

This module provides functions to convert between UNC paths (\\server\share) and
local drive paths, as well as normalization and validation functions.
"""

import os
import re
import logging
import subprocess
from pathlib import Path
from typing import Dict, Union, Optional, Tuple

# Set up module-level logger
logger = logging.getLogger(__name__)

# Define if we're running on Windows
IS_WINDOWS = os.name == 'nt'

# Global flag for win32net availability
HAVE_WIN32NET = False
# Global flag for win32wnet availability (WNet Multiple Provider Router)
HAVE_WIN32WNET = False

# Only try to import Windows-specific modules if we're on Windows
if IS_WINDOWS:
    from unctools.utils.compat import is_module_available

    # Check if win32net is available without importing it
    if is_module_available('win32net'):
        try:
            import win32net
            HAVE_WIN32NET = True
        except ImportError:
            # This should rarely happen since we checked for availability
            logger.debug("win32net module found but failed to import.")

    # win32wnet powers the WNetGetUniversalName provider-chain enrichment
    # (catches drives served by non-SMB / third-party network providers that
    # the LanmanWorkstation net-use table -- NetUseEnum -- can miss).
    if is_module_available('win32wnet'):
        try:
            import win32wnet
            HAVE_WIN32WNET = True
        except ImportError:
            logger.debug("win32wnet module found but failed to import.")

# Define constants
UNC_PATTERN = re.compile(r'^\\\\([^\\]+)\\([^\\]+)(?:\\(.*))?$')
DRIVE_LETTER_PATTERN = re.compile(r'^([A-Za-z]:)(?:\\(.*))?$')

class UNCConverter:
    r"""
    Handles conversion between UNC paths and mapped drive paths.
    
    This class provides methods to convert UNC paths (\\server\share) to their 
    corresponding drive paths (X:\) and vice versa, based on the system's 
    network mappings.
    """
    
    def __init__(self, refresh_on_init=True):
        """
        Initialize the UNC converter.
        
        Args:
            refresh_on_init: Whether to refresh network mappings on initialization.
                             Default is True.
        """
        self._mapping: Dict[str, str] = {}  # UNC prefix -> drive letter
        self._reverse_mapping: Dict[str, str] = {}  # drive letter -> UNC prefix
        
        # Windows network share command is only available on Windows
        self._is_windows = IS_WINDOWS
        
        if refresh_on_init:
            self.refresh_mappings()
    
    def refresh_mappings(self) -> Dict[str, str]:
        """
        Refresh the mapping of UNC paths to drive letters by querying the system.
        
        Returns:
            A dictionary mapping UNC prefixes to drive letters.
        """
        if not self._is_windows:
            logger.debug("Not running on Windows, no network mappings to refresh")
            return {}
            
        old_mapping = self._mapping.copy()
        self._mapping.clear()
        self._reverse_mapping.clear()
        
        # Try to use win32net if available
        if HAVE_WIN32NET:
            success = self._get_mappings_with_win32net()
            if not success:
                # Fall back to subprocess
                self._get_mappings_with_subprocess()
        else:
            # Use subprocess method
            self._get_mappings_with_subprocess()

        # Additive enrichment pass: pick up drives the net-use table missed
        # (non-SMB / third-party providers, some DFS/reconnect cases) via the
        # WNet provider chain. Never overwrites an authoritative net-use entry.
        self._get_mappings_with_wnetuniversalname()

        # Check if mappings changed
        if self._mapping != old_mapping:
            logger.debug(f"Network mappings changed: {len(self._mapping)} mappings")
            
        return self._mapping
    
    def _get_mappings_with_win32net(self) -> bool:
        """
        Get network mappings using the win32net API.
        
        This method populates the internal mapping dictionaries.
        
        Returns:
            True if successful, False otherwise.
        """
        if not HAVE_WIN32NET:
            return False
            
        try:
            # Import here to ensure it's only imported when needed
            import win32net
            
            # Level 2 provides detailed information
            connections, total, resume = win32net.NetUseEnum(None, 2)
            
            for conn in connections:
                local = conn.get('local', '').upper()
                remote = conn.get('remote', '').lower()
                
                if local and remote:
                    # Ensure drive letter has trailing backslash
                    if local and not local.endswith('\\'):
                        local += '\\'
                    
                    # Store UNC path without trailing backslash as key
                    remote = remote.rstrip('\\')
                    
                    self._mapping[remote] = local
                    self._reverse_mapping[local.rstrip('\\')] = remote
            
            logger.debug(f"Retrieved {len(self._mapping)} network mappings using win32net")
            return True
        except Exception as e:
            logger.warning(f"Error in win32net.NetUseEnum: {e}")
            return False
    
    def _get_mappings_with_subprocess(self) -> None:
        """
        Get network mappings by parsing 'net use' command output.
        
        This method populates the internal mapping dictionaries.
        """
        if not self._is_windows:
            return
            
        try:
            output = subprocess.check_output(["net", "use"], text=True, stderr=subprocess.STDOUT)
            
            # Parse output and extract mappings
            for line in output.splitlines():
                # Look for lines like: "OK Z: \\server\share"
                m = re.search(r'^(OK|Disconnected)\s+([A-Za-z]:)\s+(\\\\\S+)', line, re.IGNORECASE)
                if m:
                    drive_letter = m.group(2).upper()
                    if not drive_letter.endswith('\\'):
                        drive_letter += '\\'
                    
                    unc_path = m.group(3).lower().rstrip('\\')
                    
                    self._mapping[unc_path] = drive_letter
                    self._reverse_mapping[drive_letter.rstrip('\\')] = unc_path
            
            logger.debug(f"Retrieved {len(self._mapping)} network mappings using 'net use'")
        except Exception as e:
            logger.warning(f"Failed to get network mappings using 'net use': {e}")

    def _get_mappings_with_wnetuniversalname(self) -> None:
        """Enrich the mappings via ``win32wnet.WNetGetUniversalName`` (the WNet
        Multiple Provider Router).

        ``NetUseEnum`` / ``net use`` reflect the LanmanWorkstation (SMB) net-use
        table and can miss drives served by non-SMB or third-party network
        providers, and some DFS/reconnect cases. ``WNetGetUniversalName`` walks
        the MPR provider chain and resolves the universal (UNC) name for such
        drives. This runs as an **additive** pass after the primary source: a
        drive already mapped by ``NetUseEnum``/``net use`` is left untouched
        (those entries are authoritative); only drives not yet known are added.

        Provenance: ports the ``win32wnet.WNetGetUniversalName`` per-drive A-Z
        scan from ``dazzle_filekit.utils.compat.get_drive_mappings`` into the
        path-identity layer that owns drive<->UNC knowledge (STACK-MAP V9).
        Populates ``_mapping`` / ``_reverse_mapping`` in the module's normalized
        conventions (UNC lowercased + no trailing slash; drive uppercased).
        """
        if not self._is_windows or not HAVE_WIN32WNET:
            return

        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            drive_no_slash = f"{letter}:"

            # Don't overwrite an authoritative net-use entry.
            if drive_no_slash in self._reverse_mapping:
                continue

            try:
                # Level 1 (UNIVERSAL_NAME_INFO_LEVEL) returns the UNC string.
                unc = win32wnet.WNetGetUniversalName(drive_no_slash, 1)
            except Exception:
                # Not a redirected/mapped drive, or no MPR provider claims it.
                continue

            if not unc:
                continue

            unc_clean = str(unc).rstrip('\\').lower()
            if not unc_clean.startswith('\\\\'):
                continue

            self._mapping.setdefault(unc_clean, drive_no_slash + '\\')
            self._reverse_mapping[drive_no_slash] = unc_clean
            logger.debug(f"WNet enrichment: {drive_no_slash} -> {unc_clean}")

    def convert_to_local(self, path: Union[str, Path]) -> Path:
        """
        Convert a UNC path to its corresponding local drive path if possible.
        
        Args:
            path: The path to convert, potentially a UNC path.
            
        Returns:
            Path: The converted path using a drive letter if a mapping exists, 
                  otherwise the original path.
        """
        path_str = str(path).replace('/', '\\')
        
        # If the path already has a drive letter, return it unchanged
        if re.match(r'^[A-Za-z]:', path_str):
            return Path(path_str)
        
        # Check if it's a UNC path (starts with \\)
        if not path_str.startswith('\\\\'):
            return Path(path_str)
        
        # Try to match the UNC path with known mappings
        # Sort keys by length in descending order to match the most specific first
        for unc_prefix in sorted(self._mapping.keys(), key=len, reverse=True):
            if path_str.lower().startswith(unc_prefix.lower()):
                # Replace the UNC prefix with the drive letter
                local_part = path_str[len(unc_prefix):]
                drive_path = f"{self._mapping[unc_prefix]}{local_part.lstrip(chr(92))}"
                logger.debug(f"Converted UNC path '{path_str}' to local path '{drive_path}'")
                return Path(drive_path)
        
        # No matching mapping found, return the original path
        logger.debug(f"No drive mapping found for UNC path '{path_str}'")
        return Path(path_str)
    
    def convert_to_unc(self, path: Union[str, Path]) -> Path:
        """
        Convert a local drive path to its corresponding UNC path if possible.
        
        Args:
            path: The path to convert, potentially using a mapped drive.
            
        Returns:
            Path: The converted UNC path if the drive is mapped to a network share,
                  otherwise the original path.
        """
        path_str = str(path).replace('/', '\\')
        
        # Check if the path starts with a drive letter
        match = re.match(r'^([A-Za-z]:[\\]?)', path_str, re.IGNORECASE)
        if not match:
            # Not a drive path, return unchanged
            return Path(path_str)
        
        drive = match.group(1).upper()
        if not drive.endswith('\\'):
            drive += '\\'
        
        drive_no_slash = drive.rstrip('\\')
        
        # Check if the drive is in our mapping
        if drive_no_slash in self._reverse_mapping:
            unc_prefix = self._reverse_mapping[drive_no_slash]
            # Replace the drive with the UNC path
            rest_of_path = path_str[len(drive_no_slash):].lstrip(chr(92))
            unc_path = f"{unc_prefix}{chr(92)}{rest_of_path}"
            logger.debug(f"Converted local path '{path_str}' to UNC path '{unc_path}'")
            return Path(unc_path)
        
        # No matching mapping found, return the original path
        logger.debug(f"No UNC mapping found for local path '{path_str}'")
        return Path(path_str)
    
    def get_mappings(self) -> Dict[str, str]:
        """
        Get a dictionary of current UNC path to drive letter mappings.
        
        Returns:
            A dictionary mapping UNC paths to drive letters.
        """
        return self._mapping.copy()
    
    def get_reverse_mappings(self) -> Dict[str, str]:
        """
        Get a dictionary of current drive letter to UNC path mappings.
        
        Returns:
            A dictionary mapping drive letters to UNC paths.
        """
        return self._reverse_mapping.copy()

# Create a global instance for convenience
_global_converter = None

def _get_global_converter() -> UNCConverter:
    """
    Get or create the global UNCConverter instance.
    
    Returns:
        The global UNCConverter instance.
    """
    global _global_converter
    if _global_converter is None:
        _global_converter = UNCConverter()
    return _global_converter

def convert_to_local(path: Union[str, Path]) -> Path:
    """
    Convert a UNC path to its corresponding local drive path if possible.
    
    Args:
        path: The path to convert, potentially a UNC path.
        
    Returns:
        Path: The converted path using a drive letter if a mapping exists, 
              otherwise the original path.
    """
    converter = _get_global_converter()
    return converter.convert_to_local(path)

def convert_to_unc(path: Union[str, Path]) -> Path:
    """
    Convert a local drive path to its corresponding UNC path if possible.
    
    Args:
        path: The path to convert, potentially using a mapped drive.
        
    Returns:
        Path: The converted UNC path if the drive is mapped to a network share,
              otherwise the original path.
    """
    converter = _get_global_converter()
    return converter.convert_to_unc(path)

def refresh_mappings() -> Dict[str, str]:
    """
    Refresh the global mapping of UNC paths to drive letters.
    
    Returns:
        A dictionary mapping UNC paths to drive letters.
    """
    converter = _get_global_converter()
    return converter.refresh_mappings()

def get_mappings() -> Dict[str, str]:
    """
    Get the current global UNC path to drive letter mappings.
    
    Returns:
        A dictionary mapping UNC paths to drive letters.
    """
    converter = _get_global_converter()
    return converter.get_mappings()

# normalize_path(prefer_unc=) was REMOVED in 0.2.0 (STACK-MAP D4): the explicit
# convert_to_local / convert_to_unc ARE the API; a direction-switch wrapper
# taught nothing and collided with other libraries' normalize_path semantics.

def parse_unc_path(path: Union[str, Path]) -> Optional[Tuple[str, str, str]]:
    """
    Parse a UNC path into server, share, and path components.
    
    Args:
        path: The UNC path to parse.
        
    Returns:
        A tuple of (server, share, path) if the path is a valid UNC path,
        or None if the path is not a UNC path.
    """
    path_str = str(path).replace('/', '\\')
    match = UNC_PATTERN.match(path_str)
    
    if match:
        server = match.group(1)
        share = match.group(2)
        rest = match.group(3) or ""
        return (server, share, rest)
    
    return None

def join_unc_path(server: str, share: str, rest: str = "") -> str:
    """
    Join UNC path components into a complete UNC path.
    
    Args:
        server: The server name.
        share: The share name.
        rest: The rest of the path (optional).
        
    Returns:
        A properly formatted UNC path.
    """
    if rest:
        return f"{chr(92)}{chr(92)}{server}{chr(92)}{share}{chr(92)}{rest.lstrip(chr(92))}"
    else:
        return f"{chr(92)}{chr(92)}{server}{chr(92)}{share}"


# ── Moved here from the dissolved operations module (0.2.0, STACK-MAP D7) ──
# Pure path-identity work: batch conversion and UNC path algebra. NOTE:
# parse_unc_path/join_unc_path above are near-duplicates of
# get_unc_path_elements/build_unc_path (these preserve forward slashes in the
# relative part; those don't) -- consolidation candidate for 0.3.0.

def batch_convert(paths, to_unc: bool = False) -> Dict[str, str]:
    """
    Convert a batch of paths between UNC and local formats.

    Args:
        paths: List of paths to convert.
        to_unc: If True, convert to UNC paths; if False, convert to local paths.

    Returns:
        A dictionary mapping original paths to converted paths.
    """
    result = {}

    for path in paths:
        original_path = str(path)

        try:
            if to_unc:
                converted_path = str(convert_to_unc(path))
            else:
                converted_path = str(convert_to_local(path))

            result[original_path] = converted_path
        except Exception as e:
            logger.warning(f"Failed to convert path {original_path}: {e}")
            result[original_path] = original_path  # Keep original on failure

    return result

def get_unc_path_elements(path: Union[str, Path]) -> Optional[Tuple[str, str, str]]:
    """
    Extract server, share, and path components from a UNC path.

    Args:
        path: The UNC path to analyze.

    Returns:
        A tuple of (server, share, relative_path) if the path is a valid UNC path,
        or None if the path is not a UNC path.
    """
    original_path_str = str(path)
    path_str = original_path_str.replace('/', '\\')

    # Check if it's a UNC path
    if not path_str.startswith('\\\\'):
        return None

    # Parse the UNC path
    match = re.match(r'^\\\\([^\\]+)\\([^\\]+)(?:\\(.*))?', path_str)
    if match:
        server = match.group(1)
        share = match.group(2)
        relative_path = match.group(3) or ""

        # If original path used forward slashes, preserve them in the relative path
        if '/' in original_path_str:
            # Replace backslashes with forward slashes in the relative path
            relative_path = relative_path.replace('\\', '/')

        return (server, share, relative_path)
    return None

def build_unc_path(server: str, share: str, relative_path: Optional[str] = None) -> str:
    """
    Build a UNC path from server, share, and path components.

    Args:
        server: The server name.
        share: The share name.
        relative_path: The relative path within the share (optional).

    Returns:
        A properly formatted UNC path.
    """
    unc_base = f"\\\\{server}\\{share}"

    if not relative_path:
        return unc_base

    # Ensure relative path doesn't start with a backslash
    rel_path = relative_path.lstrip('\\').lstrip('/')

    if rel_path:
        return f"{unc_base}\\{rel_path}"
    else:
        return unc_base
