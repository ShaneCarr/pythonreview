#!/usr/bin/env python3
"""
Quick test runner for input.json file
Just run this script whenever you update your JSON data!
"""

from logVisualizer import run_input_test

def test_input_json():
    """Pytest-compatible test function"""
    run_input_test()

if __name__ == "__main__":
    # When run directly (not via pytest)
    run_input_test()