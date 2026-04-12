# Changelog

All notable changes to the License Compliance Checker project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- SBOM API endpoints (currently CLI-only due to library migration)
- Policy write operations via API (POST, PUT, DELETE endpoints)
- Email notifications for policy violations
- Slack/Teams integration for alerts
- Support for additional languages (PHP, Swift, Kotlin)
- Advanced SBOM features (vulnerability integration)

---

## [1.1.0] - 2026-04-12

### Security
- **POST /scans rate limited** — added `10/minute` rate limit; was previously unprotected
- **CORS default hardened** — changed from `"*"` to `""` (must be explicitly configured via `LCC_ALLOWED_ORIGINS`)
- **Admin reset scoped** — `/admin/reset` now only deletes LCC-namespaced Redis keys (`scan:*`, `lcc:*`), not `flushdb()`
- **Worker path containment** — scan paths validated to stay within `LCC_WORKSPACE` or system temp directory; prevents path traversal
- **Git history audited** — confirmed no secrets ever committed to repository

### Added

#### Agentic AI Era Capabilities
- **HuggingFace Hub API resolver** (`src/lcc/resolution/hf_hub_resolver.py`) — scans Python, YAML, and JSON files for model ID references (`from_pretrained("org/model")`, `model_name_or_path`, `--model` args) and fetches license/metadata from the HF API without requiring local download
- **GGUF/ONNX model detection** — `HuggingFaceDetector` now supports `.gguf` (Ollama/llama.cpp) and `.onnx` files; infers model family from filename; reads GGUF binary metadata header
- **Dataset risk registry** — 15 datasets classified with commercial use risk; OpenAI API outputs, ChatGPT, ShareGPT, Books3, and The Pile flagged as high/critical risk with explanatory notes
- **`--include-transitive` CLI flag** — surfaces transitive dependency analysis with lock file validation and guidance when no lock file is present

#### Regulatory
- **Honest Article 53 framing** — `ARTICLE_53_SCOPE_NOTE` added to all EU AI Act assessment outputs; clearly states this is audit evidence for documentation obligations, not a full legal compliance determination

### Fixed
- `datetime.utcnow()` → `datetime.now(UTC)` in `database/models.py` (Python 3.12 deprecation)
- `warnings_count` now computed via `WarningAnalyzer.analyze_scan()` in the scan worker — was always 0 previously
- `GET /scans/{id}/warnings` returns real warning analysis instead of an empty stub
- Performance tests: corrected `Scanner(detectors, resolvers, config)` constructor signature (was passing wrong argument order)
- Performance tests: corrected `scanner.scan(project_root=Path(...))` call signature
- Integration tests: removed `500` from acceptable status codes — unhandled server errors are no longer considered passing
- `tests/performance/test_resolver_performance.py`: replaced non-existent `PackageInfo` with `Component(type=ComponentType.PYPI/NPM, ...)`
- GitHub Actions: removed invalid `secrets` context from `if:` conditions in `publish-pypi.yml` and `test-pypi.yml`
- GitHub Actions: license scan step changed from hard-fail to warning-only for dev dependency violations

### Tests
- 393 tests passing (was 228 in v1.0.0)
- Added: `tests/detection/test_hf_reference_detector.py` (23 tests)
- Added: `tests/detection/test_gguf_detection.py` (10 tests)
- Added: `tests/regulatory/test_dataset_risk_registry.py` (23 tests)

---

## [1.0.0] - 2026-02-06

### Added
- FastAPI-based REST API with JWT authentication and role-based access control
- Async scan worker using ARQ + Redis for background job processing
- PostgreSQL persistence via async SQLAlchemy
- Multi-ecosystem detection: Python, Node.js, Go, Rust, Ruby, Java/Gradle, .NET
- HuggingFace model and dataset detection with model card parsing
- AI-specific license registry: RAIL, OpenRAIL, Llama, Gemma, Mistral, BigScience and more
- EU AI Act Article 53 regulatory assessor
- NIST AI RMF, ISO 42001, and US EO 14110 framework scaffolding
- CycloneDX and SPDX SBOM generation
- CLI with Rich output, JSON/SARIF/CSV formats
- Prometheus metrics, structured JSON logging, request trace IDs
- Docker Compose production deployment
- GitHub Actions CI with Python 3.11 + 3.12 matrix

---

## [0.3.0] - 2024-10-30 - Phase 3: AI-Native

### Added

#### AI/ML Support
- **Hugging Face Model Detection**: Automatic detection of models from Hugging Face Hub
- **Hugging Face Dataset Detection**: Detection of datasets with license information
- **AI License Support**: 17+ AI-specific licenses (OpenRAIL variants, Llama 2/3/3.1, Gemma, etc.)
- **Dataset License Support**: 15+ dataset licenses (Creative Commons, ODC, CDLA, ImageNet, COCO, etc.)
- **AI/ML Policies**: Three AI-specific policy templates (research, permissive, strict)

