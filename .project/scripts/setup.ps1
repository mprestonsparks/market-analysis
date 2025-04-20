# Project management setup script
# Verifies prerequisites and initializes project structure

# Function to check if a command exists
function Test-Command {
    param($Command)
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = 'stop'
    try {
        if (Get-Command $Command) { return $true }
    } catch {
        return $false
    } finally {
        $ErrorActionPreference = $oldPreference
    }
}

Write-Host "Checking prerequisites..."

# Check Git
if (-not (Test-Command "git")) {
    Write-Error "Git is not installed. Please install Git and try again."
    exit 1
}

# Check GitHub CLI
if (-not (Test-Command "gh")) {
    Write-Error "GitHub CLI is not installed. Please install gh and try again."
    exit 1
}

# Check GitHub authentication
$ghAuth = gh auth status
if ($LASTEXITCODE -ne 0) {
    Write-Error "Not authenticated with GitHub. Please run 'gh auth login' first."
    exit 1
}

# Install NuGet provider if needed
if (-not (Get-PackageProvider -ListAvailable -Name NuGet)) {
    Write-Host "Installing NuGet provider..."
    Install-PackageProvider -Name NuGet -Force -Scope CurrentUser
}

# Check and install PowerShell-yaml module
if (-not (Get-Module -ListAvailable -Name "powershell-yaml")) {
    Write-Host "Installing PowerShell-yaml module..."
    Install-Module -Name powershell-yaml -Force -Scope CurrentUser -AllowClobber
    Import-Module powershell-yaml
}

Write-Host "All prerequisites met!"

# Create necessary directories if they don't exist
$directories = @(
    ".project/docs",
    ".project/scripts",
    ".project/status"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "Created directory: $dir"
    }
}

Write-Host "Project management structure initialized successfully!"
Write-Host "Next steps:"
Write-Host "1. Run github_setup.ps1 to configure GitHub integration"
Write-Host "2. Review documentation in .project/docs/"
