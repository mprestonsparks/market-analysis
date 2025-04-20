# Task status update script
# Updates task status and GitHub issues

param(
    [Parameter(Mandatory=$true)]
    [int]$TaskId,
    
    [Parameter(Mandatory=$true)]
    [ValidateSet('ready', 'in-progress', 'blocked', 'review', 'completed')]
    [string]$NewStatus,
    
    [Parameter(Mandatory=$false)]
    [string]$Details = ""
)

Import-Module powershell-yaml

$yamlPath = ".project/status/DEVELOPMENT_STATUS.yaml"

if (-not (Test-Path $yamlPath)) {
    Write-Error "DEVELOPMENT_STATUS.yaml not found"
    exit 1
}

# Load current status
$content = Get-Content $yamlPath -Raw
$status = ConvertFrom-Yaml $content

# Find and update task
$task = $status.next_available_tasks | Where-Object { $_.id -eq $TaskId }
if (-not $task) {
    Write-Error "Task $TaskId not found"
    exit 1
}

$oldStatus = $task.status
$task.status = $NewStatus

# Update GitHub issue if it exists
if ($task.github_issue) {
    # Add comment about status change
    $comment = "Status changed from $oldStatus to $NewStatus"
    if ($Details) {
        $comment += "`n`nDetails: $Details"
    }
    
    gh issue comment $task.github_issue -b $comment
    
    # Update labels
    gh issue edit $task.github_issue --remove-label $oldStatus --add-label $NewStatus
    
    if ($NewStatus -eq 'completed') {
        gh issue close $task.github_issue
    } elseif ($oldStatus -eq 'completed') {
        gh issue reopen $task.github_issue
    }
}

# Update YAML file
$updatedYaml = ConvertTo-Yaml $status
Set-Content -Path $yamlPath -Value $updatedYaml

Write-Host "Updated task $TaskId status from $oldStatus to $NewStatus"
if ($Details) {
    Write-Host "Details: $Details"
}
