#!/usr/bin/env python3
"""
Simple test script to run the chart generation demo
"""

# Import your module
from logVisualizer import demo_with_your_log, matplotlib
import sys

print("=== Chart Generation Test ===")
print(f"PyCharm detected: {'pydevd' in sys.modules}")
print(f"Backend: {matplotlib.get_backend()}")

# Run the demo
demo_with_your_log()