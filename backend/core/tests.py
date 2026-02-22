from django.test import TestCase
from django.urls import reverse

class HealthTest(TestCase):
    def test_health_endpoint(self):
        # Ajuste se você usar um name=... na url
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "ok")