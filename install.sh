#!/bin/bash
# Simple Dev Cleaner — one-line install (curl)
# Usage: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/mgdev02/Simple-Dev-Cleaner/main/install.sh)"

set -e

REPO="https://github.com/mgdev02/Simple-Dev-Cleaner.git"

echo "Simple Dev Cleaner — Installing..."
echo ""

# Need Python 3
if ! command -v python3 &>/dev/null; then
  echo "Error: python3 not found. Install Python 3.9+ (e.g. brew install python@3.12)." >&2
  exit 1
fi

# Prefer pipx (isolated env)
if command -v pipx &>/dev/null; then
  pipx install "git+${REPO}"
  echo ""
  echo "Done. Run: sdevclean"
  exit 0
fi

# Ensure pipx is available via pip, then use it
if python3 -m pip install --user pipx 2>/dev/null; then
  python3 -m pipx ensurepath 2>/dev/null || true
  if python3 -m pipx install "git+${REPO}" 2>/dev/null; then
    echo ""
    echo "Done. If sdevclean is not found, run: pipx ensurepath"
    echo "Then run: sdevclean"
    exit 0
  fi
fi

# Fallback: pip install --user
echo "Using pip (install for current user)..."
python3 -m pip install --user "git+${REPO}"
echo ""
echo "Done. Run: sdevclean"
echo "If the command is not found, add to your PATH (e.g. in ~/.zshrc):"
echo '  export PATH="$HOME/Library/Python/$(python3 -c "import sys; print(sys.version_info.minor)")/bin:$PATH"'
