# AI Project Management System Implementation & Usage Guide

## Overview

This guide explains how to implement and use the AI-driven project management system across multiple repositories in your multi-repo project. It covers how to set up and maintain synchronization between GitHub Issues, GitHub Project boards, and the local YAML file that the AI assistant uses to understand task dependencies and order.

**Key Goals:**

- Keep local `.project/status/DEVELOPMENT_STATUS.yaml` synchronized with GitHub Issues and a shared GitHub Project board.
- Use a Directed Acyclic Graph (DAG) to model task dependencies so the AI assistant can identify the next available tasks automatically.
- Provide scripts and workflows to handle setup, synchronization, and status updates seamlessly.

## System Components

### Local Files & Directories

- **`.project/status/DEVELOPMENT_STATUS.yaml`**  
  Central record of tasks. Stores information like task IDs, status, dependencies, and associated GitHub Issues. This file is updated both manually and automatically, ensuring a local source of truth that mirrors GitHub.

- **`.project/scripts/`**  
  Contains scripts for setup, GitHub integration, and status updates:
  - `setup.ps1`: Checks prerequisites (Git, GitHub CLI, modules) and initializes project directories.
  - `github_setup.ps1`: Configures GitHub integration (creates labels, links issues, sets up your project board).
  - `update_status.ps1`: Updates a single task’s status locally and on GitHub (e.g., marking a task as `in-progress` or `completed`).

- **`.project/docs/`**  
  Documentation for customization, AI integration, and workflow guidelines. Feel free to simplify or rewrite these to match your current repo context.

### GitHub Workflows

- **`.github/workflows/project-v2-trigger.yml`**  
  Runs when Issues, PRs, or Project board items change. It checks out the code and runs sync scripts to ensure local files reflect the GitHub state.

- **`.github/workflows/sync-local-to-project.yml`**  
  Triggered when `.project/status/DEVELOPMENT_STATUS.yaml` changes are pushed. Ensures that local updates (e.g., completing a task) are pushed back to GitHub, updating Issues and Project statuses.

- **`.github/workflows/sync-project-to-local.yml`**  
  Triggered by project board item events, syncing changes from GitHub back into `DEVELOPMENT_STATUS.yaml` in the repository. Updates are committed and pushed to maintain local parity.


### Scripts and Dependencies

- **`.github/scripts/sync/dag.js`**  
  The DAG logic script. Reads `DEVELOPMENT_STATUS.yaml`, builds a graph of tasks, checks for cycles, and helps determine task order. Central to the AI’s ability to pick the next task.

- **`.github/scripts/sync/index.js`**  
  Core synchronization logic. Interacts with GitHub via the `@octokit/rest` library, processes events, and updates `DEVELOPMENT_STATUS.yaml`.

- **`package.json` / `package-lock.json`**  
  Node.js dependencies (Octokit, testing frameworks). Required for the sync scripts and DAG logic to run.

## Setting Up a New Repository

1. **Copy the Files:**  
   Copy over the `.project/`, `.github/workflows/`, `.github/scripts/`, and any necessary Node.js config files into your new repository. Also include `DEVELOPMENT_STATUS.yaml`, even if you intend to start from scratch.

2. **Clean the `DEVELOPMENT_STATUS.yaml` (If Starting Fresh):**  
   If you want an empty or minimal start (no predefined tasks), simply empty the `DEVELOPMENT_STATUS.yaml` file. With no tasks defined, the system will rely on you creating GitHub Issues or Project board items to populate it later.

3. **Run `setup.ps1`:**  
   Open PowerShell from the repository root and run:  
   ```powershell
   .\project\scripts\setup.ps1
   ```  
   This ensures prerequisites (Git, gh CLI, modules) are installed and directories are in place.

4. **Run `github_setup.ps1`:**  
   After setup is complete, run:
   ```powershell
   .\project\scripts\github_setup.ps1
   ```
   This script:
   - Ensures the correct GitHub Project board is available.
   - Creates status labels (e.g., `ready`, `in-progress`, `blocked`) in your repo.
   - If tasks are defined in `DEVELOPMENT_STATUS.yaml`, it creates Issues accordingly. If the file is empty, no Issues are created at this time.

5. **Trigger the Initial Sync (If Starting Fresh):**  
   If you have an empty `DEVELOPMENT_STATUS.yaml`, create a new Issue in the GitHub UI for this repository and assign it to the project board. The `project-v2-trigger.yml` or `sync-project-to-local.yml` workflow will detect the change and update the local YAML. After a few moments, check `DEVELOPMENT_STATUS.yaml` again to verify it’s been updated with the new Issue.

6. **Round-Trip Sync Verification:**
   - Use `update_status.ps1` to change a task’s status locally, for example:
     ```powershell
     .\project\scripts\update_status.ps1 -TaskId 1 -NewStatus in-progress -Details "Started coding"
     ```
   - This should update both the local YAML and the corresponding GitHub Issue. Check GitHub to ensure the labels and project column reflect the change.

## Customization & Portability

- **User & Project Board:**  
  Since all four of your repos share the same user and project board, you don’t need to edit `github_setup.ps1`. If in the future you use a different project or user, update the script accordingly.

- **Repository Names:**  
  If the repository references in `github_setup.ps1` (like `trade-manager`, `market-analysis`, etc.) match your environment, no changes are needed. If you rename repos or add new ones, update `github_setup.ps1` and any docs accordingly.

- **Documentation:**  
  The `.project/docs/*` files provide background on AI integration, customization, and workflows. Feel free to consolidate them into a single guide, remove outdated references, or rewrite them to fit your team’s needs.

- **Removing Unused Tools & Scripts:**  
  If you don’t need `test-project-v2-events.yml` or `validate-workflows.sh`, delete them to keep your repo clean. If you don’t rely on certain docs, remove or archive them.

## Best Practices

- **Regularly Update `DEVELOPMENT_STATUS.yaml`:**  
  Keep tasks accurate. Update statuses after completing tasks or add new tasks when necessary.

- **Leverage the DAG Logic:**  
  The `dag.js` script ensures you never lose track of dependencies. Use it and the AI’s reasoning capabilities to identify the next logical task quickly.

- **Keep Docs Relevant:**  
  Maintain up-to-date documentation so new contributors or future you can understand the system easily.

- **Review Changes:**  
  Although the AI assistant automates many steps, always review generated code, documentation changes, and task status updates before merging to maintain quality and consistency.

## Summary

To implement the AI project management system in a new repository:

1. Copy the system files (`.project`, `.github/workflows`, `.github/scripts`, etc.).
2. Optionally clear `DEVELOPMENT_STATUS.yaml` for a fresh start.
3. Run `setup.ps1` and then `github_setup.ps1` to configure the environment and GitHub integration.
4. Create or modify a GitHub Issue to trigger syncing and populate the YAML file.
5. Use `update_status.ps1` and GitHub Issues interchangeably to manage task statuses.
6. Optionally remove any testing workflows or validation scripts not needed.
7. Update documentation to reflect the new repository and its context.

By following this guide, you’ll have a streamlined, AI-assisted project management system across all your repositories, ensuring consistent workflow and efficient task management.