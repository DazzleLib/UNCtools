"""DEPRECATED facade -- the operations module was dissolved in 0.2.0.

STACK-MAP D7 (probe-not-mutate): the path-identity layer may probe the
filesystem read-only, never mutate or transfer content. Accordingly:

- DELETED (content I/O has no home at L0): ``safe_open``, ``safe_copy``,
  ``batch_copy``, ``process_files``, ``replace_in_file``,
  ``batch_replace_in_files``. The retry-with-converted-path idea lives on as a
  documented on-demand capability for dazzle-filekit (L1), built when a real
  consumer needs it.
- MOVED to :mod:`unctools.converter` (path algebra): ``batch_convert``,
  ``get_unc_path_elements``, ``build_unc_path``.
- MOVED to :mod:`unctools.detector` (read-only identity probes):
  ``file_exists``, ``is_path_accessible``, ``find_accessible_path``.

This facade re-exports ONLY the moved survivors so straggling imports keep
working through 0.2.x, warns on import, and is REMOVED in 0.3.0. Import from
the top-level package (or the new homes) instead.
"""

import warnings

warnings.warn(
    "unctools.operations was dissolved in 0.2.0: probes moved to "
    "unctools.detector, path algebra to unctools.converter, and the "
    "content-I/O wrappers were removed (STACK-MAP D7). This facade module "
    "is removed in 0.3.0 -- import from the top-level package instead.",
    DeprecationWarning,
    stacklevel=2,
)

from .converter import batch_convert, build_unc_path, get_unc_path_elements  # noqa: E402,F401
from .detector import file_exists, find_accessible_path, is_path_accessible  # noqa: E402,F401

__all__ = [
    "batch_convert",
    "get_unc_path_elements",
    "build_unc_path",
    "file_exists",
    "is_path_accessible",
    "find_accessible_path",
]
