# MODAX Documentation Index

## Overview
Complete documentation index for the MODAX industrial control system.

**System Status:**
- **Version:** 0.4.0 (Extended G-Code Support & Industry 4.0 Roadmap)
- **Test Coverage:** 96-97% (126+ Unit Tests)
- **NEW:** Vollständige CNC-Maschinen-Funktionalität
- **✅ Features Verifiziert:** WebSocket, TimescaleDB, Prometheus, Health Checks
- **Main Entry Points:** 
  - Field Layer: `esp32-field-layer/src/main.cpp`
  - Control Layer: `python-control-layer/main.py` (Port 8000)
  - AI Layer: `python-ai-layer/main.py` (Port 8001)
  - HMI Layer: `csharp-hmi-layer/Program.cs`

## Quick Start
- [README](../README.md) - Project overview and quick start guide
- [SETUP](SETUP.md) - Detailed setup instructions
- [ARCHITECTURE](ARCHITECTURE.md) - System architecture overview

## Main Entry Points & Implementation

### Control Layer (python-control-layer/main.py)
**Port:** 8000 | **Framework:** FastAPI + uvicorn
- Initialisiert ControlLayer mit MQTT-Handler und DataAggregator
- Startet API-Server für HMI-Integration
- Orchestriert Datenfluss zwischen Field, AI und HMI Layer
- Implementiert Signal-Handler für graceful shutdown
- Features: AI-Analysis-Loop, Safety-Command-Validation, Auto-Reconnect

### AI Layer (python-ai-layer/main.py)
**Port:** 8001 | **Framework:** FastAPI + uvicorn
- Startet AI-Service mit REST API für Analyse-Anfragen
- Komponenten: StatisticalAnomalyDetector, SimpleWearPredictor, OptimizationRecommender
- Endpoints: POST /analyze, GET /models/info, POST /reset-wear/{id}
- **NUR BERATEND:** Keine Sicherheitsfunktionen, keine Echtzeit-Kontrolle
- Features: Z-Score-Anomalieerkennung, Stress-Akkumulations-Verschleiß, Baseline-Learning

## Core System Documentation

### Architecture & Design
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture and component overview
- [API.md](API.md) - REST API reference for Control and AI layers
- [CONFIGURATION.md](CONFIGURATION.md) - Configuration options and environment variables
- [NETWORK_ARCHITECTURE.md](NETWORK_ARCHITECTURE.md) - Network design, OT/IT separation, Purdue Model
- **[GLOSSARY.md](GLOSSARY.md)** ⭐ **NEW** - Comprehensive glossary of all technical terms (250+ entries)
- **[FUNCTION_REFERENCE.md](FUNCTION_REFERENCE.md)** ⭐ **NEW** - Detailed function documentation for all modules
- **[HANDBOOK_PREPARATION.md](HANDBOOK_PREPARATION.md)** ⭐ **NEW** - Structure and preparation for complete user handbook
- **[TOFU.md](TOFU.md)** ⭐ **NEW** - Quick Wins: Production-ready features and best practices
  - Health-check endpoints (/health, /ready)
  - API versioning (/api/v1/...)
  - Standardized error responses
  - Rate limiting & CORS configuration
  - Graceful shutdown & environment validation
  - Structured JSON logs & Prometheus metrics
  - Docker health checks
- **[CNC_FEATURES.md](CNC_FEATURES.md)** ⭐ - Comprehensive CNC machine functionality
  - G-code parser (ISO 6983)
  - Motion control and interpolation
  - Tool management and compensation
  - Coordinate systems and transformations
  - Fixed cycles (drilling, milling, tapping)
  - API endpoints for CNC operations
- **[EXTENDED_GCODE_SUPPORT.md](EXTENDED_GCODE_SUPPORT.md)** ⭐ **NEW** - Extended G-code and Interpreter
  - 150+ G/M-codes (NURBS, threading, probing)
  - Manufacturer-specific codes (Siemens, Fanuc, Heidenhain, Okuma, Mazak, Haas)
  - Macro support (G65/G66, O-codes, variables)
  - Control flow (GOTO, GOSUB, RETURN, labels)
  - Interpreter with subroutines and loops
  - F and S code handling
