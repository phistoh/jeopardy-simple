#!/bin/fish

cd "$(dirname "$0")"
exec .venv/bin/python main.py $argv
