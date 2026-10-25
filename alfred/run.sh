#!/bin/bash
# Alfred starts scripts with a minimal PATH; lexi needs a Python 3.8 or newer.
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
exec python3 -I "$(dirname "$0")/lexi_alfred.py" "$@"
