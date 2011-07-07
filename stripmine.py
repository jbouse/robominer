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

try:
	cParser = ConfigParser.SafeConfigParser()
	cParser.read('stripmine.cfg')
except ConfigParser.ParsingError, err:
	print 'Could not parse:', err
	sys.exit(1)

oParser = OptionParser(version=USER_AGENT)

