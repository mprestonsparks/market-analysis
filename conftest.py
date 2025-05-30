"""
Root conftest.py for market analysis project.
This file sets up the Python path for tests.
"""
import os
import sys
import pytest

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
