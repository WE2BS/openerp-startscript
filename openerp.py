#!/usr/bin/python
# -*- encoding: utf-8 -*-
#
# OpenERP StartScript - A start/stop script for OpenERP
# Copyright (C) 2010-Today Thibaut DIRLIK <thibaut.dirlik@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
This script starts/stop OpenERP using start-stop-daemon on debian/ubuntu.

The best way to use it is to pull latest stable branch from launchpad :
    $ bzr branch lp:openobject-server/6.0 server
    $ bzr branch lp:openobject-client-web/6.0 web

Then just use the script in the top-directory :
    $ ./openerp.py start server
    $ ./openerp.py start web-server

You can stop servers using 'stop' and get status using 'status'. Please be aware that using this
script will not show process' output, so you have to enable logging in OpenERP configuration files.

Installation
============

You can easily create a link to the openerp.py in /usr/loca/bin, to be able to use
the script from anywhere on the system :

    $ cd /usr/local/bin
    $ ln -s <path to openerp.py> openerp

And now, you can use it like this :

    $ cd <path where there are 'server' or 'web' directory>
    $ openerp start server
    $ openerp start webserver
"""

from __future__ import with_statement

import sys
import os
import subprocess
import optparse
import shlex
import logging

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(levelname)s: %(message)s')

# Commands used to start/stop programs
START_COMMAND = 'start-stop-daemon --start --quiet --startas %(script)s ' \
                '--make-pidfile --background --chdir %(dir)s --pidfile %(pidfile)s'
STOP_COMMAND = 'start-stop-daemon --stop --quiet --pidfile %(pidfile)s -R TERM/15/KILL/5'

# Common args passed to Popen()
POPEN_ARGS = { 'stdout' : subprocess.PIPE, 'stderr' : subprocess.PIPE }

def start(directory, program, pidfile):

    """
    Starts the program with `start-stop-daemon`.
    """

    command = START_COMMAND % {'script' : program, 'dir' : directory, 'pidfile' : pidfile}
    process = subprocess.Popen(shlex.split(command), **POPEN_ARGS)
    output, error = process.communicate()

    logging.debug('Running "%s", returncode=%d.' % (command, process.returncode))

    if process.returncode == 1:
        message = 'The process is already running !'
    elif process.returncode > 1:
        message = 'An error occured, here is the output :\n ' + str(output) + str(error)
    else:
        return 0
    
    return exit(process.returncode, message)

def stop(pidfile):

    """
    Starts the program with `start-stop-daemon`.
    """

    command = STOP_COMMAND % {'pidfile' : pidfile}
    process = subprocess.Popen(shlex.split(command), **POPEN_ARGS)
    output, error = process.communicate()

    logging.debug('Running "%s", returncode=%d.' % (command, process.returncode))

    if process.returncode == 1:
        message = 'The process is not running !'
    elif process.returncode > 1:
        message = 'An error occured, here is the output : \n ' + str(output) + str(error)
    else:
        return 0

    return exit(process.returncode, message)

def exit(code, message):

    """
    Print the message and returns the code.
    """

    logging.error(message)
    return code

def main(argv):

    """
    Main function called when executing the script.
    """

    parser = optparse.OptionParser('Usage: %s [options] <start|stop|restart|status> <server|webserver>' % argv[0])
    parser.add_option('--server-dir', default='server', help='Server directory', dest='server_dir')
    parser.add_option('--webserver-dir', default='web', help='WebServer directory', dest='webserver_dir')
    parser.add_option('--user', default='openerp', help='Unix user used to start processes', dest='user')
    parser.add_option('--debug', action='store_true', help='Unix user used to start processes', dest='debug')

    options, args = parser.parse_args(argv[1:])

    if options.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if len(args) < 2 or args[0] not in ('start', 'stop', 'restart', 'status') or args[1] not in ('server','webserver'):
        return exit(1, 'ERROR: Use "%s --help" to get more informations.' % argv[0])

    command, target = args[0:2]

    if target == 'server':
        program = os.path.join(options.server_dir, 'bin', 'openerp-server.py')
        pidfile = os.path.join(options.server_dir, 'bin', 'server.pid')
    elif target == 'webserver':
        program = os.path.join(options.webserver_dir, 'openerp-web.py')
        pidfile = os.path.join(options.webserver_dir, 'webserver.pid')
    else:
        return exit(1, 'Invalid target: %s' % target)

    if not os.path.exists(program):
        return exit(1, "The '%s' program file doesn't exist: %s." % (target, program))

    if command == 'start':
        code = start(os.getcwd(), program, pidfile)
        if code == 0:
            logging.info('The target "%s" has been started correctly.' % target)
        return code

    if command == 'stop':
        code = stop(pidfile)
        if code == 0:
            logging.info('The target "%s" has been stopped correctly.' % target)
        return code

    if command == 'restart':
        code_stop = stop(pidfile)
        code_start = start(os.getcwd(), program, pidfile)
        if code_stop != 0 or code_start != 0:
            return exit(1, 'Error while restarting the target "%s".' % target)
        return 0

    if command == 'status':
        with open(pidfile) as file:
            pid = file.readline().strip()
            if os.path.exists(os.path.join('/proc', pid)):
                logging.info('The target "%s" is running.' % target)
            else:
                logging.info('The target "%s" is stopped.' % target)
        return 0
    
if __name__ == '__main__':
    sys.exit(main(sys.argv))
