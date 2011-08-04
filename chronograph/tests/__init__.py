import datetime
import time

from django.core.management import _commands

from chronograph.models import Job, Log, freqs

try:
    from django.utils import unittest
except:
    import unittest

from commands import Sleeper

class JobTestCase(unittest.TestCase):
    jobs = []
    
    def setUp(self):
        # Install the test command; this little trick installs the command
        # so that we can refer to it by name
        _commands['test_sleeper'] = Sleeper()
        
        # Create some Job instances and edd them to the database
        now = datetime.datetime.now()
        next_run = datetime.datetime(year=now.year, month=now.month,
                                     day=now.day, hour=now.hour,
                                     minute=now.minute)
        for i in range(10):
            attribs = {
                'name':      'Sleeper %d' % i,
                'args':      str(i),
                'frequency': 'MINUTELY',
                'command':   'test_sleeper',
                'params':    'interval:%d' % (i+1),
                'next_run':  next_run
            }
            self.jobs.append(Job.objects.create(**attribs))
        self.next_run = next_run
    
    def testJobRun(self):
        """
        Test that the jobs run properly.
        """
        for i, job in enumerate(self.jobs[:4]):
            time_expected = float(job.args)
            
            time_start = time.time()
            job.run()
            time_end = time.time()
            
            time_taken = time_end - time_start
            self.assertAlmostEqual(time_taken, time_expected, delta=1.2)
