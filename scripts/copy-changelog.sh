#!/usr/bin/env bash

set -euo pipefail

printf -- '---\n%s\n---\n%s\n' 'icon: lucide/scroll-text' "$(cat CHANGELOG.md)" > docs/changelog.md
