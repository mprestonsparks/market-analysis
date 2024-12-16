# Project Management Setup

## Overview
This document describes the project management structure and tools used in the Trade Manager repository.

## Directory Structure
```
.project/
├── docs/           # Project management documentation
├── scripts/        # Automation scripts
└── status/         # Project status tracking
```

## Components

### 1. Status Tracking
- `DEVELOPMENT_STATUS.yaml`: Central source of truth for project status
- Tracks tasks, dependencies, and progress
- Integrates with GitHub issues

### 2. Automation Scripts
- `setup.ps1`: Initial project setup
- `github_setup.ps1`: GitHub integration setup
- `update_status.ps1`: Task status management

### 3. Documentation
- `setup.md`: Setup instructions (this file)
- `workflow.md`: Development workflow guide
- `customization.md`: Customization guidelines
- `ai_integration.md`: AI assistant integration

## Getting Started
1. Run `.project/scripts/setup.ps1` to verify prerequisites
2. Run `.project/scripts/github_setup.ps1` to configure GitHub integration
3. Use `.project/scripts/update_status.ps1` to manage task status

## Usage Examples

### Update Task Status
```powershell
.project/scripts/update_status.ps1 -TaskId 1 -NewStatus "in-progress" -Details "Starting implementation"
```

### View Current Status
```powershell
Get-Content .project/status/DEVELOPMENT_STATUS.yaml
```