- **[HOBBYIST_CNC_SYSTEMS.md](HOBBYIST_CNC_SYSTEMS.md)** ⭐ **NEW** - Hobbyist & Desktop CNC Systems
  - **Estlcam:** Image/QR-code processing (PNG/JPG/GIF), alternative controls (gamepad, handwheel), angle error compensation, remote API
  - **UCCNC:** Universal CNC controller for various hardware platforms
  - **Haas:** Industrial CNC with specific codes (G47 engraving, G71/G72 roughing, M130 media player)
  - Integration recommendations for MODAX
  - Comparison table and safety guidelines
- **[ADVANCED_CNC_INDUSTRY_4_0.md](ADVANCED_CNC_INDUSTRY_4_0.md)** ⭐ **NEW** - Industry 4.0 Advanced Features
  - Advanced Communication Protocols (EtherCAT, PROFINET, OPC UA, MQTT, MTConnect)
  - Intelligent Process Control (Adaptive Feed, Vibration Monitoring, Energy Management)
  - Advanced Automation (Predictive Maintenance, Lights-Out Production, Automated Job Setup)
  - Future Integration (AI Parameter Optimization, Digital Twin, Peer-to-Peer Learning)
  - Next-Generation HMI (AR Overlays, Cloud-Native Interfaces, Voice/Gesture Control)
  - Implementation Roadmap and ROI Analysis

### Security
- [SECURITY.md](SECURITY.md) - Comprehensive security concept
  - Transport encryption (MQTT over TLS, HTTPS)
  - Authentication & authorization
  - Audit logging
  - Secrets management
  - Network security
  - Compliance (IEC 62443, NIST SP 800-82)
- **[AUTHENTICATION_IMPLEMENTATION_GUIDE.md](AUTHENTICATION_IMPLEMENTATION_GUIDE.md)** ⭐ **NEW** - Step-by-step authentication setup
  - MQTT authentication (username/password, TLS certificates)
  - API authentication (API keys, RBAC)
  - Secrets management (environment variables, Docker secrets, Vault)
  - Configuration examples and troubleshooting
  - Testing and verification procedures
- **[SECURITY_AUDIT_2025-12-09.md](../SECURITY_AUDIT_2025-12-09.md)** ⭐ **NEW** - Security Audit Results
  - ✅ PASSED - Zero vulnerabilities detected
  - Bandit scanner: 384 lines audited
  - 39 security tests (100% pass rate)
  - Production security checklist
  - IEC 62443 & NIST SP 800-82 compliance notes

### Data Management
- [DATA_PERSISTENCE.md](DATA_PERSISTENCE.md) - Time-series database strategy
  - TimescaleDB implementation
  - Data retention policies
  - Continuous aggregates
  - Query optimization
- [BACKUP_RECOVERY.md](BACKUP_RECOVERY.md) - Backup and disaster recovery
  - 3-2-1 backup strategy
  - Automated backups
  - Recovery procedures
  - RTO/RPO targets

### Operations & Deployment
- [CONTAINERIZATION.md](CONTAINERIZATION.md) - Docker and container deployment
  - Dockerfiles for all components
  - docker-compose configurations
  - Production deployment strategies
- [CI_CD.md](CI_CD.md) - Continuous Integration/Deployment
  - GitHub Actions workflows
  - Quality gates
  - Deployment strategies
  - Rollback procedures
- [HIGH_AVAILABILITY.md](HIGH_AVAILABILITY.md) - High availability and failover
  - HA architecture
  - Load balancing
  - Database replication
  - Automatic failover
  - Disaster recovery

### Monitoring & Logging
- [MONITORING.md](MONITORING.md) - Observability stack
  - Prometheus metrics
  - Loki log aggregation
  - Grafana dashboards
  - AlertManager configuration
  - Distributed tracing
- [LOGGING_STANDARDS.md](LOGGING_STANDARDS.md) - Logging best practices
- [ERROR_HANDLING.md](ERROR_HANDLING.md) - Error handling patterns

## Integration & Extensibility

