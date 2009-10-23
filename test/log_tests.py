import unittest

from VMBuilder.log import console, set_verbosity
import logging

class LogTestSuite(unittest.TestCase):
	def test_verbosity_options(self):
		'Using --debug, --verbose and --quiet flags set proper log levels'
		
		checks = [
			('--debug', logging.DEBUG),
			('--verbose', logging.INFO),
			('--quiet', logging.CRITICAL),
		]
		
		for opt, level in checks:
			set_verbosity(None, opt, None, None)
			self.assertEquals(level, console.level, 'Found wrong logging level after setting flag "%s"' % opt)

