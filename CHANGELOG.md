# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - Phase 1-10 Implementation

**Infrastructure (Phase 1-5)**
- ✅ Project structure with modular architecture
- ✅ Apptainer containerization (koocad.def, koocad-dev.def)
- ✅ CI/CD pipeline with GitHub Actions
- ✅ Pre-commit hooks (black, ruff, mypy, bandit)
- ✅ Master plan document (145 phases)

**Core Modules (Phase 1-5)**
- ✅ Parameter system (645 lines)
  - FloatParameter, IntParameter, BoolParameter, EnumParameter
  - ExpressionParameter with dependency resolution
  - ParameterSet with constraint validation
  - Unit conversion (mm, inch, mil, µm, cm, m)
- ✅ Shape abstraction layer
  - Unified interface for CadQuery/OCCT
  - Boolean operations (union, intersect, subtract)
  - Export methods (STEP, IGES, STL, GLB)
  - Transformations (translate, rotate, mirror)

**Observability Stack (Phase 6-8)**
- ✅ Structured logging with structlog
  - JSON and console output formats
  - Context injection (request_id, user_id)
  - Log level filtering
- ✅ Prometheus metrics collection
  - Operation counters and duration histograms
  - CAD generation metrics
  - Export size tracking
  - Job queue monitoring
- ✅ OpenTelemetry distributed tracing
  - Span creation and propagation
  - Automatic context injection
  - OTLP exporter integration

**Testing & Quality (Phase 9-10)**
- ✅ Test data factories (Faker-based)
  - BGAParameterFactory
  - MLCCParameterFactory
  - ParameterSweepFactory (Cartesian, Random)
- ✅ Performance benchmarking utilities
  - Execution time measurement
  - Memory usage tracking
  - CPU utilization monitoring
  - Regression detection
- ✅ Security utilities
  - SecretsManager (Fernet encryption)
  - ParameterValidator (path traversal, command injection)
  - APIKeyManager (generation, hashing, verification)
  - AuditLogger (access logging)

**Configuration Management**
- ✅ Pydantic settings with environment variables
  - Database, Redis, MinIO configuration
  - Celery task queue settings
  - Logging, tracing, security settings
  - CAD kernel and mesh engine configuration

**Documentation**
- ✅ ARCHITECTURE.md (600 lines) - Technical design
- ✅ MASTER_PLAN.md (845 lines) - 145 phase roadmap
- ✅ HPC_DEPLOYMENT.md (389 lines) - HPC deployment guide
- ✅ CONTRIBUTING.md - Developer guidelines

**Examples**
- ✅ 01_basic_parameters.py - Parameter system usage
- ✅ 02_logging_and_metrics.py - Observability demo
- ✅ 03_test_data_generation.py - Test data factories

### Code Statistics
- **Source code**: 13 files, 2,574 lines
- **Tests**: 3 test suites, 632 lines
- **Documentation**: 2,234 lines
- **Total**: 5,440+ lines of production code

### Changed
- Migrated from Docker to Apptainer for HPC optimization
- Updated CI/CD to build Apptainer containers
- Enhanced README with Apptainer installation guide

### Removed
- Docker Compose configuration (replaced by Apptainer)
- Dockerfile.dev (replaced by koocad-dev.def)

### Security
- Encryption for sensitive parameters
- Path traversal protection
- Command injection validation
- API key hashing with PBKDF2
- Audit logging for access control

---

## [0.1.0] - 2025-11-10

### Added
- Project initialization
- Basic infrastructure setup
- Documentation framework

---

[Unreleased]: https://github.com/yourusername/KooCADImGUI/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/KooCADImGUI/releases/tag/v0.1.0
