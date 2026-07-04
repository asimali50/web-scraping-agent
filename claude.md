# Web Scraping Agent - Project Documentation

A production-grade multi-agent web scraping system that discovers brand websites and collects product information from Amazon, Google, and brand websites.

## Quick Navigation

### 📋 Project Overview
- **[Project Status](docs/PROJECT_STATUS.md)** - Current state, architecture overview, and system capabilities
- **[Final Implementation Report](docs/FINAL_IMPLEMENTATION_REPORT.md)** - Complete technical summary and architecture decisions

### 🎯 Development Phases

#### Phase 2: Foundation
- **[Phase 2 Completion](docs/PHASE2_COMPLETION.md)** - Project skeleton, configuration, logging, database, browser service, and data models

#### Phase 3: Core Agents
- **[Phase 3 Completion](docs/PHASE3_COMPLETION.md)** - 6 core agents (Amazon, Google, Website, Matching, Cache) + orchestrator for brand website detection pipeline

#### Phase 4: Production Features
- **[Phase 4 Completion](docs/PHASE4_COMPLETION.md)** - Sheet integration, batch processing, report generation, and CLI interface for production deployment

#### Phase 5: Integration & Deployment
- **[Phase 5 Completion](docs/PHASE5_COMPLETION.md)** - Integration, execution framework, progress tracking, checkpoints, and error recovery
- **[Phase 5 Final Report](docs/PHASE5_FINAL_REPORT.md)** - Final status and deployment readiness
- **[Phase 5 Progress Report](docs/PHASE5_PROGRESS_REPORT.md)** - Detailed progress tracking
- **[Phase 5 Summary](docs/PHASE5_SUMMARY.md)** - Executive summary of Phase 5 work

### 🚀 Deployment & Configuration

- **[Final Deployment Checklist](docs/FINAL_DEPLOYMENT_CHECKLIST.md)** - Pre-deployment verification and checklist
- **[Playwright Installation Complete](docs/PLAYWRIGHT_INSTALLATION_COMPLETE.md)** - Browser automation setup verification

### 🔍 Testing & Validation

- **[Runtime Audit Report](docs/RUNTIME_AUDIT_REPORT.md)** - Performance metrics, error analysis, and system validation
- **[Test Sample Data](docs/TEST_SAMPLE_DATA.json)** - Sample test inputs and expected outputs

### 📊 Logs & Diagnostics

- **[Installation Attempt Log](docs/install_attempt.log)** - Dependency installation logs
- **[Playwright Installation Log](docs/playwright_install.log)** - Browser driver installation logs

## Project Structure

```
web-scraping-agent/
├── src/
│   ├── agents/              # 6 core agent implementations
│   │   ├── amazon_agent.py
│   │   ├── google_agent.py
│   │   ├── website_agent.py
│   │   ├── matching_agent.py
│   │   ├── cache_agent.py
│   │   └── sheet_agent.py
│   ├── services/            # Core services
│   │   ├── browser_service.py
│   │   ├── cache_service.py
│   │   ├── checkpoint_service.py
│   │   ├── error_recovery.py
│   │   ├── logger_service.py
│   │   └── progress_service.py
│   ├── processors/          # Processing pipeline
│   │   ├── orchestrator.py
│   │   ├── batch_processor.py
│   │   └── report_generator.py
│   ├── core/                # Core configurations
│   │   ├── config.py
│   │   ├── constants.py
│   │   ├── exceptions.py
│   │   └── models.py
│   ├── cli.py              # Command-line interface
│   └── main.py             # Entry point
├── tests/                   # Test suites
├── docs/                    # Documentation (this directory)
├── config.yaml             # Configuration file
├── requirements.txt        # Python dependencies
└── README.md              # Project overview
```

## Core Components

### Agents (6 Total)
1. **Amazon Agent** - Scrapes product data from Amazon
2. **Google Agent** - Searches for brand websites via Google
3. **Website Agent** - Extracts data from brand websites
4. **Matching Agent** - Correlates products across sources
5. **Cache Agent** - Manages caching layer
6. **Sheet Agent** - Handles Excel file I/O

### Services
- **Browser Service** - Manages Playwright browser instances
- **Cache Service** - Distributed caching with SQLite backend
- **Checkpoint Service** - Batch execution recovery
- **Error Recovery** - Graceful error handling and retries
- **Logger Service** - Structured logging
- **Progress Service** - Execution progress tracking

### Key Features
- ✅ Multi-agent orchestration with error recovery
- ✅ Checkpoint-based batch processing resumption
- ✅ Progress tracking and real-time status
- ✅ Caching layer for performance
- ✅ Excel integration for input/output
- ✅ CLI interface for easy operation
- ✅ Comprehensive logging and reporting
- ✅ Production-ready deployment

## Getting Started

### Setup
```bash
pip install -r requirements.txt
python src/main.py --help
```

### Configuration
Update `config.yaml` with your settings. Reference configuration options in `src/core/config.py`.

### Running Batch Jobs
```bash
python src/cli.py process input_file.xlsx output_file.xlsx
```

### View Progress
Progress tracking and checkpoints are stored in the `checkpoints/` directory. The system automatically resumes from the last checkpoint on failure.

## Development Notes

- All agents follow the standardized Agent interface in `src/core/models.py`
- Configuration is centralized in `config.yaml` and `src/core/config.py`
- Logging uses Python's structured logging with the configured logger service
- Database operations use SQLite via the cache service
- Browser automation uses Playwright for cross-platform compatibility

## Status

**Last Updated:** 2026-07-03

The system is production-ready as of Phase 5 completion. All components have been integrated, tested, and verified. See [Final Deployment Checklist](docs/FINAL_DEPLOYMENT_CHECKLIST.md) for deployment verification.

## References

- Phase-by-phase documentation in `docs/` directory
- Technical architecture in [Final Implementation Report](docs/FINAL_IMPLEMENTATION_REPORT.md)
- Runtime performance metrics in [Runtime Audit Report](docs/RUNTIME_AUDIT_REPORT.md)
- Test data in [Test Sample Data](docs/TEST_SAMPLE_DATA.json)
