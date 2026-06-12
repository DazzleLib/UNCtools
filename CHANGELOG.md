# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This file begins at 0.2.0 (the project predates it; 0.1.0 was the initial PyPI release).

UNCtools is the L0 path-identity layer of the
[DazzleLib stack](https://github.com/DazzleLib/.github/blob/main/docs/STACK-MAP.md):
it may PROBE the filesystem read-only to answer identity questions; it never
mutates or transfers content.

## [Unreleased]

## [0.2.0] -- 2026-06-11

The probe-not-mutate release (stack phase P1, [#3](https://github.com/DazzleLib/UNCtools/issues/3)).
Aligns the library with the frozen DazzleLib architecture contract: content I/O
moves up a layer, names teach the layer model, and the `dazzle-unctools`
pointer dist makes the library discoverable under the org's uniform naming.

### Removed (breaking)
- **Content-I/O wrappers** (`safe_open`, `safe_copy`, `batch_copy`,
  `process_files`, `replace_in_file`, `batch_replace_in_files`): file I/O has
  no home in the identity layer. Zero external consumers (verified by the
  stack audit). The retry-with-converted-path idea lives on as a documented
  on-demand capability for dazzle-filekit.
- **`normalize_path(prefer_unc=)`**: the explicit `convert_to_local` /
  `convert_to_unc` ARE the API; the direction-switch wrapper collided with
  other libraries' `normalize_path` semantics.
- **`path_exists_case_sensitive` / `get_case_sensitive_path`** (internal,
  never exported): path-case canonicalization is format-normalization work and
  merges into dazzle-filekit.

### Changed
- **`get_path_type` renamed `classify_path_origin`**: it classifies WHERE a
  path comes from (`unc`/`network`/`subst`/`local`/...). The old name remains
  as a DEPRECATED warning shim through 0.2.x (removed in 0.3.0). The rename
  resolves the semantic collision with dazzle-filekit's `get_path_type`
  (which classifies WHAT a filesystem object is).
- **`operations` module dissolved**: read-only identity probes
  (`file_exists`, `is_path_accessible`, `find_accessible_path`) moved to
  `detector`; path algebra (`batch_convert`, `get_unc_path_elements`,
  `build_unc_path`) moved to `converter`. The module remains as a deprecated
  re-export facade for the survivors through 0.2.x (removed in 0.3.0). The
  top-level `unctools` namespace is unchanged for all surviving symbols.

### Added
- **`dazzle-unctools` pointer dist**: a codeless PyPI package depending on
  `unctools` -- installs the same library under the org's uniform `dazzle-*`
  name (install either; the import is `unctools`). Permanent by design.
- **`docs/api-stability.md`** + import-stability canary
  (`tests/test_import_stability.py`): the public surface is now locked and
  machine-checked; changes follow the deprecation policy, never silent.
- This CHANGELOG.

[Unreleased]: https://github.com/DazzleLib/UNCtools/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/DazzleLib/UNCtools/releases/tag/v0.2.0
