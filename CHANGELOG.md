# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This file begins at 0.2.0 (the project predates it; 0.1.0 was the initial PyPI release).

UNCtools is the L0 path-identity layer of the
[DazzleLib stack](https://github.com/DazzleLib/.github/blob/main/docs/STACK-MAP.md):
it may PROBE the filesystem read-only to answer identity questions; it never
mutates or transfers content.

## [Unreleased]

## [0.3.0] -- 2026-07-30

### Added
- **`path_variants(path) -> [(kind, value)]`** -- the kinded, provenance-preserving variant primitive: enumerates a path's alternative names as `('unc', ...)` (drive->UNC), `('drive', ...)` (UNC->mapped drive), `('subst', ...)` (alias expanded to its underlying real path). **Kind is the mechanism-of-derivation, not the form-of-value** -- a subst expansion's value is a plain local path (`classify_path_origin(value) == 'local'` is correct by design); provenance is unrecoverable from the string form, which is why the primitive carries it. Derivations only: the input path is NOT included (unlike `dazzle_lib.PathVariantResolver.variants()`, which includes it -- documented cross-reference in the docstring). Never raises; `[]` on non-Windows. Built for the DazzleLib portable-paths train (dazzlelink#24): dazzle-linklib's locator population and live re-resolution consume it.
- **`get_subst_mappings()`** -- one-shot enumeration of ALL subst drives (single `subst` spawn), refreshing the detection cache for every drive letter consistently, so a removed subst mapping stops reporting stale `is_subst_drive(...) == True`.
- Top-level exports: `get_subst_target`, `get_network_target`, `get_subst_mappings`, `get_mappings`, `refresh_mappings`, `path_variants` (previously submodule-only or new).

### Changed
- `is_subst_drive` / `get_subst_target` now route through `get_subst_mappings()` -- one subprocess per enumeration instead of up to two per call, and cache-consistent (stale positives cleared on refresh).

### Deprecation schedule note
- The 0.2.0 notes slated the `get_path_type` shim and the `operations` re-export facade for **removal in 0.3.0**. They are consciously RETAINED through 0.3.x (this release is the portable-paths feature train; bundling breaking removals into it would couple unrelated blast radii) and are now slated for **0.4.0**.

## [0.2.2] -- 2026-06-17

### Added
- **`UNCConverter` WNetGetUniversalName enrichment**: `refresh_mappings()` now runs an additive pass (`_get_mappings_with_wnetuniversalname`) after the SMB net-use scan, using `win32wnet.WNetGetUniversalName` to resolve drives the LanmanWorkstation net-use table (`NetUseEnum` / `net use`) can miss -- those served by non-SMB / third-party network providers and some DFS/reconnect cases. It only adds drives not already mapped (authoritative net-use entries are never overwritten) and normalizes results to the module's conventions. Folds in the provider-chain coverage previously held by `dazzle-filekit.get_drive_mappings` (DazzleLib stack V9), so that copy can be retired without losing coverage.

## [0.2.1] -- 2026-06-16

### Changed
- Build: adopted the `git-repokit-common` subtree (`scripts/repokit-common/`) and its `_version.py` autobump versioning scheme -- the installed git hooks now auto-stamp build metadata on commit (resolves the git-hooks porting tracked in #1).

### Fixed
- Resolved 5 stale merge-conflict regions left in `.gitignore` by an old `origin/dev` merge; merged both sides as a deduplicated union, no ignore patterns dropped.

### Documentation
- Documented git-hook installation in CONTRIBUTING.md.

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

[Unreleased]: https://github.com/DazzleLib/UNCtools/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/DazzleLib/UNCtools/compare/v0.2.2...v0.3.0
[0.2.2]: https://github.com/DazzleLib/UNCtools/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/DazzleLib/UNCtools/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/DazzleLib/UNCtools/releases/tag/v0.2.0
