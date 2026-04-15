from django.conf import settings
from zrb.storage.sqlalchemy import SQLAlchemyStore

zrb_store = SQLAlchemyStore(settings.ZRB_DATABASE_URL)

class ZoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0]
        # Map subdomain to zone ID
        subdomain = host.split('.')[0] if '.' in host else None
        zone_id = {
            'branch-a': 'branch_a',
            'branch-b': 'branch_b',
            'head-office': 'head_office',
            'risk': 'risk',
            'audit': 'audit',
            None: 'bank',
        }.get(subdomain, 'bank')
        request.zone = zrb_store.get_zone(zone_id)
        return self.get_response(request)