### Protocol Integration
- [OPC_UA_INTEGRATION.md](OPC_UA_INTEGRATION.md) - OPC UA server and client
  - asyncua implementation
  - Information model
  - Security configuration
  - SCADA integration examples

### External Systems (Coming Soon)
- EXTERNAL_INTEGRATIONS.md - ERP/MES/SCADA integration
  - SAP integration
  - MES system connectivity
  - SCADA protocols (WinCC, Ignition)
  - Cloud platforms (Azure IoT, AWS SiteWise)

### Advanced Features (Coming Soon)
- MACHINE_DATA_MODELS.md - Digital twins and machine models
- ADVANCED_AI.md - Advanced AI features
  - Federated learning
  - Explainable AI (XAI)
  - AutoML
  - Advanced anomaly detection

## Testing & Quality Assurance
- [TESTING.md](TESTING.md) - Testing and code quality guide
  - Running tests (98 tests total)
  - Code coverage reporting (96-97%)
  - Linting with flake8 and pylint
  - Test structure and best practices
  - Writing new tests
- TESTING_STRATEGY.md (Coming Soon) - Advanced testing strategy
  - Hardware-in-the-loop (HIL) testing
  - Performance testing
  - Security testing

## Operational Guides (Coming Soon)
- RUNBOOKS.md - Standard operational procedures
  - Common maintenance tasks
  - Troubleshooting guides
  - Emergency procedures
- FIRMWARE_OTA.md - Over-the-air firmware updates
- REPORTING_ANALYTICS.md - OEE and analytics reporting

## Future Planning (Coming Soon)
- TECHNOLOGY_ROADMAP.md - Technology evolution roadmap
- PLUGIN_ARCHITECTURE.md - Plugin system for extensibility
- INDUSTRY_EXTENSIONS.md - Industry-specific extensions
  - CNC and manufacturing
  - Robotics
  - Process industry
- BUSINESS_MODEL.md - Licensing and business model

## Component-Specific Documentation

### Field Layer (ESP32)
- [esp32-field-layer/README.md](../esp32-field-layer/README.md) - ESP32 firmware documentation

### Control Layer (Python)
- [python-control-layer/README.md](../python-control-layer/README.md) - Control layer documentation

### AI Layer (Python)
- [python-ai-layer/README.md](../python-ai-layer/README.md) - AI layer documentation

### HMI Layer (C#)
- [csharp-hmi-layer/README.md](../csharp-hmi-layer/README.md) - HMI documentation

## Project Management

### Planning & Tracking
- [TODO.md](../TODO.md) - Open tasks and roadmap
- [ISSUES.md](../ISSUES.md) - Known issues and bugs
- [DONE.md](../DONE.md) - Completed tasks
- [CHANGELOG.md](../CHANGELOG.md) - Version history

### Recent Updates
- [SESSION_SUMMARY_2025-12-09_PRIORITY_TASKS.md](../SESSION_SUMMARY_2025-12-09_PRIORITY_TASKS.md) - ⭐ **NEW** 20 Priority Tasks Completion (2025-12-09)
- [REVIEW_SUMMARY_2025-12-07.md](REVIEW_SUMMARY_2025-12-07.md) - Comprehensive code and documentation review
- [IMPROVEMENTS_SUMMARY.md](IMPROVEMENTS_SUMMARY.md) - Summary of improvements
- [IMPROVEMENTS_2025-12-07.md](IMPROVEMENTS_2025-12-07.md) - Recent improvements

## Documentation by Role

### For Developers
**Essential Reading:**
1. [ARCHITECTURE](ARCHITECTURE.md) - Understand the system
2. [SETUP](SETUP.md) - Get environment running
3. [API](API.md) - Learn the APIs
4. [CONTRIBUTING](../CONTRIBUTING.md) - Contribution guidelines
5. [FUNCTION_REFERENCE](FUNCTION_REFERENCE.md) - Detailed function documentation
6. [GLOSSARY](GLOSSARY.md) - Technical terms and definitions
7. [TESTING](TESTING.md) - Testing and code quality
8. [CI_CD](CI_CD.md) - Development workflow

