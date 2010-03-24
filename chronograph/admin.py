from django import forms
from django.conf.urls.defaults import patterns, url
from django.contrib import admin
from django.core.management import get_commands
from django.core.urlresolvers import reverse, NoReverseMatch
from django.db import models
from django.forms.util import flatatt
from django.http import HttpResponseRedirect, Http404
from django.template.defaultfilters import linebreaks
from django.utils import dateformat
from django.utils.datastructures import MultiValueDict
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.translation import ungettext, get_date_formats, ugettext_lazy as _

from chronograph.models import Job, Log

from datetime import datetime

class HTMLWidget(forms.Widget):
    def __init__(self,rel=None, attrs=None):
        self.rel = rel
        super(HTMLWidget, self).__init__(attrs)
    
    def render(self, name, value, attrs=None):
        if self.rel is not None:
            key = self.rel.get_related_field().name
            obj = self.rel.to._default_manager.get(**{key: value})
            related_url = '../../../%s/%s/%d/' % (self.rel.to._meta.app_label, self.rel.to._meta.object_name.lower(), value)
            value = "<a href='%s'>%s</a>" % (related_url, escape(obj))
            
        final_attrs = self.build_attrs(attrs, name=name)
        return mark_safe("<div%s>%s</div>" % (flatatt(final_attrs), linebreaks(value)))

class JobAdmin(admin.ModelAdmin):
    list_display = ('name', 'last_run_with_link', 'next_run', 'get_timeuntil',
                    'frequency', 'params',  'is_running', 'run_button', 'view_logs_button')
    list_filter = ('frequency', 'disabled',)
    fieldsets = (
        (None, {
            'fields': ('name', ('command', 'args',), 'disabled',)
        }),
        ('Frequency options', {
            'classes': ('wide',),
            'fields': ('frequency', 'next_run', 'params',)
        }),
    )
    actions = ['run_selected_jobs']
    
    def last_run_with_link(self, obj):
        format = get_date_formats()[1]
        value = capfirst(dateformat.format(obj.last_run, format))
        
        try:
            log_id = obj.log_set.latest('run_date').id
            try:
                # Old way
                url = reverse('chronograph_log_change', args=(log_id,))
            except NoReverseMatch:
                # New way
                url = reverse('admin:chronograph_log_change', args=(log_id,))
            return '<a href="%s">%s</a>' % (url, value)
        except:
            return value
    last_run_with_link.allow_tags = True
    last_run_with_link.short_description = 'Last run'
    last_run_with_link.admin_order_field = 'last_run'
    
    def get_timeuntil(self, obj):
        return obj.get_timeuntil()
    get_timeuntil.short_description = _('time until next run')
    get_timeuntil.admin_order_field = 'next_run'
    
    def run_button(self, obj):
        on_click = "window.location='%d/run/?inline=1';" % obj.id
        return '<input type="button" onclick="%s" value="Run" />' % on_click
    run_button.allow_tags = True
    run_button.short_description = 'Run'
    
    def view_logs_button(self, obj):
        on_click = "window.location='../log/?job=%d';" % obj.id
        return '<input type="button" onclick="%s" value="View Logs" />' % on_click
    view_logs_button.allow_tags = True
    view_logs_button.short_description = 'Logs'
    
    def run_job_view(self, request, pk):
        """
        Runs the specified job.
        """
        try:
            job = Job.objects.get(pk=pk)
        except Job.DoesNotExist:
            raise Http404
        # Rather than actually running the Job right now, we
        # simply schedule the Job to be run by the next cron job
        job.next_run = datetime.now()
        job.save()
        request.user.message_set.create(message=_('The job "%(job)s" has been scheduled to run.') % {'job': job})        
        if 'inline' in request.GET:
            redirect = request.path + '../../'
        else:
            redirect = request.REQUEST.get('next', request.path + "../")
        return HttpResponseRedirect(redirect)
    
    def get_urls(self):
        urls = super(JobAdmin, self).get_urls()
        my_urls = patterns('',
            url(r'^(.+)/run/$', self.admin_site.admin_view(self.run_job_view), name="chronograph_job_run")
        )
        return my_urls + urls
    
    def run_selected_jobs(self, request, queryset):
        rows_updated = queryset.update(next_run=datetime.now())
        if rows_updated == 1:
            message_bit = "1 job was"
        else:
            message_bit = "%s jobs were" % rows_updated
        self.message_user(request, "%s successfully set to run." % message_bit)
    run_selected_jobs.short_description = "Run selected jobs"
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        request = kwargs.pop("request", None)
        
        # Add a select field of available commands
        if db_field.name == 'command':
            choices_dict = MultiValueDict()
            for command, app in get_commands().items():
                choices_dict.appendlist(app, command)
            
            choices = []
            for key in choices_dict.keys():
                #if str(key).startswith('<'):
                #    key = str(key)
                commands = choices_dict.getlist(key)
                commands.sort()
                choices.append([key, [[c,c] for c in commands]])
                
            kwargs['widget'] = forms.widgets.Select(choices=choices)
            return db_field.formfield(**kwargs)
            
        return super(JobAdmin, self).formfield_for_dbfield(db_field, **kwargs)

class LogAdmin(admin.ModelAdmin):
    list_display = ('job_name', 'run_date',)
    search_fields = ('stdout', 'stderr', 'job__name', 'job__command')
    date_hierarchy = 'run_date'
    fieldsets = (
        (None, {
            'fields': ('job',)
        }),
        ('Output', {
            'fields': ('stdout', 'stderr',)
        }),
    )
    
    def job_name(self, obj):
      return obj.job.name
    job_name.short_description = _(u'Name')
    
    def has_add_permission(self, request):
        return False
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        request = kwargs.pop("request", None)
        
        if isinstance(db_field, models.TextField):
            kwargs['widget'] = HTMLWidget()
            return db_field.formfield(**kwargs)
        
        if isinstance(db_field, models.ForeignKey):
            kwargs['widget'] = HTMLWidget(db_field.rel)
            return db_field.formfield(**kwargs)
        
        return super(LogAdmin, self).formfield_for_dbfield(db_field, **kwargs)

admin.site.register(Job, JobAdmin)
admin.site.register(Log, LogAdmin)