==========================================
A PL/SQL packages mapper for Django
==========================================

Django-plsql enables your system to create python module with callable functions to
each PL/SQL package function and procedure.

* map PL/SQL packages to corresponding python module.

Requirements
------------

plsql-mapper 0.1 requires

* Django (http://www.djangoproject.com)
* cx_Oracle (http://cx-oracle.sourceforge.net/)

Documentation
-------------

http://readthedocs.org/docs/django-filebrowser/

Translation
-----------

https://www.transifex.net/projects/p/django-filebrowser/

Versions
--------

* The current trunk/head is compatible with Django 1.2; users of Django 1.1
  should continue using messages-0.4.x; if you are upgrading from 0.4.x to trunk
  please read the UPGRADING docs.
* messages-0.4.x is compatible with Django 1.1 (and may work with Django 1.0).
  The code is avaliable as a Branch.
* messages-0.3 is compatible with Django 1.0, but no longer maintained
* messages-0.2 is still compatible with Django 0.96.x, but not longer maintaned.
  The code is avalibale as a Branch.


Documentation
-------------

The documentation is contained in the /docs/ directory and can be build with
sphinx. A HTML version of the documentation is available at:
http://files.arnebrodowski.de/software/django-messages/Documentation/


Install
-------
Download the tar archive, unpack and run python setup.py install or checkout
the trunk and put the ``django_messages`` folder on your ``PYTHONPATH``.
Released versions of django-messages are also available on pypi and can be
installed with easy_install or pip.


Usage
-----

Add ``django_messages`` to your ``INSTALLED_APPS`` setting and add an
``include('django_messages.urls')`` at any point in your url-conf.

The app includes some default templates, which are pretty simple. They
extend a template called ``base.html`` and only emit stuff in the block
``content`` and block ``sidebar``. You may want to use your own templates,
but the included ones are good enough for testing and getting started.


Dependencies
------------

Django-messages has no external dependencied except for django. But if
django-notification and/or django-mailer are found it will make use of them.
Note: as of r65 django-messages will only use django-notification if
'notification' is also added to the INSTALLES_APPS setting. This has been
done to make situations possible where notification is on pythonpath but
should not be used, or where notification is an other python package as
django-notification which has the same name.



