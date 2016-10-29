"""
HELIUM
(c) 2016 Evan Chen
See LICENSE.txt for details.

threader.py

This is a simple wrapper for running processes async.
"""

import logging
import threading

def run_async(func, name=""):
	def target_func():
		try:
			func()
		else:
			logging.info("%s completed OK" %name)
	t = threading.Thread(target = func)
	t.daemon = True
	t.start()
