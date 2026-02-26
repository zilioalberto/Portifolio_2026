from django.test import TestCase

from django.test import TestCase
from accounts.models import User
from projects.models import Project

class WizardHappyPathTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u1", password="x", role=User.Role.ADMIN)

    def test_happy_path_generate_bom(self):
        # cria projeto
        p = Project.objects.create(name="Projeto 1", panel_type=Project.PanelType.AUTOMATION, created_by=self.user)

        # step1
        resp = self.client.put(
            f"/api/projects/{p.id}/step1/",
            data={
                "voltage_v": 380,
                "frequency_hz": 60,
                "phase_system": "3P",
                "has_neutral": True,
                "icc_range_ka": "10",
                "control_voltage": "24VDC",
                "ambient_temp_c": 35,
                "ip_rating": "IP54",
                "standard": "IEC_60204_1",
                "has_drives_emc": False,
            },
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)

        # add carga motor
        resp = self.client.post(
            f"/api/projects/{p.id}/loads/",
            data={
                "name": "Motor Esteira",
                "type": "MOTOR",
                "quantity": 1,
                "motor": {"power_kw": "2.20", "voltage_v": 380, "drive_type": "DOL"},
            },
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)

        # gerar bom
        resp = self.client.post(f"/api/projects/{p.id}/generate-bom/", content_type="application/json")
        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        self.assertIn("bom", body)
        self.assertGreaterEqual(len(body["bom"]["items"]), 2)

    def test_generate_bom_fails_without_step1(self):
        p = Project.objects.create(name="Projeto 2", panel_type=Project.PanelType.AUTOMATION, created_by=self.user)
        resp = self.client.post(f"/api/projects/{p.id}/generate-bom/", content_type="application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("alerts", resp.json())