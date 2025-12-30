#!/usr/bin/env bash
#
# read_article.sh - Quick article reader from clipboard
#
# Usage:
#   1. Copy article URL to clipboard
#   2. Run: ./read_article.sh
#   3. Article opens in bat pager with Markdown syntax highlighting
#
# Requirements:
#   - bat (https://github.com/sharkdp/bat)
#   - macOS: pbpaste (built-in)
#   - Linux: xsel or xclip
#
# Installation:
#   macOS: brew install bat
#   Linux: apt install bat xsel  # or xclip

set -euo pipefail

# Check if bat is installed
if ! command -v bat &> /dev/null; then
    echo "Error: bat is not installed. Install with:"
    echo "  macOS: brew install bat"
    echo "  Linux: apt install bat"
    exit 1
fi

# Get URL from clipboard based on OS
if [[ $(uname) == "Darwin" ]]; then
    # macOS: use pbpaste
    url=$(pbpaste)
elif [[ $(uname) == "Linux" ]]; then
    # Linux: try xsel first, fallback to xclip
    if command -v xsel &> /dev/null; then
        url=$(xsel -ob)  # clipboard selection (-op for primary/middle-click)
    elif command -v xclip &> /dev/null; then
        url=$(xclip -selection clipboard -o)
    else
        echo "Error: Neither xsel nor xclip found. Install one:"
        echo "  apt install xsel"
        echo "  apt install xclip"
        exit 1
    fi
else
    echo "Error: Unsupported OS: $(uname)"
    exit 1
fi

# Validate URL
if [[ ! $url =~ ^https?:// ]]; then
    echo "Error: Clipboard does not contain a valid URL"
    echo "Clipboard content: $url"
    exit 1
fi

echo "Reading article from: $url"

# Run kiosque with verbose logging and pipe to bat
uv run kiosque -v "$url" - | bat - -l md