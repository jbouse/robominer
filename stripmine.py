#!/usr/bin/env python

from multiprocessing import Process
from optparse import OptionParser
import ConfigParser 

import os, sys
import logging as log
import pyopencl as cl
from struct import *
from time import sleep, time, strftime
from datetime import datetime

from BitcoinMiner import *

VERSION = '2011.07.06'

USER_AGENT = 'stripmine/' + VERSION

def Miner(device, options):
	log.debug('Worker starting on device ' + device)
	log.debug('Setting DISPLAY variable for device ' + device)
	os.environ['DISPLAY'] = ':0.' + device
	log.debug('Confirming environment: ' + os.environ['DISPLAY'])
	log.debug('Checking that device is found now that DISPLAY is set')

	devices = cl.get_platforms()[0].platform.get_devices()

	class StripMiner(BitcoinMiner):
		def say(self, format, args=()):
			log.info('Device[%s]: ' % device + format % args)

		def sayLine(self, format, args=()):
			if(format == 'verification failed, check hardware!'):
				message = 'Device[' + device + '] failed verification, check hardware!'
				log.warn(message)
			else:
				self.say(format, args)

		miner = StripMiner(device,
					options.host,
					options.user,
					options.password,
					options.port,
					options.frames,
					options.rate,
					options.askrate,
					options.worksize,
					options.vectors,
					options.verbose,
					options.proxy)

		miner.mine()

def main():
	oParser = OptionParser(version=USER_AGENT,
			description='Bitcoin strip mining daemon')
	oParser.add_option('-c', '--config', action='store',
		dest='configfile', default='stripmine.cfg')
	oParser.add_option('-p', '--pool', action='store',
		dest='pool', default=None)
	(options, args) = oParser.parse_args()

	try:
		cParser = ConfigParser.SafeConfigParser()
		cParser.read([options.configfile, os.path.expanduser('~/.stripmine.cfg')])
	except ConfigParser.ParsingError, err:
		print 'Could not parse:', err
		sys.exit(1)

	# Define default settings
	for opt, val in cParser.defaults().iteritems():
		setattr(options, opt, val)

	# Define pool specific values if specified and available
	if cParser.has_section('pool_%s' % options.pool):
		for opt in cParser.options('pool_%s' % options.pool):
			setattr(options, opt, cParser.get('pool_%s' % options.pool, opt))

if __name__ == '__main__':
	main()
