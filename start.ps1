$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$runtime = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $runtime)) {
    $bundled = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
    if (Test-Path -LiteralPath $bundled) {
        & $bundled -m venv .venv
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        py -3 -m venv .venv
    } else {
        python -m venv .venv
    }
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.10+ is required.' }
}
& $runtime -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
& $runtime manage.py migrate
if ($LASTEXITCODE -ne 0) { throw 'Database migration failed.' }
& $runtime manage.py seed_demo
if ($LASTEXITCODE -ne 0) { throw 'Demo data creation failed.' }
Write-Host 'Site: http://127.0.0.1:8000/  Admin: http://127.0.0.1:8000/admin/'
Write-Host 'Create an administrator in another terminal: .\.venv\Scripts\python.exe manage.py createsuperuser'
& $runtime manage.py runserver 127.0.0.1:8000 --noreload
