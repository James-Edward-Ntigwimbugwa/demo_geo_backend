from django.test import TestCase, RequestFactory
from asgiref.sync import async_to_sync
import json

from .views import base_floor_view


class BaseFloorViewTests(TestCase):
    def setUp(self):
        self.rf = RequestFactory()

    def test_base_floor_get_returns_geojson(self):
        """Verify the async endpoint returns parsed GeoJSON and expected fields.

        This test patches `sync_to_async` to avoid touching the real DB and returns
        a deterministic row set.
        """
        # Fake execute function that returns rows like _dictfetchall() would
        def fake_execute(sql, params=None):
            return [{
                'ogc_fid': 1,
                'layer': 'L1',
                'paperspace': False,
                'text': 'floor A',
                'geometry': json.dumps({'type': 'LineString', 'coordinates': []})
            }]

        # Patch the module-level sync_to_async to return an async function that runs fake_execute
        import interactive_maps_backend_main.views as vmod

        async def fake_async_execute(*a, **k):
            return fake_execute(*a, **k)

        vmod.sync_to_async = lambda fn: (lambda *a, **k: fake_async_execute(*a, **k))

        request = self.rf.get('/api/base-floor/')
        response = async_to_sync(base_floor_view)(request)

        self.assertEqual(response.status_code, 200)
        parsed = json.loads(response.content)
        self.assertIsInstance(parsed, list)
        self.assertEqual(len(parsed), 1)
        item = parsed[0]
        self.assertEqual(item['ogc_fid'], 1)
        self.assertEqual(item['layer'], 'L1')
        self.assertEqual(item['text'], 'floor A')
        self.assertIn('geometry', item)
