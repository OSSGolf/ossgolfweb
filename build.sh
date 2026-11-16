#!/bin/sh
# Rebuild the site. RSS Lobster regenerates every page plus the preview image and favicons
# with its defaults, so two scripts run afterwards: postbuild.py applies the shared header
# (GitHub link, tagline on post pages) and logo.py puts the oss/golf images back.
set -e
cd "$(dirname "$0")"
rsslobster regenerate .
python3 graphics/postbuild.py
python3 graphics/logo.py
