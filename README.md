observium-poller-wrapper
========================

A small wrapper around Observium's poller.php script to speed it up.

Are you not sleeping well because there are gaps in your graphs? Do you feel
like your observium poller isn't putting enough effort into its sole task of
polling every device and completing that task in less than 5 minutes?

Fear not, a dirty script called "poller-wrapper.py" is here!

This program accepts one command line argument: the number of threads
that should run simultaneously. If no argument is given it will assume
a default of 8 threads.

In /etc/cron.d/observium replace this (or the equivalent) poller entry:

    */5 * * * *   root    /opt/observium/poller.php -h all >> /dev/null 2>&1

with something like this:

    */5 * * * * root python /opt/observium/poller-wrapper.py 16 >> /dev/null 2>&1

Requirements:

    python, MySQLdb, Queue, subprocess

Tested on:
	Python 2.7.3 / Ubuntu 12.04 LTS
	Python 2.6.6 / Debian 6 (Squeeze)

