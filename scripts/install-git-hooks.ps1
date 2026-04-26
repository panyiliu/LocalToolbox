$hookPath = ".git/hooks/pre-commit"
$hookContent = @"
#!/usr/bin/env sh
python scripts/precommit_guard.py
"@

Set-Content -Path $hookPath -Value $hookContent -NoNewline
Write-Host "pre-commit hook installed at $hookPath"
