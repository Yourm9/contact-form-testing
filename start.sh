#!/bin/bash
playwright install-deps
python3 -m playwright install
gunicorn app:app --bind 0.0.0.0:$PORT
