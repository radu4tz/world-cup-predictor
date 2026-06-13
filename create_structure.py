#!/usr/bin/env python3

from pathlib import Path

directories = [
    ".github/workflows",
    "docs",
    "backend/output",
]

files = [
    "backend/output/.gitkeep",
]

for directory in directories:
    Path(directory).mkdir(parents=True, exist_ok=True)

for file in files:
    Path(file).touch(exist_ok=True)

print("Project structure created successfully.")
