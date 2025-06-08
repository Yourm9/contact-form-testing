#!/bin/bash

# Install system dependencies required for Chromium
playwright install-deps

# Install the browser binaries
python3 -m playwright install

# Run the bot
python3 bot.py
