# GitHub integration setup script
# Creates labels and configures project board

Import-Module powershell-yaml

Write-Host "Setting up GitHub integration..."

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

    if ($modified) {
        $updatedYaml = ConvertTo-Yaml $status
        Set-Content -Path $yamlPath -Value $updatedYaml
        Write-Host "Updated DEVELOPMENT_STATUS.yaml with issue numbers"
    }
}

Write-Host "GitHub integration setup complete!"
Write-Host "Next steps:"
Write-Host "1. Configure project board columns"
Write-Host "2. Link issues to project board"
Write-Host "3. Start managing tasks"
