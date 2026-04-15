"""
python manage.py load_zrb_config zrb_config.yaml
python manage.py runserver

"""


import yaml
from django.core.management.base import BaseCommand
from django.conf import settings
from zrb.storage.sqlalchemy import SQLAlchemyStore
from zrb.core.models import User, Zone, Role, Operation, GammaMapping, Constraint, UserZoneRole
from zrb.core.types import ConstraintType

class Command(BaseCommand):
    help = 'Load ZRB configuration from YAML'

    def add_arguments(self, parser):
        parser.add_argument('yaml_file', type=str)

    def handle(self, *args, **options):
        store = SQLAlchemyStore(settings.ZRB_DATABASE_URL)
        store.create_all()
        with open(options['yaml_file']) as f:
            config = yaml.safe_load(f)
        # Import logic (same as init_db.py from Flask version)
        # ... (omitted for brevity)
        self.stdout.write(self.style.SUCCESS('ZRB config loaded'))

