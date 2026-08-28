# Skill backup sync script
# Sync 5 skill directories to all-skills repo for GitHub backup

$ErrorActionPreference = "Continue"
$repoRoot = "E:\code\all-skills"

$syncMap = [ordered]@{
  "C:\Users\HP\AppData\Roaming\com.ai-toolbox\skills" = "ai-toolbox-skills"
  "C:\Users\HP\.config\opencode\skills"               = "opencode-skills"
  "C:\Users\HP\.agents\skills"                        = "agents-skills"
  "C:\Users\HP\.claude\skills"                        = "claude-skills"
  "E:\code\my-ai-workspace\.opencode\skills"          = "project-skills"
}

$excludeDirs = @(
  "node_modules", "funasr-env", "venv", ".venv", "env", ".env",
  "__pycache__", ".cache", ".tmp", "temp", "dist", "build",
  ".npm", ".yarn", ".vscode", ".idea", ".git"
)

$excludeFiles = @(
  "*.dll", "*.so", "*.dylib", "*.exe", "*.bin", "*.lib", "*.obj",
  "*.zip", "*.tar.gz", "*.rar", "*.7z", "*.whl",
  "*.pt", "*.pth", "*.onnx", "*.pb", "*.h5", "*.model",
  "*.db", "*.sqlite", "*.sqlite3",
  "*.pdf", "*.mp4", "*.mov", "*.avi", "*.mkv",
  "*.pyc", "*.pyo", "*.log",
  "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
  ".DS_Store", "Thumbs.db"
)

function Sync-SkillDir {
  param([string]$Source, [string]$TargetName)

  $target = Join-Path $repoRoot $TargetName

  Write-Host "========================================" -ForegroundColor Cyan
  Write-Host "[$TargetName] Syncing..." -ForegroundColor Yellow
  Write-Host "  Source: $Source"
  Write-Host "  Target: $target"

  if (-not (Test-Path $Source)) {
    Write-Host "  [SKIP] Source not found" -ForegroundColor DarkYellow
    return
  }

  if (-not (Test-Path $target)) {
    New-Item -ItemType Directory -Path $target -Force | Out-Null
  }

  $xdArgs = @("/XD") + $excludeDirs
  $xfArgs = @("/XF") + $excludeFiles
  $robocopyArgs = @($Source, $target, "/E", "/COPY:DAT", "/R:2", "/W:1", "/NDL", "/NFL", "/NJH", "/NJS", "/NC", "/NS", "/NP") + $xdArgs + $xfArgs

  $result = & robocopy @robocopyArgs 2>&1
  $exitCode = $LASTEXITCODE

  if ($exitCode -ge 8) {
    Write-Host "  [ERROR] robocopy exit: $exitCode" -ForegroundColor Red
    Write-Host ($result | Select-Object -Last 5) -ForegroundColor Red
  } elseif ($exitCode -eq 0) {
    Write-Host "  [OK] No changes" -ForegroundColor Green
  } else {
    Write-Host "  [OK] Synced (exit=$exitCode)" -ForegroundColor Green
  }
}

Write-Host ""
Write-Host "===== Skill backup START =====" -ForegroundColor Green
Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

foreach ($entry in $syncMap.GetEnumerator()) {
  Sync-SkillDir -Source $entry.Key -TargetName $entry.Value
}

Write-Host ""
Write-Host "===== Skill backup DONE =====" -ForegroundColor Green
Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""
Write-Host "Next: git add + commit + push in $repoRoot" -ForegroundColor Yellow

exit 0
