# GitHub integration setup script
# Creates labels and configures project board

Import-Module powershell-yaml

Write-Host "Setting up GitHub integration..."

# Get project ID
$projectQuery = @"
query {
  user(login: "mprestonsparks") {
    projectV2(number: 1) {
      id
      title
    }
  }
}
"@

$projectInfo = gh api graphql -f query=$projectQuery | ConvertFrom-Json
if (-not $projectInfo.data.user.projectV2) {
    Write-Error "Trading System Development project not found. Please create it first."
    Write-Host @"
Please create a new project on GitHub with the following settings:
1. Title: Trading System Development
2. Template: Board
3. Create the following columns:
   - Ready
   - In Progress
   - Blocked
   - Review
   - Completed
4. Link the following repositories:
   - trade-manager
   - trade-discovery
   - market-analysis
   - trade-dashboard
"@
    exit 1
}

$PROJECT_ID = $projectInfo.data.user.projectV2.id

# Create status labels
$labels = @(
    @{name="ready"; color="0E8A16"; description="Task is ready to be worked on"},
    @{name="in-progress"; color="FFA500"; description="Task is currently being worked on"},
    @{name="blocked"; color="D93F0B"; description="Task is blocked by dependencies"},
    @{name="review"; color="1D76DB"; description="Task is awaiting review"},
    @{name="completed"; color="0E8A16"; description="Task is completed"}
)

foreach ($label in $labels) {
    gh label create $label.name --color $label.color --description $label.description
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Created label: $($label.name)"
    } else {
        Write-Host "Label already exists: $($label.name)"
    }
}

# Create initial issues from DEVELOPMENT_STATUS.yaml
$yamlPath = ".project/status/DEVELOPMENT_STATUS.yaml"
if (Test-Path $yamlPath) {
    $content = Get-Content $yamlPath -Raw
    $status = ConvertFrom-Yaml $content
    $modified = $false

    foreach ($task in $status.next_available_tasks) {
        if (-not $task.github_issue) {
            $title = "Task $($task.id): $($task.name)"
            $body = @"
Priority: $($task.priority)
Status: $($task.status)
Blocking: $($task.blocking -join ', ')
Prerequisites met: $($task.prerequisites_met)
Blocked by: $($task.blocked_by -join ', ')
Dependencies: $($task.dependencies -join ', ')

Description:
$($task.description)
"@
            $issueResult = gh issue create --title $title --body $body
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Created issue: $title"
                $issueNumber = $issueResult -replace '.+/(\d+)$','$1'
                $task.github_issue = [int]$issueNumber
                $modified = $true
            }
        }
    }

    # Update YAML if modified
    if ($modified) {
        $newYaml = ConvertTo-Yaml $status
        Set-Content $yamlPath $newYaml
        Write-Host "Updated $yamlPath with new issue numbers"
    }
}

Write-Host "GitHub integration setup complete!"
Write-Host "Next steps:"
Write-Host "1. Configure project board columns"
Write-Host "2. Link issues to project board"
Write-Host "3. Start managing tasks"