**Advanced Topics:**
- [BEST_PRACTICES](BEST_PRACTICES.md) - Development best practices
- [OPC_UA_INTEGRATION](OPC_UA_INTEGRATION.md) - Protocol integration
- [ERROR_HANDLING](ERROR_HANDLING.md) - Error patterns
- [LOGGING_STANDARDS](LOGGING_STANDARDS.md) - Logging practices
- [TROUBLESHOOTING](TROUBLESHOOTING.md) - Problem solving guide

### For DevOps Engineers
**Essential Reading:**
1. [CONTAINERIZATION](CONTAINERIZATION.md) - Container deployment
2. [CI_CD](CI_CD.md) - Build and deployment pipelines
3. [MONITORING](MONITORING.md) - System monitoring
4. [HIGH_AVAILABILITY](HIGH_AVAILABILITY.md) - HA configuration

**Advanced Topics:**
- [NETWORK_ARCHITECTURE](NETWORK_ARCHITECTURE.md) - Network design
- [BACKUP_RECOVERY](BACKUP_RECOVERY.md) - Data protection
- [SECURITY](SECURITY.md) - Security hardening

### For System Administrators
**Essential Reading:**
1. [SETUP](SETUP.md) - Installation guide
2. [CONFIGURATION](CONFIGURATION.md) - System configuration
3. [BACKUP_RECOVERY](BACKUP_RECOVERY.md) - Backup procedures
4. [MONITORING](MONITORING.md) - Health monitoring

**Advanced Topics:**
- [HIGH_AVAILABILITY](HIGH_AVAILABILITY.md) - HA management
- [SECURITY](SECURITY.md) - Security operations
- RUNBOOKS.md (Coming soon) - Operational procedures

### For Security Engineers
**Essential Reading:**
1. [SECURITY](SECURITY.md) - Complete security concept
2. [NETWORK_ARCHITECTURE](NETWORK_ARCHITECTURE.md) - Network security
3. [BACKUP_RECOVERY](BACKUP_RECOVERY.md) - Data protection

**Advanced Topics:**
- [CI_CD](CI_CD.md) - Security scanning in pipeline
- [OPC_UA_INTEGRATION](OPC_UA_INTEGRATION.md) - OPC UA security

### For Integration Engineers
**Essential Reading:**
1. [API](API.md) - REST APIs
2. [OPC_UA_INTEGRATION](OPC_UA_INTEGRATION.md) - OPC UA
3. [ARCHITECTURE](ARCHITECTURE.md) - System overview

**Advanced Topics:**
- EXTERNAL_INTEGRATIONS.md (Coming soon) - ERP/MES/SCADA
- [DATA_PERSISTENCE](DATA_PERSISTENCE.md) - Data access

### For Management
**Essential Reading:**
1. [README](../README.md) - Project overview
2. [ARCHITECTURE](ARCHITECTURE.md) - System capabilities
3. BUSINESS_MODEL.md (Coming soon) - Commercial aspects

**Planning Documents:**
- [TODO](../TODO.md) - Roadmap
- TECHNOLOGY_ROADMAP.md (Coming soon) - Future plans

