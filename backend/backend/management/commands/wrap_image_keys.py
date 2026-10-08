"""Wrap historical database keys without changing image files."""
from django.core.management.base import BaseCommand
from backend.models import UserImage
from backend.encryption import wrap_key, unwrap_key


class Command(BaseCommand):
    help = 'Wrap or rotate image keys. Dry-run unless --apply is supplied; back up database and master key first.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true')

    def handle(self, *args, **options):
        count = 0
        for image in UserImage.objects.exclude(encryption_key__isnull=True).exclude(encryption_key='').iterator():
            key = unwrap_key(image.encryption_key)
            if options['apply']:
                UserImage.objects.filter(pk=image.pk).update(encryption_key=wrap_key(key))
            count += 1
        self.stdout.write(f'{count} image keys {"wrapped" if options["apply"] else "readable; no changes made"}.')
