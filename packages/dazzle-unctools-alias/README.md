# dazzle-unctools (alias package)

This is an **alias package** (one inert breadcrumb module, no functionality): installing it installs
[`unctools`](https://pypi.org/project/unctools/) -- the
[DazzleLib](https://github.com/DazzleLib) stack's L0 path-identity library --
under the org's uniform `dazzle-*` naming.

```bash
pip install dazzle-unctools   # equivalent to: pip install unctools
```

**The import name is `unctools`:**

```python
from unctools import convert_to_local, classify_path_origin
```

Why this exists: the DazzleLib stack uses uniform `dazzle-*` dist names for
discoverability ([architecture contract](https://github.com/DazzleLib/.github/blob/main/docs/STACK-MAP.md),
decision D9a). Rather than rename a working library's import and repository,
the uniform name points at the real one -- the same pattern as
`dazzle-dz` -> `dazzlecmd`. If the library is ever truly renamed, that rename
ships as this dist's 1.0.

Report issues at [DazzleLib/UNCtools](https://github.com/DazzleLib/UNCtools/issues).
