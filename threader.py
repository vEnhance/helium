"""
HELIUM
(c) 2016 Evan Chen
See LICENSE.txt for details.

threader.py

This is a simple wrapper for running processes async.
"""

import logging
import threading
import traceback

logger = logging.getLogger("django")

def run_async(func, name = None):
	logger.info("Starting `%s`..." %name)

	if name is None:
		name = func.__name__
	def target_func():
		try:
			func()
		except Exception as e:
			logger.error("Process `%s` FAILED: %s" %(name, traceback.format_exc()))
			raise
		else:
			logger.info('success', "Process `%s` OK" %name)
	t = threading.Thread(target = target_func)
	t.daemon = True
	t.start()
