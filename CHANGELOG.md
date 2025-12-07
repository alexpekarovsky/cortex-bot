# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions CI/CD workflows
- Contributing guidelines (CONTRIBUTING.md)
- Code of Conduct (CODE_OF_CONDUCT.md)
- Security policy (SECURITY.md)
- Issue and PR templates

### Changed
- Updated README with comprehensive documentation
- Improved .gitignore for production use

## [1.0.0] - 2024-12-03

### Added

#### Core Platform
- FastMCP-based MCP server implementation
- Support for stdio and streamable-http transports
- Docker container support with non-root user
- Modular tool architecture (builtin, custom, remote components)
- OpenAPI-based tool generation from YAML specifications

#### Case Management (5 tools)
- `get_cases` - List and filter security cases/incidents
- `get_incident_extra_data` - Get comprehensive case forensic details
- `update_incident` - Update case status, assignment, and severity
- `update_case_ai_summary` - Generate AI-powered investigation summaries
- `update_case_timeline` - Generate visual HTML timeline for cases

#### Alert Management (4 tools)
- `get_issues` - List and filter security alerts
- `get_alert_multi_events` - Get detailed alert event data
- `get_contributing_events` - Get correlation alert contributing events
- `update_issue` - Update alert severity and status

#### Threat Hunting (1 tool)
- `run_xql_query` - Execute XQL queries for threat hunting and analysis

#### Identity Threat Detection (2 tools)
- `list_risky_users` - List high-risk user accounts from ITDR
- `list_risky_hosts` - List high-risk endpoints from ITDR

#### Endpoints & Assets (3 tools)
- `get_endpoints` - Get endpoint inventory and details
- `get_assets` - Get asset inventory
- `get_assessment_profile_results` - Get security assessment results

#### Response Actions (6 tools)
- `isolate_endpoint` - Isolate endpoint from network
- `unisolate_endpoint` - Restore endpoint network connectivity
- `scan_endpoint` - Initiate on-demand malware scan
- `abort_scan` - Cancel running endpoint scan
- `terminate_process` - Kill process by name on endpoint
- `terminate_causality` - Terminate entire process tree

#### File Operations (5 tools)
- `quarantine_files` - Quarantine suspicious files
- `restore_file` - Restore quarantined files
- `get_quarantine_status` - Check file quarantine status
- `retrieve_files` - Retrieve files from endpoint for analysis
- `get_file_retrieval_details` - Get download URLs for retrieved files

#### Script Execution (6 tools)
- `run_script` - Execute pre-registered scripts on endpoints
- `get_scripts` - List available scripts in library
- `get_script_metadata` - Get script parameters and details
- `get_script_execution_status` - Monitor script execution progress
- `get_script_execution_results` - Get script output and results
- `run_snippet_code_script` - Execute ad-hoc code snippets

#### IOC Management (2 tools)
- `insert_indicators_json` - Add IOCs via JSON format
- `insert_indicators_csv` - Add IOCs via CSV format

#### War Room Collaboration (2 tools)
- `add_war_room_entry` - Add notes/commands to War Room
- `get_war_room_entries` - Get War Room history and entries

#### XSOAR & Enrichment (5 tools)
- `run_xsoar_automation` - Execute any XSOAR automation command
- `enrich_ip_address` - IP reputation lookup via threat intel
- `enrich_domain` - Domain reputation lookup via threat intel
- `enrich_file_hash` - File hash reputation lookup via threat intel
- `enrich_url` - URL reputation lookup via threat intel

#### Monitoring (1 tool)
- `get_action_status` - Check response action execution status

### Documentation
- Installation guide for Claude Code, Claude Desktop, and Gemini CLI
- Custom component development guide
- API reference documentation

### Infrastructure
- GitLab CI/CD pipeline with lint, test, and deploy stages
- Poetry dependency management
- Pytest test framework with async support
- Black and Ruff code formatting/linting

## [0.1.0] - 2024-11-01

### Added
- Initial project structure
- Basic case and issue retrieval tools
- Docker container support
- Environment-based configuration

---

[Unreleased]: https://github.com/PaloAltoNetworks/cortex-mcp/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/PaloAltoNetworks/cortex-mcp/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/PaloAltoNetworks/cortex-mcp/releases/tag/v0.1.0