#### SBOM Generation
- **CycloneDX Support**: Generate CycloneDX 1.5 format SBOMs
- **SPDX Support**: Generate SPDX 2.3 format SBOMs
- **Multiple Output Formats**: JSON, XML, YAML, and tag-value formats
- **CLI Commands**: Complete SBOM generation via CLI (`lcc sbom`)
- **Metadata Enrichment**: Project name, version, author, supplier metadata

#### REST API
- **FastAPI Backend**: Modern, high-performance API server
- **JWT Authentication**: Secure token-based authentication
- **User Management**: Create users, manage roles, API keys
- **Scan Endpoints**: Create scans, list scans, get scan details
- **Policy Endpoints**: List policies, get policy details
- **Dashboard Endpoint**: Aggregated statistics for visualization
- **GitHub Integration**: Scan repositories directly via URL
- **Rate Limiting**: 100 requests/minute per endpoint
- **OpenAPI Documentation**: Interactive API docs at `/docs`

#### Professional Dashboard
- **Next.js 14 App Router**: Modern React-based web interface
- **Authentication**: Secure login with JWT tokens
- **Scans Page**: List all scans with filtering and search
- **Scan Details**: Detailed findings view with violations and warnings
- **Policies Page**: View and explore policy configurations
- **Analytics Page**: License distribution, trends, compliance metrics
- **Dashboard**: Overview with statistics and visualizations
- **SBOM Page**: Instructions and CLI commands for SBOM generation
- **Account Page**: User profile and settings
- **Dark Mode**: Full dark mode support with theme toggle
- **Responsive Design**: Mobile-friendly interface

#### Documentation
- **USER_GUIDE.md**: Comprehensive user guide (700+ lines)
- **POLICY_GUIDE.md**: Policy creation and management guide (550+ lines)
- **API_GUIDE.md**: Complete REST API documentation (800+ lines)
- **TROUBLESHOOTING.md**: Common issues and solutions (450+ lines)
- **FAQ.md**: Frequently asked questions (350+ lines)
- **CONTRIBUTING.md**: Contribution guidelines (330+ lines)
- **VIDEO_SCRIPT.md**: Video tutorial script (400+ lines)
- **CHANGELOG.md**: This file

### Changed
- **Multi-Source Resolution**: Enhanced resolution chain with ClearlyDefined, GitHub, and filesystem
- **Policy System**: Extended policy syntax with AI-specific license support
- **Detection System**: Improved detector architecture for AI/ML components
- **CLI Enhancement**: Added `sbom` subcommand for SBOM generation
- **Configuration**: Extended config.yaml with AI-specific settings

### Fixed
- GitHub rate limit handling with retry-after support
- SPDX expression parsing for complex dual licenses
- License detection accuracy for AI models
- Database connection handling in multi-threaded scenarios
- CORS configuration for dashboard-API communication

### Tests
- 87+ Phase 3 tests with 100% pass rate
- AI model detection tests
- Dataset detection tests
- SBOM generation tests (CycloneDX and SPDX)
- API endpoint tests
- Authentication tests
- Policy evaluation tests with AI licenses

---

## [0.2.0] - 2024-10-15 - Phase 2: Advanced Features

### Added
- **GitHub Resolver**: License resolution from GitHub API
- **ClearlyDefined Resolver**: Curated license data from ClearlyDefined
- **Custom Resolvers**: Support for custom resolution logic
- **Multi-Source Resolution**: Chained resolution with fallback
- **Policy Contexts**: Multiple contexts per policy (dev, prod, etc.)
- **Dual-License Handling**: Preferences for dual-licensed components
- **YAML Policies**: Human-readable policy files
- **Policy Validation**: `lcc policy validate` command
- **Policy Listing**: `lcc policy list` command
- **HTML Reporter**: Generate HTML compliance reports
- **Markdown Reporter**: Generate Markdown reports
- **Report Templates**: Customizable report templates
- **SQLite Database**: Persistent storage for scan results
- **Caching System**: TTL-based cache for resolver results
- **Configuration File**: `~/.lcc/config.yaml` for settings
- **Environment Variables**: Support for `LCC_*` env vars
- **Verbose Logging**: `--verbose` flag for debugging

### Changed
- Improved CLI output with colors and formatting
- Enhanced error messages and debugging info
- Optimized scanning performance (2-3x faster)
- Better handling of malformed package files

### Fixed
- Memory leaks in long-running scans
- Concurrent resolver race conditions
- Unicode handling in license texts
- Windows path compatibility issues

---

## [0.1.0] - 2024-10-01 - Phase 1: Foundation

### Added
- **Initial Release**: First public version of LCC
- **Multi-Language Detection**: Python, JavaScript, Go, Rust, Java, Ruby, .NET
- **Package Manager Support**: npm, pip, Cargo, Maven, Gradle, Bundler, NuGet
- **Registry Resolver**: License resolution from PyPI, npm, crates.io
- **Basic Policy Engine**: Simple allow/deny lists
- **CLI Tool**: `lcc scan` command for scanning projects
- **JSON Reporter**: Machine-readable scan results
- **Console Reporter**: Human-readable terminal output
- **Docker Support**: Official Docker images
- **Documentation**: README with basic usage instructions
- **GitHub Repository**: Open-source repository with Apache-2.0 license

