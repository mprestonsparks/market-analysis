function Show-SelectedTree {
    param (
        [Parameter(Mandatory=$true)]
        [string]$BasePath,

        [string[]]$TopLevelFiles = @(
            '.dockerignore',
            '.env.example',
            '.gitignore',
            '.pre-commit-config.yaml',
            'Dockerfile',
            'README.md',
            'conftest.py',
            'docker-compose.test.yml',
            'docker-compose.yml',
            'pyproject.toml',
            'pytest.ini',
            'setup.py'
        ),

        [string[]]$TopLevelDirs = @(
            '.github',
            '.project',
            '.vscode',
            'docs',
            'examples',
            'requirements',
            'scripts',
            'src',
            'tests'
        ),

        [string[]]$ExcludedDirs = @("node_modules", "__pycache__", ".git")
    )

    # Print top-level files (if they exist, including hidden/system by using Get-Item -Force)
    foreach ($file in $TopLevelFiles) {
        $fullPath = Join-Path $BasePath $file
        # Try to get the file with -Force
        $item = Get-Item $fullPath -ErrorAction SilentlyContinue -Force
        if ($item -and $item.PSIsContainer -eq $false) {
            Write-Output "+--- $file"
        }
    }


    # Print directories recursively
    $dirCount = $TopLevelDirs.Count
    for ($i = 0; $i -lt $dirCount; $i++) {
        $dir = $TopLevelDirs[$i]
        $dirPath = Join-Path $BasePath $dir
        if (Test-Path $dirPath) {
            $isLast = ($i -eq ($dirCount - 1))
            if ($isLast) {
                Show-Subtree -Path $dirPath -Level 1 -IsLast -ExcludedDirs $ExcludedDirs
            } else {
                Show-Subtree -Path $dirPath -Level 1 -ExcludedDirs $ExcludedDirs
            }
        }
    }
}

function Show-Subtree {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Path,

        [int]$Level,

        [string[]]$ExcludedDirs,

        [switch]$IsLast
    )

    $indent = ('|   ' * ($Level - 1))
    $prefix = if ($IsLast) {"$indent`---"} else {"$indent+---"}

    Write-Output "$prefix $(Split-Path $Path -Leaf)"

    # Gather directories and files, excluding unwanted directories
    $directories = Get-ChildItem $Path -Directory -ErrorAction SilentlyContinue |
        Where-Object { $ExcludedDirs -notcontains $_.Name } |
        Sort-Object Name

    $files = Get-ChildItem $Path -File -ErrorAction SilentlyContinue | Sort-Object Name

    # Ensure both $directories and $files are arrays before concatenation
    $children = @($directories) + @($files)

    if ($children.Count -eq 0) {
        return
    }

    $lastChild = $children[-1]

    foreach ($child in $children) {
        if ($child -is [System.IO.DirectoryInfo]) {
            $childIsLast = ($child.FullName -eq $lastChild.FullName)
            if ($childIsLast) {
                Show-Subtree -Path $child.FullName -Level ($Level + 1) -IsLast -ExcludedDirs $ExcludedDirs
            } else {
                Show-Subtree -Path $child.FullName -Level ($Level + 1) -ExcludedDirs $ExcludedDirs
            }
        } else {
            # Print files
            $fileIndent = ('|   ' * $Level)
            $filePrefix = if ($child.FullName -eq $lastChild.FullName) {"`---"} else {"+---"}
            Write-Output "$fileIndent$filePrefix $($child.Name)"
        }
    }
}

# Usage:
Show-SelectedTree -BasePath (Join-Path $PSScriptRoot "..")
