<#
.SYNOPSIS
    双参考两段式出图：氛围稿（qwen 文生图）→ 融合（wan2.7 双参考）。

.DESCRIPTION
    第一段用 qwen-image-3.0-pro 纯文生图产材质/氛围稿。
    第二段用 wan2.7-image-pro 同时吃「结构底图」和「氛围稿」，把质感叠回正确结构上。
    前置依赖已在本机配好的 baoyu-image-gen（DashScope key）。

.PARAMETER Base
    几何控制图（白模/线稿截图）。必填。

.PARAMETER MoodPrompt
    氛围稿提示词。可以直接传字符串，也可以传 .md/.txt 文件路径。

.PARAMETER FusionPrompt
    融合提示词。省略时使用内置模板（ref1 结构 / ref2 材质 的三句分工写法）。

.PARAMETER Out
    终稿路径。

.PARAMETER Mood
    氛围稿路径。省略时自动放在终稿同目录的 <Out 名>-mood.png。

.PARAMETER MoodOnly
    只出氛围稿，不跑融合。

.PARAMETER SkipMood
    复用已存在的氛围稿，跳过第一段。

.PARAMETER Ar
    画幅比例，默认 16:9。

.PARAMETER Style
    风格名，仅写入日志便于回溯。

.EXAMPLE
    .\gen.ps1 -Base .\_input\interior-white.png -MoodPrompt .\mood.txt -Out .\final.png -Style "暖调中古"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Base,
    [Parameter(Mandatory = $true)][string]$MoodPrompt,
    [string]$FusionPrompt,
    [Parameter(Mandatory = $true)][string]$Out,
    [string]$Mood,
    [switch]$MoodOnly,
    [switch]$SkipMood,
    [string]$Ar = "16:9",
    [string]$Style = ""
)

$ErrorActionPreference = "Stop"

$Main = "C:\Users\HP\.config\opencode\skills\baoyu-image-gen\scripts\main.ts"
if (-not (Test-Path -LiteralPath $Main)) { throw "找不到 baoyu-image-gen 主脚本：$Main" }
if (-not (Test-Path -LiteralPath $Base)) { throw "找不到结构底图：$Base" }

function Resolve-Text([string]$value) {
    if (Test-Path -LiteralPath $value) { return (Get-Content -LiteralPath $value -Raw -Encoding UTF8).Trim() }
    return $value
}

$moodText = Resolve-Text $MoodPrompt
$outFull  = [System.IO.Path]::GetFullPath($Out)
$outDir   = [System.IO.Path]::GetDirectoryName($outFull)
if (-not (Test-Path -LiteralPath $outDir)) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }

if (-not $Mood) {
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($outFull)
    $Mood = Join-Path $outDir "$baseName-mood.png"
}
$moodFull = [System.IO.Path]::GetFullPath($Mood)

Write-Host "== 结构底图: $Base"
Write-Host "== 风格    : $Style"
Write-Host "== 氛围稿  : $moodFull"

# ---------- 第一段：氛围稿（纯文生图，不吃 --ref） ----------
if (-not $SkipMood) {
    Write-Host "`n[1/2] qwen-image-3.0-pro 生成氛围稿 ..."
    bun $Main --provider dashscope --model qwen-image-3.0-pro `
        --prompt $moodText --image $moodFull --ar $Ar --quality 2k
    if ($LASTEXITCODE -ne 0) { throw "氛围稿生成失败（退出码 $LASTEXITCODE）" }
    if (-not (Test-Path -LiteralPath $moodFull)) { throw "氛围稿未生成：$moodFull" }
} else {
    if (-not (Test-Path -LiteralPath $moodFull)) { throw "-SkipMood 需要已存在的氛围稿：$moodFull" }
    Write-Host "[1/2] 跳过氛围稿，复用 $moodFull"
}

if ($MoodOnly) {
    Write-Host "`n-MoodOnly：只产氛围稿，结束。"
    return
}

# ---------- 第二段：双参考融合 ----------
if (-not $FusionPrompt) {
    $FusionPrompt = @"
参考图 1 是空间结构的唯一依据：墙体、窗洞、开口位置、开间比例、层高、家具占位轮廓必须与参考图 1 完全一致，不得增删墙体或改变格局。
参考图 2 是材质与氛围的唯一依据：严格参照其家具材质、布艺与皮革质感、木纹、灯光色温与光晕、细节密度与生活感，以及窗外实景内容；参考图 2 的构图与结构一律忽略。

避免：任何文字、水印、logo、边框；不得新增参考图 1 中不存在的构件。
要求：写实建筑表现图，自然光，高细节，客户交付级画质。
"@
} else {
    $FusionPrompt = Resolve-Text $FusionPrompt
}
if ($Style) { $FusionPrompt = "风格：$Style。`n$FusionPrompt" }

Write-Host "`n[2/2] wan2.7-image-pro 双参考融合 ..."
bun $Main --provider dashscope --model wan2.7-image-pro `
    --prompt $FusionPrompt `
    --ref $Base `
    --ref $moodFull `
    --image $outFull --ar $Ar --quality 2k
if ($LASTEXITCODE -ne 0) { throw "融合失败（退出码 $LASTEXITCODE）" }

Write-Host "`n完成：$outFull"
Write-Host "氛围稿：$moodFull"
Write-Host "下一步：看画面做三查，再判定 可交付 / 仅意向 / 重做（见 references\acceptance.md）"
