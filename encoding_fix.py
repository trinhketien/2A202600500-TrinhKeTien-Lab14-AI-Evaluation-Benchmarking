"""
Encoding fix cho Windows console (cp1258 không hỗ trợ emoji).
Import file này ở đầu mọi script để fix.
"""
import sys
import io

# Force stdout/stderr to UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
