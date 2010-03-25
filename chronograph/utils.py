from django.conf import settings
from django.core.management import setup_environ
from django.utils.importlib import import_module

import os
import re
import subprocess

def get_manage_py():
    module = import_module(settings.SETTINGS_MODULE)
    return os.path.join(setup_environ(module, settings.SETTINGS_MODULE), 'manage.py')

def is_running(job):
    if job.is_running and job.pid is not None:
        # The Job thinks that it is running, so
        # lets actually check
        if os.name == 'posix':
            # Try to use the 'ps' command to see if the process
            # is still running
            pid_re = re.compile(r'%d ([^\r\n]*)\n' % job.pid)
            p = subprocess.Popen(["ps", "-eo", "pid args"], stdout=subprocess.PIPE)
            p.wait()
            for pname in pid_re.findall(p.stdout.read()):
                # If we've gotten here, it means that we have a running process
                # with this ``job.pid``.  Now we must check for the ``run_command``
                # process with the given ``job.pk``
                return pname.find('run_job %d' % job.pk) > -1
    return False

def run_job(job, wait):
    """
    Runs the ``job``.  This actually calls the management command
    ``run_job`` via a subprocess.  If you call this and want to wait
    for the process to complete, pass ``wait=True``.
    
    Returns the process, a ``subprocess.Popen`` instance.
    """
    if not is_running(job):
        p = subprocess.Popen(['python', get_manage_py(), 'run_job', str(job.id)])
        if wait:
            p.wait()
        return p