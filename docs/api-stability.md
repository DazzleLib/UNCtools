# API Stability

UNCtools is the L0 path-identity layer of the
[DazzleLib stack](https://github.com/DazzleLib/.github/blob/main/docs/STACK-MAP.md).
Its public surface is locked and machine-checked by
`tests/test_import_stability.py` -- if that canary fails, a consumer somewhere
breaks: follow the policy below, never silently fix the test.

## Policy

1. **Locked symbols never vanish silently.** Removal/rename ships a NOISY
   `DeprecationWarning` shim naming the new home and removal version,
   registered in the stack's alias register, removed on schedule.
2. **The layer charter is not negotiable** (STACK-MAP rule 3a): this library
   may probe the filesystem read-only to answer identity questions; it never
   mutates or transfers content. Functions that do are rejected, not deprecated.
3. **Name hygiene** (STACK-MAP rule 7): before exporting a public symbol,
   grep the stack -- same-name-different-semantics requires a layer-teaching
   rename (that is how `classify_path_origin` got its name).

## Locked surface (0.2.0)

| Module | Symbols |
|---|---|
| `unctools` (top level) | `convert_to_local`, `convert_to_unc`, `batch_convert`, `get_unc_path_elements`, `build_unc_path`, `is_unc_path`, `is_network_drive`, `is_subst_drive`, `classify_path_origin`, `get_network_mappings`, `detect_path_issues`, `file_exists`, `is_path_accessible`, `find_accessible_path`, `configure_logging`, `get_version` |
| `unctools.converter` | `UNCConverter`, `convert_to_local`, `convert_to_unc`, `batch_convert`, `get_unc_path_elements`, `build_unc_path`, `refresh_mappings`, `get_mappings`, `parse_unc_path`, `join_unc_path` |
| `unctools.detector` | the origin classifiers + probes listed above, plus `get_drive_type`, `get_subst_target`, `get_network_target`, `is_server_in_intranet_zone` |
| `unctools.windows.*` | Windows-only security/network/registry surface (unchanged in 0.2.0) |

## Active deprecations

| Symbol | Replacement | Warns since | Removed in |
|---|---|---|---|
| `get_path_type` | `classify_path_origin` | 0.2.0 | 0.3.0 |
| `unctools.operations` (module facade) | top-level imports / `converter` / `detector` | 0.2.0 | 0.3.0 |

## Known consumers

| Consumer | Symbols | Notes |
|---|---|---|
| dazzlecmd (`safedel/_volumes.py`, `fixpath.py`) | `get_drive_type`, `is_network_drive`, `is_unc_path`, `convert_to_local` | optional imports today; harden in stack P4 |
| dazzlesum | top-level conversion/probe block | soft-imports today; harden in stack P4 |
| modified_datetime_fix | mixed (incl. a vendored copy to retire) | stack P4 |
| dazzle-filekit | `[unctools]` extra pin (no runtime import) | becomes a real edge only if/when filekit consumes identity at runtime |

## Consolidation candidates (0.3.0)

- `parse_unc_path`/`join_unc_path` vs `get_unc_path_elements`/`build_unc_path`
  (near-duplicates; the latter preserve forward slashes in the relative part)
- dazzle-lib adoption: derive errors from `dazzle_lib.PathIdentityError`
  (deliberately deferred from 0.2.0 to keep the surgery diff reviewable)
