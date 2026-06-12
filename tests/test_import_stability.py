"""Import-stability canary + 0.2.0 surgery contract (see docs/api-stability.md).

Locked surface: if this test fails, a consumer breaks -- follow the
api-stability process (noisy shim, register, slate removal), never a silent fix.

Also asserts the 0.2.0 surgery outcomes (STACK-MAP D4/D7/D8):
- deleted content-I/O wrappers are GONE (probe-not-mutate, rule 3a)
- moved survivors live in their new homes (and the top-level namespace)
- the get_path_type -> classify_path_origin shim warns (alias A4)
- the operations facade warns on import (removed in 0.3.0)
"""

import importlib
import warnings

import pytest

LOCKED_SURFACE = {
    "unctools": [
        # identity conversion
        "convert_to_local", "convert_to_unc", "batch_convert",
        "get_unc_path_elements", "build_unc_path",
        # origin classification + probes
        "is_unc_path", "is_network_drive", "is_subst_drive",
        "classify_path_origin", "get_network_mappings", "detect_path_issues",
        "file_exists", "is_path_accessible", "find_accessible_path",
        # package plumbing
        "configure_logging", "get_version",
    ],
    "unctools.converter": [
        "UNCConverter", "convert_to_local", "convert_to_unc", "batch_convert",
        "get_unc_path_elements", "build_unc_path", "refresh_mappings",
    ],
    "unctools.detector": [
        "is_unc_path", "is_network_drive", "is_subst_drive",
        "classify_path_origin", "get_network_mappings", "detect_path_issues",
        "file_exists", "is_path_accessible", "find_accessible_path",
    ],
}

DELETED_FOREVER = {
    # D7: content I/O has no home at L0 (probe, never mutate)
    "unctools.operations": ["safe_open", "safe_copy", "batch_copy",
                            "process_files", "replace_in_file",
                            "batch_replace_in_files"],
    # D8: case handling merged into dazzle-filekit
    "unctools.utils.compat": ["path_exists_case_sensitive",
                              "get_case_sensitive_path"],
    # D4: the explicit converts ARE the API
    "unctools.converter": ["normalize_path"],
}


def test_locked_surface_importable():
    missing = []
    for module_name, symbols in LOCKED_SURFACE.items():
        module = importlib.import_module(module_name)
        for symbol in symbols:
            if not hasattr(module, symbol):
                missing.append(f"{module_name}.{symbol}")
    assert not missing, f"Locked API symbols missing: {missing}"


def test_deleted_symbols_stay_deleted():
    present = []
    for module_name, symbols in DELETED_FOREVER.items():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # operations facade warns on import
            module = importlib.import_module(module_name)
        for symbol in symbols:
            if hasattr(module, symbol):
                present.append(f"{module_name}.{symbol}")
    assert not present, (
        f"Deleted-by-contract symbols re-appeared: {present} -- "
        f"these were removed by STACK-MAP D4/D7/D8 and must not return."
    )


def test_get_path_type_shim_warns_and_delegates():
    """A4: old name works through 0.2.x, warns naming the new home."""
    import unctools
    with pytest.warns(DeprecationWarning, match="classify_path_origin"):
        result = unctools.get_path_type("C:\\")
    assert result == unctools.classify_path_origin("C:\\")


def test_operations_facade_warns_on_import():
    """The dissolved operations module is a 0.2.x-only facade (gone in 0.3.0)."""
    import sys
    sys.modules.pop("unctools.operations", None)
    with pytest.warns(DeprecationWarning, match="0.3.0"):
        import unctools.operations  # noqa: F401


def test_version_is_0_2_0():
    import unctools
    assert unctools.__version__ == "0.2.0"