### Developer Resources
- **[CONTRIBUTING.md](../CONTRIBUTING.md)** ⭐ **NEW** - Contribution guidelines
  - Code of conduct
  - Development workflow
  - Coding standards (Python, C#, C++)
  - Testing requirements
  - Pull request process
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** ⭐ **NEW** - Comprehensive troubleshooting guide
  - Connection issues
  - MQTT problems
  - API issues
  - HMI problems
  - ESP32 field layer issues
  - Performance issues
  - Security issues
  - Docker/deployment issues
- **[BEST_PRACTICES.md](BEST_PRACTICES.md)** ⭐ **NEW** - Development best practices
  - Architecture & design patterns
  - Code quality standards
  - Security best practices
  - Performance optimization
  - Testing strategies
  - Deployment & operations
  - Monitoring & observability
  - Documentation standards

## Documentation Standards

### File Naming
- Use UPPERCASE_WITH_UNDERSCORES.md for documentation files
- Use descriptive names that clearly indicate content
- Place in appropriate directory (`docs/` for general, component folder for specific)

### Content Structure
Each documentation file should include:
1. **Title** - Clear, descriptive heading
2. **Overview** - Brief introduction (1-2 paragraphs)
3. **Content** - Organized with clear headings
4. **Code Examples** - Practical, runnable examples
5. **References** - External links and resources
6. **Metadata** - Last updated date and maintainer

### Markdown Style
- Use proper heading hierarchy (# → ## → ###)
- Include code blocks with language specification
- Use tables for structured data
- Include diagrams where appropriate (ASCII art or images)
- Link to related documentation

## Contributing to Documentation

### How to Update Documentation
1. Edit markdown files directly
2. Follow existing style and structure
3. Test code examples
4. Update this index if adding new documents
5. Submit pull request

### Documentation Priorities
**Priority 1 (Critical):**
- Core system functionality
- Security and safety
- Setup and configuration

**Priority 2 (Important):**
- Integration guides
- Advanced features
- Operational procedures

**Priority 3 (Nice to have):**
- Optimization guides
- Case studies
- Tutorials

## Getting Help

### Support Channels
- **GitHub Issues** - Bug reports and feature requests
- **Documentation** - This comprehensive doc set
- **Component READMEs** - Specific implementation details

### Common Questions
- **Setup problems?** → See [SETUP.md](SETUP.md) or [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **API questions?** → See [API.md](API.md)
- **Security concerns?** → See [SECURITY.md](SECURITY.md)
- **Deployment issues?** → See [CONTAINERIZATION.md](CONTAINERIZATION.md)
- **Integration needs?** → See [OPC_UA_INTEGRATION.md](OPC_UA_INTEGRATION.md)
- **Want to contribute?** → See [CONTRIBUTING.md](../CONTRIBUTING.md)
- **Development guidelines?** → See [BEST_PRACTICES.md](BEST_PRACTICES.md)

## Documentation Status

### Complete ✅
- Core system architecture
- Security concept
- Data persistence strategy
- Containerization guide
- CI/CD pipeline
- High availability
- Network architecture
- Backup & recovery
- Monitoring stack
- OPC UA integration
- Testing and code quality guide
- Comprehensive glossary (250+ terms)
- Function reference for all modules
- Handbook preparation and structure
- Complete code and documentation review (2025-12-07)

### In Progress 🔄
- External system integrations
- Advanced AI features
- Testing strategies
- Operational runbooks
- Technology roadmap

### Planned 📋
- Firmware OTA updates
- Plugin architecture
- Industry-specific extensions
- Business model documentation
- Video tutorials
- Case studies

---
**Last Updated:** 2025-12-09  
**Maintained By:** MODAX Documentation Team

## Quick Reference Card

```
┌──────────────────────────────────────────────────────┐
│ MODAX Quick Documentation Reference                  │
├──────────────────────────────────────────────────────┤
│ Getting Started:          SETUP.md                   │
│ System Overview:          ARCHITECTURE.md            │
│ API Reference:            API.md                     │
│ Function Reference:       FUNCTION_REFERENCE.md      │
│ Glossary:                 GLOSSARY.md                │
│ Testing & Quality:        TESTING.md                 │
│ Configuration:            CONFIGURATION.md           │
│ Security:                 SECURITY.md                │
│ Deployment:               CONTAINERIZATION.md        │
│ Operations:               MONITORING.md              │
│ Integration:              OPC_UA_INTEGRATION.md      │
│ High Availability:        HIGH_AVAILABILITY.md       │
│ Backup/Recovery:          BACKUP_RECOVERY.md         │
│ Network Security:         NETWORK_ARCHITECTURE.md    │
│ CI/CD:                    CI_CD.md                   │
│ Contributing:             CONTRIBUTING.md            │
│ Troubleshooting:          TROUBLESHOOTING.md         │
│ Best Practices:           BEST_PRACTICES.md          │
│ Handbook Prep:            HANDBOOK_PREPARATION.md    │
│ Latest Review:            REVIEW_SUMMARY_2025-12-07  │
└──────────────────────────────────────────────────────┘
```
