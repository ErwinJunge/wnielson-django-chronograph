from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Runs all jobs that are due.'
    
    def handle(self, *args, **options):
        from chronograph.models import Job
        procs = []
        for job in Job.objects.due():
            procs.append(job.run(False))
        for p in procs:
            p.wait()