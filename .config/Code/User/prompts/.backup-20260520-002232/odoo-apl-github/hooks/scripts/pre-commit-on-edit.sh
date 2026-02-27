#!/usr/bin/env bash
# Runs pre-commit on files edited by the agent in the current session.
# Invoked by PostToolUse hook after any file edit/create.
# Exits 0 (non-blocking) so the agent session is never hard-blocked,
# but injects a warning message if violations are found.

set -euo pipefail

INPUT=$(cat)

# Extract file path from the tool input JSON
FILE=$(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
# tool_input may be nested under 'tool_input' or at root
ti = data.get('tool_input') or data
print(ti.get('filePath') or ti.get('path') or '')
" 2>/dev/null || echo "")

# Only run on Python and XML files
if [[ -z "$FILE" ]] || [[ "$FILE" != *.py && "$FILE" != *.xml ]]; then
    exit 0
fi

# Only run if file exists in the repo
if [[ ! -f "$FILE" ]]; then
    exit 0
fi

OUTPUT=$(pre-commit run --files "$FILE" 2>&1) || true
EXIT_CODE=$?

if [[ $EXIT_CODE -ne 0 ]]; then
    # Return a non-blocking warning message to the agent
    python3 -c "
import json, sys
print(json.dumps({
    'systemMessage': (
        'pre-commit found violations in ' + sys.argv[1] + ':\n\n'
        + sys.argv[2]
        + '\n\nFix them before committing. Run: odoo-precommit agent or pre-commit run -a'
    )
}))
" "$FILE" "$OUTPUT"
fi

exit 0
