#!/bin/bash
# Simple run script for Linux/macOS
python -m venv venv
. venv/bin/activate
pip install -r requirements.txt
python -m formato.app