### Detectors
- **Python**: pip, requirements.txt, pyproject.toml, setup.py, Pipfile
- **JavaScript**: npm, yarn, pnpm, package.json, package-lock.json
- **Go**: go.mod, go.sum
- **Rust**: Cargo.toml, Cargo.lock
- **Java**: Maven (pom.xml), Gradle (build.gradle)
- **Ruby**: Gemfile, Gemfile.lock
- **.NET**: .csproj, packages.config

### Resolvers
- **PyPI Resolver**: License info from PyPI registry
- **npm Resolver**: License info from npm registry
- **Crates.io Resolver**: License info from Rust registry
- **Filesystem Resolver**: LICENSE file detection

---

## Release Notes

### Version Numbering

LCC follows [Semantic Versioning](https://semver.org/):
- **MAJOR** version (X.0.0): Incompatible API changes
- **MINOR** version (0.X.0): New features, backwards compatible
- **PATCH** version (0.0.X): Bug fixes, backwards compatible

### Upgrading

#### From 0.2.x to 0.3.x

**Breaking Changes**:
- SBOM API endpoints temporarily disabled (use CLI instead)
- Policy file format unchanged (fully compatible)
- Database schema updated (automatic migration on first run)

**New Features**:
- AI/ML license detection
- Professional web dashboard
- REST API with authentication
- SBOM generation (CycloneDX and SPDX)

**Upgrade Steps**:
```bash
# Backup database
cp ~/.lcc/lcc.db ~/.lcc/lcc.db.backup

# Pull latest Docker images
docker-compose pull

# Restart services
docker-compose down
docker-compose up -d

# Or upgrade via pip
pip install --upgrade license-compliance-checker

# Create admin user for dashboard
lcc auth create-user admin password123 --role admin
```

#### From 0.1.x to 0.2.x

**Breaking Changes**:
- Policy file format changed from JSON to YAML
- CLI flag `--policy-file` renamed to `--policy`

**Migration**:
```bash
# Convert policy from JSON to YAML
# Old (0.1.x): policy.json
# New (0.2.x): policy.yaml

# Manual conversion needed
```

---

## Deprecation Notices

### Deprecated in 0.3.0
- **SBOM API Endpoints**: Temporarily disabled due to cyclonedx-python-lib v11.x migration
  - **Alternative**: Use `lcc sbom` CLI commands
  - **Timeline**: Will be re-enabled in 0.4.0
  - **Impact**: API users should use CLI for SBOM generation

### Removed in 0.3.0
- None

### Planned for Deprecation
- **SQLite-only support**: PostgreSQL support planned for 1.0.0
- **Single-instance deployment**: Multi-instance support planned for 1.0.0

---

## Security

### Security Updates

If you discover a security vulnerability, please email security@lcc.dev. Do not open a public issue.

**Response Timeline**:
- Acknowledgment: Within 24 hours
- Fix: Within 7 days for critical issues
- Disclosure: Coordinated disclosure after fix is released

### Known Security Issues
- None at this time

---

## Contributors

Thank you to all contributors who helped with this release!

### Phase 3 (0.3.0) Contributors
- Core team: [List maintainers]
- Community contributors: [List contributors]
- Special thanks: [List special acknowledgments]

### How to Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to LCC.

---

## Links

- **Homepage**: https://lcc.dev
- **Documentation**: https://docs.lcc.dev
- **GitHub**: https://github.com/aiexponenthq/license-compliance-checker
- **Issue Tracker**: https://github.com/aiexponenthq/license-compliance-checker/issues
- **Discussions**: https://github.com/aiexponenthq/license-compliance-checker/discussions
- **Docker Hub**: https://hub.docker.com/r/lcc/lcc
- **PyPI**: https://pypi.org/project/license-compliance-checker/

---

## Acknowledgments

### Open Source Dependencies

LCC is built on the shoulders of giants. Thank you to:

- **FastAPI**: Modern Python web framework
- **Next.js**: React framework for the dashboard
- **shadcn/ui**: Beautiful UI components
- **CycloneDX**: SBOM standard and Python library
- **SPDX**: SBOM standard and Python tools
- **Hugging Face**: Model and dataset hub APIs
- **ClearlyDefined**: Curated license data
- **GitHub**: API for license detection
- And many more amazing open source projects!

### Inspiration

LCC was inspired by:
- **FOSSA**: Commercial license compliance tool
- **Snyk**: Vulnerability and license scanning
- **Black Duck**: Enterprise license compliance
- **SPDX Tools**: License scanning and SBOM generation

---

*For questions about this changelog, contact support@lcc.dev*
