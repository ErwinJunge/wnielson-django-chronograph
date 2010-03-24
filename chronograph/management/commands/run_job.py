from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.template import loader, Context

from chronograph.models import Job, Log

import sys
import traceback

from datetime import datetime
from StringIO import StringIO

class Command(BaseCommand):
    help = 'Runs a specific job, but only if it is not currently running.'
    args = "job.id"
    
    def handle(self, *args, **options):
        try:
            job_id = args[0]
        except IndexError:
            sys.stderr.write("This command requires a single argument: a job id to run.\n")
            return

        try:
            job = Job.objects.get(pk=job_id)
        except Job.DoesNotExist:
            sys.stderr.write("The requested Job does not exist.\n")
            return
        
        args, options = job.get_args()
        stdout = StringIO()
        stderr = StringIO()

        # Redirect output so that we can log it if there is any
        ostdout = sys.stdout
        ostderr = sys.stderr
        sys.stdout = stdout
        sys.stderr = stderr
        stdout_str, stderr_str = "", ""

        run_date = datetime.now()
        job.is_running = True
        job.save()
        try:
            call_command(job.command, *args, **options)
        except Exception, e:
            # The command failed to run; log the exception
            t = loader.get_template('chronograph/error_message.txt')
            c = Context({
              'exception': unicode(e),
              'traceback': ['\n'.join(traceback.format_exception(*sys.exc_info()))]
            })
            stderr_str += t.render(c)
        job.is_running = False
        job.last_run = run_date
        job.next_run = job.rrule.after(run_date)
        job.save()

        # If we got any output, save it to the log
        stdout_str += stdout.getvalue()
        stderr_str += stderr.getvalue()
        if stdout_str or stderr_str:
            log = Log.objects.create(
                job = job,
                run_date = run_date,
                stdout = stdout_str,
                stderr = stderr_str
            )

        # Redirect output back to default
        sys.stdout = ostdout
        sys.stderr = ostderr
        