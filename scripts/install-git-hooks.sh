#!/usr/bin/env sh
set -eu

HOOK_FILE=".git/hooks/pre-commit"

cat > "$HOOK_FILE" <<'EOF'
#!/usr/bin/env sh
python scripts/precommit_guard.py
EOF

chmod +x "$HOOK_FILE"
echo "pre-commit hook installed at $HOOK_FILE"
