# Customization Guide

## Overview
This document explains how to customize the project management system for specific needs.

## Configuration Files

### DEVELOPMENT_STATUS.yaml
```yaml
# Add new task
next_available_tasks:
  - id: <task_id>
    name: "Task Name"
    priority: 1-5
    status: ready|blocked|in-progress|review|completed
    blocking: []  # List of task IDs blocked by this task
    prerequisites_met: true|false
```

## Adding New Features

### 1. Custom Task Types
- Add new task types to status definitions
- Update scripts to handle new types
- Document in workflow guide

### 2. Additional Scripts
- Place in `.project/scripts/`
- Follow existing naming conventions
- Update documentation

### 3. Custom Metrics
- Add to status tracking
- Update monitoring
- Document thresholds

## Trade Manager Customizations

### 1. Order Types
- Add new order type definitions
- Implement validation rules
- Update documentation

### 2. Risk Parameters
- Define risk thresholds
- Add monitoring rules
- Configure alerts

### 3. Performance Metrics
- Define KPIs
- Add tracking
- Set benchmarks

## Best Practices

### 1. Documentation
- Keep docs up to date
- Follow markdown format
- Include examples

### 2. Scripts
- Add error handling
- Include help text
- Test thoroughly

### 3. Status Updates
- Use provided scripts
- Keep status accurate
- Update promptly
