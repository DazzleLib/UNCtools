"""Tests for the 0.3.0 kinded variant primitive + subst one-shot enumeration.

path_variants(path) -> [(kind, value)] where kind is the MECHANISM-OF-DERIVATION
(unc / drive / subst), not the form of the value; the input path is never
included (derivations only -- callers prepend it if adapting to
dazzle_lib.PathVariantResolver, whose variants() DOES include the input).
"""

import os
import string
import subprocess

import pytest

import unctools
from unctools import path_variants, get_subst_mappings, get_subst_target
from unctools.detector import _clear_path_type_cache

IS_WINDOWS = os.name == "nt"


def _free_drive_letter():
    import ctypes

    bits = ctypes.windll.kernel32.GetLogicalDrives()
    used = {c for i, c in enumerate(string.ascii_uppercase) if bits & (1 << i)}
    for c in "QRSTUVWXY":
        if c not in used:
            return c
    return None


@pytest.fixture
def subst_drive(tmp_path):
    """A real subst drive mapped to tmp_path; removed afterwards."""
    if not IS_WINDOWS:
        pytest.skip("subst is Windows-only")
    letter = _free_drive_letter()
    if letter is None:
        pytest.skip("no free drive letter for subst")
    subprocess.run(["subst", f"{letter}:", str(tmp_path)], check=True)
    _clear_path_type_cache()
    try:
        yield f"{letter}:"
    finally:
        subprocess.run(["subst", f"{letter}:", "/d"], check=True)
        _clear_path_type_cache()


# --- exports (0.3.0 surface) -----------------------------------------------

def test_new_symbols_are_top_level():
    for name in (
        "get_subst_target",
        "get_network_target",
        "get_subst_mappings",
        "get_mappings",
        "refresh_mappings",
        "path_variants",
    ):
        assert hasattr(unctools, name), name


# --- path_variants contract -------------------------------------------------

def test_variants_exclude_the_original(tmp_path):
    # A plain local path with no mappings applying -> no variants, and never
    # the input itself (even separator-normalized).
    p = str(tmp_path / "plain.txt")
    results = path_variants(p)
    values = [os.path.normcase(v) for _, v in results]
    assert os.path.normcase(p) not in values


def test_variants_are_kinded_pairs(tmp_path):
    results = path_variants(str(tmp_path))
    for item in results:
        assert isinstance(item, tuple) and len(item) == 2
        kind, value = item
        assert kind in ("unc", "drive", "subst")
        assert isinstance(value, str) and value


def test_posix_or_failure_returns_empty(monkeypatch):
    # Simulate non-Windows: the primitive must return [] (no mechanisms).
    import unctools.detector as det

    monkeypatch.setattr(det, "IS_WINDOWS", False)
    assert det.path_variants(r"C:\anything") == []


def test_never_raises_on_garbage():
    assert isinstance(path_variants(""), list)
    assert isinstance(path_variants("::::not a path::::"), list)


# --- subst: live end-to-end (AC-A) -------------------------------------------

def test_subst_expansion_is_kinded_and_real(subst_drive, tmp_path):
    inside = tmp_path / "inside.txt"
    inside.write_text("x", encoding="utf-8")

    alias_path = f"{subst_drive}\\inside.txt"
    results = path_variants(alias_path)
    subst_variants = [(k, v) for k, v in results if k == "subst"]
    assert len(subst_variants) == 1
    kind, value = subst_variants[0]
    # The value is the EXPANDED real path (mechanism provenance: kind='subst',
    # while the value itself is a plain local path).
    assert os.path.normcase(value) == os.path.normcase(str(inside))
    assert os.path.exists(value)
    # classify_path_origin(value) is 'local' BY DESIGN -- kind != form.
    assert unctools.classify_path_origin(value) in ("local", "unknown")


def test_get_subst_mappings_one_shot_and_cache_refresh(subst_drive, tmp_path):
    mappings = get_subst_mappings()
    assert subst_drive in mappings
    assert os.path.normcase(mappings[subst_drive]) == os.path.normcase(str(tmp_path))
    # get_subst_target agrees and works off the same enumeration.
    assert os.path.normcase(get_subst_target(subst_drive)) == os.path.normcase(str(tmp_path))
    # is_subst_drive True while mapped...
    assert unctools.is_subst_drive(subst_drive) is True


def test_stale_subst_cache_is_refreshed(tmp_path):
    if not IS_WINDOWS:
        pytest.skip("subst is Windows-only")
    letter = _free_drive_letter()
    if letter is None:
        pytest.skip("no free drive letter")
    drive = f"{letter}:"
    subprocess.run(["subst", drive, str(tmp_path)], check=True)
    try:
        assert unctools.is_subst_drive(drive) is True
    finally:
        subprocess.run(["subst", drive, "/d"], check=True)
    # Mapping removed: a fresh one-shot enumeration must CLEAR the stale True.
    get_subst_mappings()
    assert unctools.is_subst_drive(drive) is False
