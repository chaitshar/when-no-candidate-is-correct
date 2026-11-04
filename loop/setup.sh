#!/bin/bash
# Cloud VM only. Failures are logged, the brief handles a missing tool.
[ "$CLAUDE_CODE_REMOTE" = "true" ] || exit 0
L="${CLAUDE_PROJECT_DIR:-.}/loop/setup.log"
python3 -m pip install -q numpy scipy pandas matplotlib statsmodels pyarrow sympy antlr4-python3-runtime==4.11.1 >>"$L" 2>&1
apt-get update -qq >>"$L" 2>&1
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended texlive-bibtex-extra latexmk >>"$L" 2>&1
echo "setup finished rc=$?" >>"$L"
