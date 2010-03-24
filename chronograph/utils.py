from django.conf import settings
import subprocess

MANAGE_PY = '/Users/wnielson/Projects/chronograph-daemon/project/manage.py'

try:
    import psutil
    USE_PSUTIL = True
except ImportError:
    USE_PSUTIL = False

def is_running(job):
    if job.is_running and job.pid is not None:
        # The Job thinks that it is running, so
        # lets actually check, but only if psutil
        # is available
        if USE_PSUTIL:
            try:
                p = psutil.Process(job.pid)
            except:
                # The process with this pid doesn't
                # exist, so this job isn't running
                job.is_running = False
                job.pid = None
                job.save()
                return False
            # Now that we have a process, lets check to
            # see if it is actually this Job's process
            
    return False

def run_job(job, wait):
    """
    Runs the ``job``.  This actually calls the management command
    ``run_job`` via a subprocess.  If you call this and want to wait
    for the process to complete, pass ``wait=True``.
    
    Returns the process, a ``subprocess.Popen`` instance.
    """
    if not is_running(job):
        p = subprocess.Popen(['python', MANAGE_PY, 'run_job', str(job.id)])
        if wait:
            p.wait()
        return p