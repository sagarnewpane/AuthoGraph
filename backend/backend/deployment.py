"""Production entrypoint; all security settings come from the shared environment."""
import os
os.environ.setdefault('DJANGO_DEBUG', 'false')
from .settings import *  # noqa: F403

STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}
