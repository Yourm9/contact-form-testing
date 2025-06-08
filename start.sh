#!/bin/bash

# Install system dependencies required for Chromium
playwright install-deps

# Install the browser binaries
python3 -m playwright install

# Run the bot
python3 bot.py

export FLASK_APP=app.py
export FLASK_ENV=production
flask run --host=0.0.0.0 --port=5000