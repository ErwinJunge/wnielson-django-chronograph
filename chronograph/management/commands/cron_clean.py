from django.core.management.base import BaseCommand
from django.core.exceptions import ImproperlyConfigured
import sys

class Command( BaseCommand ):
    help = 'Deletes old job logs.'
    
    def handle( self, *args, **options ):
        from chronograph.models import Log
        from datetime import datetime, timedelta
                
        if len( args ) != 2:
            sys.stderr.write('Command requires two argument. Unit (weeks, days, hours or minutes) and interval.')
            raise Exception
        else:
            unit = str( args[ 0 ] )
            if unit not in [ 'weeks', 'days', 'hours', 'minutes' ]:
                sys.stderr.write('Valid units are weeks, days, hours or minutes.')
                raise Exception
            try:
                amount = int( args[ 1 ] ) 
            except ValueError:
                sys.stderr.write('Interval must be an integer.')
                raise Exception
        kwargs = { unit: amount }
        time_ago = datetime.now() - timedelta( **kwargs )
        Log.objects.filter( run_date__lte = time_ago ).delete()