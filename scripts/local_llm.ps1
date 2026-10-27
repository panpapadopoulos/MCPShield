param(
    [ValidateSet('serve', 'pull', 'check', 'dashboard', 'evaluate', 'smoke')]
    [string]$Action = 'check',
    [string]$Model = 'qwen2.5:3b',
    [ValidateRange(1, 5)][int]$Repeats = 1,
    [ValidateSet('validation', 'test')][string]$Split = 'validation',
    [ValidateSet('original', 'expanded')][string]$Suite = 'expanded',
    [string]$Output = ''
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
$python = Join-Path $projectRoot '.venv/Scripts/python.exe'
$ollama = Join-Path $projectRoot '.local/ollama/ollama.exe'
if (!(Test-Path -LiteralPath $ollama)) {
    $installed = Get-Command ollama -ErrorAction SilentlyContinue
    if (!$installed) { throw 'Ollama not found. See docs/LOCAL_LLM.md.' }
    $ollama = $installed.Source
}
$env:OLLAMA_MODELS = Join-Path $projectRoot '.local/models'
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:OLLAMA_NO_CLOUD = '1'
$env:MCPSHIELD_LLM_MODEL = $Model
$env:MCPSHIELD_LLM_API_KEY = 'ollama'
$env:MCPSHIELD_LLM_BASE_URL = 'http://127.0.0.1:11434/v1'
$env:MCPSHIELD_LLM_TIMEOUT = '120'
$env:MCPSHIELD_LLM_OUTPUT_FORMAT = 'json_schema'
switch ($Action) {
    'serve' { & $ollama serve }
    'pull' { & $ollama pull $Model }
    'check' { & $python scripts/check_llm.py }
    'dashboard' { & $python -m uvicorn shield.api:app --host 127.0.0.1 --port 8000 }
    'evaluate' {
        $evaluationArgs = @('scripts/evaluate_local.py', '--repeats', $Repeats, '--split', $Split, '--suite', $Suite)
        if ($Output) { $evaluationArgs += @('--output', $Output) }
        & $python @evaluationArgs
    }
    'smoke' {
        $evaluationArgs = @('scripts/evaluate_local.py', '--smoke', '--repeats', $Repeats, '--split', $Split, '--suite', $Suite)
        if ($Output) { $evaluationArgs += @('--output', $Output) }
        & $python @evaluationArgs
    }
}
if ($LASTEXITCODE -ne 0) { throw "Local LLM action failed: $Action" }
