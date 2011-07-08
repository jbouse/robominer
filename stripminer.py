#!/usr/bin/env python

from multiprocessing import Process
from optparse import OptionParser
import ConfigParser 
import os, sys, logging
import pyopencl as cl
from struct import *
from time import sleep, time, strftime
from datetime import datetime

from BitcoinMiner import *

try:
	import ADL
except ImportError:
	print "Missing the pyADL module needed for this to work."
	print "pyADL can be found at: http://www.bitshift.io/pyADL/"
	sys.exit(1)

os.chdir(os.path.dirname(os.path.abspath(__file__)))

VERSION = '2011.07.06'

USER_AGENT = 'stripminer/' + VERSION

LOG_LEVEL = logging.DEBUG
LOG_FORMAT = '%(asctime)s %(name)-10s %(levelname)-8s %(message)s'
LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'

def Miner(device, options):
	log = logging.getLogger('GPU%d-MINER' % device)
	log.info('Worker starting on device %d', device)
	log.debug('Setting DISPLAY variable for device %d', device)
	os.environ['DISPLAY'] = ':0.%d' % device
	log.debug('Confirming environment: %s', os.environ['DISPLAY'])
	log.debug('Checking that device is found now that DISPLAY is set')

	platform = cl.get_platforms()[0]
	devices = platform.get_devices()


	class StripMiner(BitcoinMiner):
		def say(self, format, args=()):
			log.info(format % args)

		def sayLine(self, format, args=()):
			if(format == 'verification failed, check hardware!'):
				log.warn(format % args)
			else:
				self.say(format, args)

	try:
		miner = StripMiner(devices[device],
			options.host,
			options.user,
			options.password,
			int(options.port),
			int(options.frames),
			float(options.rate),
			int(options.askrate),
			int(options.worksize),
			bool(options.vectors),
			bool(options.verbose))
		miner.mine()
	except:
		log.info('Miner is exiting', device)
	finally:
		if miner: miner.exit()

def main():
	oParser = OptionParser(version=USER_AGENT,
			description='Bitcoin strip mining daemon')
	oParser.add_option('-c', '--config', action='store',
		dest='configfile', default='stripminer.cfg')
	oParser.add_option('-p', '--pool', action='store',
		dest='pool', default=None)
	(options, args) = oParser.parse_args()

	try:
		cParser = ConfigParser.SafeConfigParser()
		cParser.read([options.configfile, os.path.expanduser('~/.stripminer.cfg')])
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

	# Setup logging if section is found in config
	if options.logfile:
		logfile = options.logfile
		# logfile += '_' + strftime("%Y-%m-%d_%H%M%S")
		logfile += '.log'
		logging.basicConfig(filename=logfile, 
			level=LOG_LEVEL, format=LOG_FORMAT, datefmt=LOG_DATEFMT)

	log = logging.getLogger('stripminer')

	# Collection GPU card information
	log.info('Collecting available GPU information')
	os.environ['DISPLAY'] = ':0'
	devices = ADL.getNumGPU()

	# Fire off mining workers for each device
	processes = []
	for device in devices:
		gpuidx = device['GPU']
		ADL.setIndex(gpuidx)
		log.info('Device[GPU%d] %s (Core: %d, Memory: %d, Fan %d%%)',
			gpuidx, device['Name'], ADL.getCoreClockSpeed(),
			ADL.getMemoryClockSpeed(), ADL.getFanSpeed())
		if cParser.has_section('ADL_GPU%d' % gpuidx):
			log.debug('Found ADL settings for GPU%d', gpuidx)
			if cParser.has_option('ADL_GPU%d' % gpuidx, 'core'):
				core = cParser.getint('ADL_GPU%d' % gpuidx, 'core')
				log.debug('Device[GPU%d] setting Core to %d Mhz', gpuidx, core)
				ADL.setCoreClockSpeed(2, core)
			if cParser.has_option('ADL_GPU%d' % gpuidx, 'memory'):
				memory = cParser.getint('ADL_GPU%d' % gpuidx, 'memory')
				log.debug('Device[GPU%d] setting Memory to %d Mhz', gpuidx, memory)
				ADL.setMemoryClockSpeed(1, memory)
				ADL.setMemoryClockSpeed(2, memory)
			if cParser.has_option('ADL_GPU%d' % gpuidx, 'fan'):
				fan = cParser.getint('ADL_GPU%d' % gpuidx, 'fan')
				log.debug('Device[GPU%d] setting Fan to %d%%', gpuidx, fan)
				ADL.setFanSpeed(fan)

		p = Process(target=Miner, args=(gpuidx, options))
		processes.append(p)

	try:
		for process in processes:
			process.start()
			process.join()
	except KeyboardInterrupt:
		log.info('Closing down the mine!')
	finally:
		for process in processes:
			if process.is_alive():
				process.terminate()
				sleep(1.1)

if __name__ == '__main__':
	main()
