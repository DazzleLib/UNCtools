"""WNetGetUniversalName provider-chain enrichment (STACK-MAP V9 fold).

NetUseEnum / ``net use`` reflect the SMB (LanmanWorkstation) net-use table and
can miss drives served by non-SMB / third-party network providers and some
DFS/reconnect cases. ``win32wnet.WNetGetUniversalName`` walks the WNet Multiple
Provider Router and resolves those. This is the capability folded in from
dazzle-filekit's ``get_drive_mappings`` before that copy is removed (V9).

These tests mock win32wnet so they run on any platform.
"""
from unittest import mock

from unctools import converter as conv_mod
from unctools.converter import UNCConverter


def _make_converter():
    c = UNCConverter(refresh_on_init=False)
    c._is_windows = True  # exercise the Windows path regardless of host OS
    return c


def test_wnet_adds_drive_netuse_missed(monkeypatch):
    """A drive only WNet can resolve is folded in, normalized, exactly once."""
    c = _make_converter()
    # NetUseEnum already found Z: -> \\server\share (authoritative).
    c._mapping = {"\\\\server\\share": "Z:\\"}
    c._reverse_mapping = {"Z:": "\\\\server\\share"}

    def fake_universal(drive, level):
        # WNet resolves a DFS/third-party drive T: that net-use missed.
        # Returns mixed-case, no trailing slash -- must be normalized.
        if drive == "T:":
            return "\\\\DFSRoot\\Team"
        raise Exception("not a network drive")

    fake = mock.Mock()
    fake.WNetGetUniversalName.side_effect = fake_universal
    monkeypatch.setattr(conv_mod, "win32wnet", fake, raising=False)
    monkeypatch.setattr(conv_mod, "HAVE_WIN32WNET", True)

    c._get_mappings_with_wnetuniversalname()

    # T: added once, normalized to module conventions.
    assert c._reverse_mapping["T:"] == "\\\\dfsroot\\team"
    assert c._mapping["\\\\dfsroot\\team"] == "T:\\"
    # The pre-existing authoritative Z: entry is untouched.
    assert c._reverse_mapping["Z:"] == "\\\\server\\share"
    # Exactly two drives mapped (Z: + T:), no duplicates.
    assert len(c._reverse_mapping) == 2


def test_wnet_does_not_overwrite_netuse(monkeypatch):
    """A drive already known from net-use is skipped before WNet is queried."""
    c = _make_converter()
    c._mapping = {"\\\\server\\share": "Z:\\"}
    c._reverse_mapping = {"Z:": "\\\\server\\share"}

    fake = mock.Mock()
    fake.WNetGetUniversalName.side_effect = Exception("nothing resolves")
    monkeypatch.setattr(conv_mod, "win32wnet", fake, raising=False)
    monkeypatch.setattr(conv_mod, "HAVE_WIN32WNET", True)

    c._get_mappings_with_wnetuniversalname()

    # Z: keeps the authoritative net-use value.
    assert c._reverse_mapping == {"Z:": "\\\\server\\share"}
    # Z: was never even queried (skip-before-call -- no overwrite possible).
    queried = [call.args[0] for call in fake.WNetGetUniversalName.call_args_list]
    assert "Z:" not in queried


def test_wnet_ignores_non_unc_results(monkeypatch):
    """A non-UNC WNet result (e.g. a local path) is ignored."""
    c = _make_converter()
    c._mapping = {}
    c._reverse_mapping = {}

    def fake_universal(drive, level):
        if drive == "Q:":
            return "C:\\local\\path"  # not a UNC -- must be skipped
        raise Exception("not a network drive")

    fake = mock.Mock()
    fake.WNetGetUniversalName.side_effect = fake_universal
    monkeypatch.setattr(conv_mod, "win32wnet", fake, raising=False)
    monkeypatch.setattr(conv_mod, "HAVE_WIN32WNET", True)

    c._get_mappings_with_wnetuniversalname()
    assert c._reverse_mapping == {}
    assert c._mapping == {}


def test_wnet_noop_without_module(monkeypatch):
    """No win32wnet -> the enrichment is a safe no-op."""
    c = _make_converter()
    c._mapping = {}
    c._reverse_mapping = {}
    monkeypatch.setattr(conv_mod, "HAVE_WIN32WNET", False)
    c._get_mappings_with_wnetuniversalname()  # must not raise
    assert c._reverse_mapping == {}
