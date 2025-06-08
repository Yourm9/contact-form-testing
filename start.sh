#!/bin/bash
playwright install-deps
python3 -m playwright install
export FLASK_APP=app.py
export FLASK_ENV=production
flask run --host=0.0.0.0
