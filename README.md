# UNCtools

[![PyPI](https://img.shields.io/pypi/v/unctools?color=green)](https://pypi.org/project/unctools/)
[![Release Date](https://img.shields.io/github/release-date/DazzleLib/UNCtools?color=green)](https://github.com/DazzleLib/UNCtools/releases)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](#platform-compatibility)

**Windows UNC path handling and network drive utilities: convert between `\\server\share` and mapped drives, classify where paths come from, and probe what's actually reachable.**

## The Problem

On Windows, the same file often has two names: the UNC form (`\\server\share\folder\file.txt`) and a mapped-drive form (`Z:\folder\file.txt`). Tools break when handed the one they didn't expect -- network drives disconnect, `subst` drives masquerade as real ones, security zones silently block UNC access, and scripts that worked on one machine fail on another because the drive mappings differ.

**UNCtools** answers the identity questions: *is this path UNC / network / subst / local -- and what is its other name?* It converts between path forms using the system's live mappings, classifies path origins, probes accessibility across both name variants, and (on Windows) manages the security zones and drive mappings themselves.

> [!NOTE]
> UNCtools is the **L0 path-identity layer** of the [DazzleLib stack](https://github.com/DazzleLib/.github/blob/main/docs/STACK-MAP.md): it may probe the filesystem read-only to answer identity questions; it never mutates or transfers content (file operations live in [dazzle-filekit](https://github.com/DazzleLib/dazzle-filekit)). The public surface is locked and machine-checked -- see [docs/api-stability.md](docs/api-stability.md).

## Quick Start

```bash
pip install unctools          # or equivalently: dazzle-unctools
```

```python
from unctools import convert_to_local, classify_path_origin

local = convert_to_local(r"\\server\share\project")   # -> Z:\project (if mapped)
origin = classify_path_origin(local)                  # -> "network"
```

## Features

- **Path conversion**: UNC ↔ mapped-drive translation from the system's live network mappings (win32net with `net use` fallback)
- **Origin classification**: `classify_path_origin` -- `unc` / `network` / `subst` / `local` / `removable` / `cdrom` / `ramdisk`
- **Identity probes**: existence and accessibility checks that try *both* name variants of a path
- **UNC path algebra**: parse and build `\\server\share\rest` components
- **Issue detection**: MAX_PATH violations, broken mappings, servers missing from the Intranet security zone
- **Windows management** (optional extra): security zones, share enumeration, drive mapping create/remove
- **Cross-platform safe**: imports everywhere; Windows-specific features degrade gracefully on Unix

## Installation

```bash
pip install unctools              # standard (or: dazzle-unctools)
pip install unctools[windows]     # + pywin32 for the rich Windows APIs
```

```bash
# Development
git clone https://github.com/DazzleLib/UNCtools.git
cd UNCtools
pip install -e .[dev]
```

## Usage

### Basic Path Conversion

```python
from unctools import convert_to_local, convert_to_unc

# Convert UNC path to local drive path
local_path = convert_to_local("\\\\server\\share\\folder\\file.txt")
# Result (if mapped): "Z:\\folder\\file.txt"

# Convert local drive path back to UNC
unc_path = convert_to_unc("Z:\\folder\\file.txt")
# Result: "\\\\server\\share\\folder\\file.txt"
```

### Path Detection

```python
from unctools import is_unc_path, is_network_drive, is_subst_drive, classify_path_origin

# Check if a path is a UNC path
if is_unc_path("\\\\server\\share\\file.txt"):
    print("This is a UNC path")

# Check if a drive is a network drive
if is_network_drive("Z:"):
    print("Z: is a network drive")

# Classify WHERE a path comes from
origin = classify_path_origin("C:\\Users\\")
# Result: "local", "network", "subst", "unc", etc.
```

### Identity Probes & Batch Conversion

```python
from unctools import file_exists, find_accessible_path, batch_convert

# Does the file exist under EITHER of its names (UNC or mapped)?
if file_exists("\\\\server\\share\\file.txt"):
    print("Reachable under at least one name")

# Which name variant actually works right now?
usable = find_accessible_path("\\\\server\\share\\file.txt")
# Result: Path("Z:\\file.txt"), Path("\\\\server\\share\\file.txt"), or None

# Convert multiple paths at once
paths = ["\\\\server\\share\\file1.txt", "\\\\server\\share\\file2.txt"]
converted = batch_convert(paths, to_unc=False)
```

### UNC Path Algebra

```python
from unctools import get_unc_path_elements, build_unc_path

server, share, rest = get_unc_path_elements("\\\\server\\share\\folder\\file.txt")
# Result: ("server", "share", "folder\\file.txt")

unc = build_unc_path("server", "share", "folder/file.txt")
# Result: "\\\\server\\share\\folder/file.txt"
```

### Windows Security Zones

```python
from unctools.windows import fix_security_zone, add_to_intranet_zone

# Fix security zone issues for a server
fix_security_zone("server")

# Add a server to the Local Intranet zone
add_to_intranet_zone("server")
```

### Network Drive Management

```python
from unctools.windows import create_network_mapping, remove_network_mapping

# Create a network drive mapping
success, drive = create_network_mapping("\\\\server\\share", "Z:")

# Remove a network drive mapping
remove_network_mapping("Z:")
```

## Platform Compatibility

| Platform | Status |
|----------|--------|
| Windows | Full functionality: conversion, classification, probes, security zones, drive management |
| Linux / macOS | Path algebra and syntax checks work; mapping-dependent features degrade gracefully (no-ops / passthrough) |

## Requirements

- **Python 3.6+** (3.9-3.13 tested in CI)
- **pywin32** (optional, via `unctools[windows]`) for the rich Windows APIs -- core features fall back to `net use` parsing without it

## Development

```bash
python -m pytest tests/   # 50+ tests; includes the api-stability import canary
black unctools
flake8 unctools
```

The public API surface is locked: see **[docs/api-stability.md](docs/api-stability.md)** for the policy, the active deprecation shims (`get_path_type` -> `classify_path_origin`, removed in 0.3.0), and known consumers. Changes follow the [stack's](https://github.com/DazzleLib/.github/blob/main/docs/STACK-MAP.md) noisy-shim deprecation policy -- never silent.

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

Like the project?

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/djdarcy)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
