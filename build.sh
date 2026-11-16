#!/bin/sh
# Rebuild the site. RSS Lobster rewrites _site/og-image.png with its default on every
# regenerate, so the logo script runs afterwards to put the oss/golf preview image back.
set -e
cd "$(dirname "$0")"
rsslobster regenerate .
python3 graphics/logo.py
