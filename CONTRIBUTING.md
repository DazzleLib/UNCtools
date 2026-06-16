# Contributing to UNCtools

Thank you for considering contributing to UNCtools! We welcome contributions from everyone.

## Code of Conduct

Please note that this project is released with a Contributor Code of Conduct.
By participating in this project you agree to abide by its terms.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When you create a bug report, please include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples** to demonstrate the steps
- **Describe the behavior you observed** and what you expected
- **Include Python version, OS (Windows version especially), and UNCtools version**
- **Include code samples** that demonstrate the issue
- **Note whether pywin32 is installed** (especially for Windows-specific features)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide a detailed description** of the suggested enhancement
- **Provide specific examples** to demonstrate the use case
- **Explain why this enhancement would be useful**
- **Consider platform implications** (Windows-specific vs cross-platform)

### Contributing Code

#### First Time Contributors

- Look for issues labeled `good first issue` or `help wanted`
- Read the [README](README.md) to understand the project's purpose
- Understand UNC path concepts if working on Windows-specific features

#### Development Setup

1. **Fork the repository**
2. **Clone your fork**:
   ```bash
   git clone https://github.com/your-username/UNCtools.git
   cd UNCtools
   ```

3. **Create a virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/Mac
   python -m venv venv
   source venv/bin/activate
   ```

4. **Install in development mode**:
   ```bash
   pip install -e ".[dev]"
   ```

5. **Install pywin32 (Windows only)**:
   ```bash
   # On Windows, this should install automatically via setup.py
   # If not, install manually:
   pip install pywin32
   ```

#### Git Hooks (recommended)

UNCtools uses shell-based git hooks (vendored via the `git-repokit-common` subtree at `scripts/repokit-common/`) for automatic version stamping and basic safety checks. They are POSIX shell scripts, so they avoid the Python-path import issues of interpreter-based hooks. Install them once after cloning:

```bash
bash scripts/repokit-common/install-hooks.sh
```

What they do:

- **pre-commit** -- stamps build metadata into `unctools/_version.py` (`sync-versions.py --auto`), protects private content, and blocks accidentally-committed large files
- **post-commit** -- updates the version hash after the commit lands
- **pre-push** -- Python syntax check, runs the test suite, and flags leftover debug statements

The hooks keep the auto-generated `__version__` string in sync, so you never edit it by hand -- bump a release by editing only the `MAJOR`/`MINOR`/`PATCH` constants in `unctools/_version.py`.

#### Pull Request Process

1. **Create a new branch** from `dev` (not `main`):
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed
   - Ensure Windows/Linux compatibility where applicable

3. **Test your changes**:
   ```bash
   # Run tests
   python -m pytest tests/ -v

   # Run with coverage
   python -m pytest tests/ -v --cov=unctools --cov-report=term-missing

   # Test on Windows with UNC paths if possible
   ```

4. **Update documentation**:
   - Update README.md if adding new features
   - Add docstrings to new functions/classes
   - Include usage examples for significant features

5. **Commit your changes**:
   - Use clear, descriptive commit messages
   - Reference any related issues
   - Follow conventional commit format if possible

6. **Push and create PR**:
   - Push to your fork
   - Create PR against `dev` branch (not `main`)
   - Fill out the PR template completely
   - Link any related issues

### Development Guidelines

#### Code Style

- Follow PEP 8
- Use type hints for all new code
- Document all public APIs
- Keep line length under 100 characters
- Use black for formatting: `black unctools tests`

#### Testing Requirements

- All new features must have tests
- Maintain or improve code coverage
- Test on Windows when working with UNC path features
- Include edge cases and error conditions
- Test both with and without pywin32 when applicable

#### Windows-Specific Considerations

When developing Windows features:

1. **Test on actual Windows** when possible (not just WSL)
2. **Use pywin32 for advanced functionality** (but provide fallbacks)
3. **Handle UNC paths correctly** (//server/share format)
4. **Consider network drives and SUBST drives**
5. **Test with various network configurations** (domain, workgroup, standalone)

#### Cross-Platform Guidelines

- **Provide fallbacks** for Windows-specific features on Linux/Mac
- **Use os.path and pathlib** for maximum compatibility
- **Test on multiple platforms** when possible
- **Document platform-specific behavior** clearly

### Documentation

- Use clear, concise language
- Include code examples
- Keep README focused, use separate docs for details
- Document Windows-specific vs cross-platform features clearly

### Questions?

Feel free to:
- Open a discussion on GitHub
- Ask questions in issues
- Review existing documentation

## Recognition

Contributors will be recognized in:
- The project README acknowledgments
- Release notes for their contributions
- GitHub contributors page

## Branch Strategy

UNCtools uses a simple branch strategy:

- **`main`** - Stable, production-ready code
- **`dev`** - Development branch (target for PRs)
- **`private`** - Local development only (not on GitHub)

**Always create PRs against the `dev` branch, not `main`.**

## Release Process

Releases are managed by project maintainers:

1. Changes merged to `dev`
2. Testing and validation
3. Merge `dev` to `main`
4. Create GitHub release with tag
5. Automatic PyPI publication via GitHub Actions

Thank you for helping make UNCtools better!
