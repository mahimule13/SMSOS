"""
ASGI config for schoolms project.
"""

import os
import importlib.util
import pkgutil

if not hasattr(pkgutil, 'find_loader'):
    def _find_loader(name, path=None):
        return importlib.util.find_spec(name, path)
    pkgutil.find_loader = _find_loader

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolms.settings')

application = get_asgi_application()
