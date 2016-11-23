"""
HELIUM
(c) 2016 Evan Chen
See LICENSE.txt for details.

threader.py

This is a simple wrapper for running processes async.
"""

import helium as He

import logging
import threading
import traceback

logger = logging.getLogger("django")

def run_async(func, user, name = None):
	if name is None:
		name = func.__name__
	logger.info("Starting `%s`..." %name)

	record = He.models.ThreadTask.objects.create(name = name, user = user)

	def target_func():
		try:
			out = func()
		except Exception as e:
			s = "Process `%s` FAILED\n%s" %(name, traceback.format_exc())
			record.output = s
			record.save()
			logger.error(s)
			raise
		else:
			s = "Process `%s` OK\n%s" %(name, out)
			record.output = s
			record.save()
			logger.info(s)
	t = threading.Thread(target = target_func)
	t.daemon = True
	t.start()
