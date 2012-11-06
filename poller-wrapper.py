#! /usr/bin/env python
"""
 poller-wrapper A small tool which wraps around the Observium poller
                and tries to guide the polling process with a more modern
                approach with a Queue and workers

 Author:        Job Snijders <job.snijders@atrato-ip.com>
 Date:          5 November 2012, 22:01 CET

 Usage:         This program accepts one command line argument: the number of threads
                that should run simultaneously. If no argument is given it will assume
                a default of 8 threads.

                In /etc/cron.d/observium replace this (or the equivalent) poller entry:
                */5 *     * * *   root    /opt/observium/poller.php -h all >> /dev/null 2>&1
                with something like this:
                */5 * * * * root python /opt/observium/poller-wrapper.py 16 >> /dev/null 2>&1

 Read more:     http://postman.memetic.org/pipermail/observium/2012-November/001303.html

 Requirements:  python, MySQLdb, Queue, subprocess
 Ubuntu Linux:  apt-get install py-mysql
 FreeBSD:       cd /usr/ports/*/py-MySQLdb && make install clean

 Tested on:     Python 2.7.3 / Ubuntu 12.04 LTS
 
 GitHub:        https://github.com/Atrato/observium-poller-wrapper

"""

"""
    Configure the relevant DB settings here
    I could've tried to parse config.php, but this was much easier
"""
db_username = "observium"
db_password = "tralala"
db_server   = "127.0.0.1"
db_dbname   = "observium"

poller_path = "/opt/observium/poller.php"

import threading, Queue, sys, MySQLdb, subprocess, time

s_time = time.time()

"""
    Take the amount of threads we want to run in parallel from the commandline
    if None are given or the argument was garbage, fall back to default of 8
"""
try:
    amount_of_workers = int(sys.argv[1])
except:
    amount_of_workers = 8

devices_list = []

db = MySQLdb.connect (host=db_server, user=db_username , passwd=db_password, db=db_dbname)
cursor = db.cursor()

""" 
    This query specificly orders the results depending on the last_polled_timetaken variable
    Because this way, we put the devices likely to be slow, in the top of the queue
    thus greatening our chances of completing _all_ the work in exactly the time it takes to 
    poll the slowest device! cool stuff he
"""
query = "select device_id from devices where disabled = 0 order by last_polled_timetaken desc"

cursor.execute(query)
devices = cursor.fetchall()
for row in devices:
    devices_list.append(int(row[0]))
db.close()

"""
    A seperate queue and a single worker for printing information to the screen prevents
    the good old joke:

        Some people, when confronted with a problem, think, 
        "I know, I'll use threads," and then two they hav erpoblesms.
"""

def printworker():
    while True:
        worker_id, device_id, elapsed_time = print_queue.get()
        print "worker %s finished device %s in %s seconds" % (worker_id, device_id, elapsed_time)
        print_queue.task_done()

"""
    This class will fork off single instances of the poller.php process, record
    how long it takes, and push the resulting reports to the printer queue
"""

def poll_worker():
    while True:
        device_id = poll_queue.get()
        try:
            start_time = time.time()
            command = "/usr/bin/env php %s -h %s >> /dev/null 2>&1" % (poller_path, device_id)
            subprocess.check_call(command, shell=True)
            elapsed_time = int(time.time() - start_time)
            print_queue.put([threading.current_thread().name, device_id, elapsed_time])
        except:
            pass
        poll_queue.task_done()

poll_queue = Queue.Queue()
print_queue = Queue.Queue()

print "starting the poller at %s with %s threads, slowest devices first" % (time.time(), amount_of_workers)

for device_id in devices_list:
    poll_queue.put(device_id)
 
for i in range(amount_of_workers):
    t = threading.Thread(target=poll_worker)
    t.setDaemon(True)
    t.start()

p = threading.Thread(target=printworker)
p.setDaemon(True)
p.start()
   
poll_queue.join()
print_queue.join()

total_time = int(time.time() - s_time)

if total_time > 300:
    print "WARNING: the process took more than 5 minutes to finish, need faster hardware or more threads"
print "poller-wrapper polled %s devices in %s seconds with %s workers" % (len(devices_list), total_time, amount_of_workers)

