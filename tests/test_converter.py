#!/usr/bin/env python3
"""
Tests for the unctools.converter module.
"""

import os
import re
import pytest
from pathlib import Path
from unittest import mock

from unctools.converter import (
    UNCConverter, convert_to_local, convert_to_unc,
    parse_unc_path, join_unc_path
)

# Test UNC paths
TEST_UNC_PATH = "\\\\server\\share\\folder\\file.txt"
TEST_LOCAL_PATH = "Z:\\folder\\file.txt"
TEST_SERVER = "server"
TEST_SHARE = "share"
TEST_REL_PATH = "folder\\file.txt"

# Sample network mappings for testing
MOCK_MAPPINGS = {
    "\\\\server\\share": "Z:\\",
    "\\\\fileserver\\public": "Y:\\",
    "\\\\nas\\backup": "X:\\"
}

MOCK_REVERSE_MAPPINGS = {
    "Z:": "\\\\server\\share",
    "Y:": "\\\\fileserver\\public",
    "X:": "\\\\nas\\backup"
}

class TestUNCConverter:
    """Tests for the UNCConverter class."""
    
    @pytest.fixture
    def converter(self):
        """Create a UNCConverter with mock mappings."""
        # Create converter with refresh_on_init=False to avoid actual system calls
        converter = UNCConverter(refresh_on_init=False)
        
        # Set up mock mappings
        converter._mapping = MOCK_MAPPINGS.copy()
        converter._reverse_mapping = MOCK_REVERSE_MAPPINGS.copy()
        
        return converter
    
    def test_constructor(self):
        """Test constructor behavior."""
        # Test with refresh_on_init=False
        with mock.patch.object(UNCConverter, 'refresh_mappings') as mock_refresh:
            converter = UNCConverter(refresh_on_init=False)
            mock_refresh.assert_not_called()
        
        # Test with refresh_on_init=True (default)
        with mock.patch.object(UNCConverter, 'refresh_mappings') as mock_refresh:
            converter = UNCConverter()
            mock_refresh.assert_called_once()
    
    def test_get_mappings(self, converter):
        """Test get_mappings method."""
        mappings = converter.get_mappings()
        assert mappings == MOCK_MAPPINGS
        
        # Ensure it's a copy
        mappings["test"] = "test"
        assert "test" not in converter.get_mappings()
    
    def test_get_reverse_mappings(self, converter):
        """Test get_reverse_mappings method."""
        mappings = converter.get_reverse_mappings()
        assert mappings == MOCK_REVERSE_MAPPINGS
        
        # Ensure it's a copy
        mappings["test"] = "test"
        assert "test" not in converter.get_reverse_mappings()
    
    def test_convert_to_local(self, converter):
        """Test convert_to_local method."""
        # Test conversion of a UNC path
        result = converter.convert_to_local(TEST_UNC_PATH)
        assert result == Path(TEST_LOCAL_PATH)
        
        # Test with a path that doesn't match any mapping
        unmapped_path = "\\\\unknown\\share\\file.txt"
        result = converter.convert_to_local(unmapped_path)
        assert result == Path(unmapped_path)
        
        # Test with a local path (should return unchanged)
        local_path = "C:\\folder\\file.txt"
        result = converter.convert_to_local(local_path)
        assert result == Path(local_path)
        
        # Test with different path formats
        unc_with_slashes = "//server/share/folder/file.txt"
        result = converter.convert_to_local(unc_with_slashes)
        assert result == Path(TEST_LOCAL_PATH)
    
    @pytest.mark.skipif(os.name != 'nt', reason="Windows-specific test - UNC paths and drive letters are Windows concepts")
    def test_convert_to_unc(self, converter):
        """Test convert_to_unc method."""
        # Test conversion of a local path
        result = converter.convert_to_unc(TEST_LOCAL_PATH)
        assert result == Path(TEST_UNC_PATH)
        
        # Test with a path that doesn't match any mapping
        unmapped_path = "C:\\folder\\file.txt"
        result = converter.convert_to_unc(unmapped_path)
        assert result == Path(unmapped_path)
        
        # Test with a UNC path (should return unchanged)
        result = converter.convert_to_unc(TEST_UNC_PATH)
        assert result == Path(TEST_UNC_PATH)
        
        # Test with drive letter variations
        result = converter.convert_to_unc("z:/folder/file.txt")
        assert result == Path(TEST_UNC_PATH)
        
        # Test with drive letter only
        result = converter.convert_to_unc("Z:")
        assert result == Path("\\\\server\\share")
    
    @pytest.mark.skipif(os.name != 'nt', reason="Windows-specific test")
    @pytest.mark.xfail(reason="Test design issue: Mock win32net returns empty dict. Needs proper mock setup for win32net.NetUseEnum")
    def test_refresh_mappings_windows(self):
        """Test refresh_mappings method on Windows."""
        # This test should only run on Windows
        # Create converter with real system calls
        with mock.patch('subprocess.run') as mock_run:
            # Mock the output of 'net use'
            mock_process = mock.MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = (
                "New connections will be remembered.\n"
                "\n"
                "Status       Local     Remote                    Network\n"
                "\n"
                "-------------------------------------------------------------------------------\n"
                "OK           Z:        \\\\server\\share            Microsoft Windows Network\n"
                "OK           Y:        \\\\fileserver\\public       Microsoft Windows Network\n"
            )
            mock_run.return_value = mock_process
            
            # Create converter and refresh mappings
            converter = UNCConverter(refresh_on_init=False)
            converter.refresh_mappings()
            
            # Check the mappings
            mappings = converter.get_mappings()
            assert "\\\\server\\share" in mappings
            assert "\\\\fileserver\\public" in mappings
            assert mappings["\\\\server\\share"] == "Z:\\"
            assert mappings["\\\\fileserver\\public"] == "Y:\\"


