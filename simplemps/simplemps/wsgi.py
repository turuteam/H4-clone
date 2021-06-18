"""
WSGI config for simplemps project.
It exposes the WSGI callable as a module-level variable named ``application``.
For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os
import sys

#path to django/dir
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
#path to django/dir/django_proj
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

application = get_wsgi_application()

