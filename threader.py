"""
HELIUM
(c) 2016 Evan Chen
See LICENSE.txt for details.

threader.py

This is a simple wrapper for running processes async.
"""

import threading


def run_async(func):
	t = threading.Thread(target = func)
	t.daemon = True
	t.start()