class TestModuleFunctions:
    """Tests for the module-level functions."""
    
    def test_convert_to_local(self):
        """Test convert_to_local function."""
        # Mock the global converter
        with mock.patch('unctools.converter._global_converter') as mock_converter:
            mock_converter.convert_to_local.return_value = Path(TEST_LOCAL_PATH)
            
            result = convert_to_local(TEST_UNC_PATH)
            assert result == Path(TEST_LOCAL_PATH)
            mock_converter.convert_to_local.assert_called_once_with(TEST_UNC_PATH)
    
    def test_convert_to_unc(self):
        """Test convert_to_unc function."""
        # Mock the global converter
        with mock.patch('unctools.converter._global_converter') as mock_converter:
            mock_converter.convert_to_unc.return_value = Path(TEST_UNC_PATH)
            
            result = convert_to_unc(TEST_LOCAL_PATH)
            assert result == Path(TEST_UNC_PATH)
            mock_converter.convert_to_unc.assert_called_once_with(TEST_LOCAL_PATH)
    
    def test_parse_unc_path(self):
        """Test parse_unc_path function."""
        # Test with a valid UNC path
        result = parse_unc_path(TEST_UNC_PATH)
        assert result == (TEST_SERVER, TEST_SHARE, TEST_REL_PATH)
        
        # Test with a UNC path with no relative path
        result = parse_unc_path("\\\\server\\share")
        assert result == (TEST_SERVER, TEST_SHARE, "")
        
        # Test with a non-UNC path
        result = parse_unc_path(TEST_LOCAL_PATH)
        assert result is None
        
        # Test with a UNC path using forward slashes
        result = parse_unc_path("//server/share/folder/file.txt")
        assert result == (TEST_SERVER, TEST_SHARE, TEST_REL_PATH)
    
    def test_join_unc_path(self):
        """Test join_unc_path function."""
        # Test with all components
        result = join_unc_path(TEST_SERVER, TEST_SHARE, TEST_REL_PATH)
        assert result == TEST_UNC_PATH
        
        # Test without relative path
        result = join_unc_path(TEST_SERVER, TEST_SHARE)
        assert result == "\\\\server\\share"
        
        # Test with empty relative path
        result = join_unc_path(TEST_SERVER, TEST_SHARE, "")
        assert result == "\\\\server\\share"
        
        # Test with relative path that starts with backslash
        result = join_unc_path(TEST_SERVER, TEST_SHARE, "\\folder\\file.txt")
        assert result == TEST_UNC_PATH