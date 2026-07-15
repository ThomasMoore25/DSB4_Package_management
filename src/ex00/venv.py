#!/usr/bin/env python3
import os

def main():
    venv_path = os.getenv('VIRTUAL_ENV')
    if venv_path is not None:
        print(f"Your current virtual env is {venv_path}")
    else:
        print("No virtual environment active")

if __name__ == '__main__':
    main()