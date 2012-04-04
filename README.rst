.. -*- restructuredtext -*-

Chronograph
===========

Control ``django-admin`` commands via the web.

Creating cron jobs for Django apps can be a pain, annoying and repetitive. With
``django-chronograph`` you simply create a single cron job to run every minute,
point it at your site's directory and run ``manage.py cron``. Then from the admin
you can add jobs.


.. Note::

	``django-chronograph`` supports Django 1.1+.

Installation and Usage
======================

Read docs/overview.txt for more information, build the documentation with
Sphinx or view them online here_.

.. _here: http://readthedocs.org/docs/django-chronograph/en/latest/overview.html

You can also grab the latest release from PyPI::

	pip install django-chronograph