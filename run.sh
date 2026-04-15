#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
PYTHONPATH=. python3 scripts/run_pipeline.py
