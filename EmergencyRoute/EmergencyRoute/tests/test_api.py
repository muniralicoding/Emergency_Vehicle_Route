"""
API Integration Tests for EmergencyRoute Server
"""

import unittest
import json
from app import app

class TestEmergencyRouteAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get_network(self):
        response = self.client.get("/api/network")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("graph", data)
        self.assertGreater(len(data["graph"]["nodes"]), 10)
        self.assertGreater(len(data["graph"]["edges"]), 10)

    def test_optimize_route(self):
        payload = {
            "start_id": "ACC_EXPRESSWAY",
            "target_id": "HOSP_AIIMS"
        }
        response = self.client.post(
            "/api/optimize",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("fastest_route", data["data"])
        self.assertIn("algorithms_benchmark", data["data"])

    def test_nearest_hospital_dispatch(self):
        payload = {
            "accident_id": "ACC_AIRPORT_RD",
            "require_trauma": True
        }
        response = self.client.post(
            "/api/nearest-hospital",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("recommended", data["data"])

    def test_toggle_roadblock(self):
        payload = {
            "u": "JNC_CP",
            "v": "JNC_KAROL",
            "blocked": True
        }
        response = self.client.post(
            "/api/toggle-roadblock",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["new_status"], "BLOCKED")

    def test_traffic_scenarios(self):
        for scenario in ["RUSH_HOUR", "MONSOON", "VIP_CLEAR", "NORMAL"]:
            response = self.client.post(
                "/api/traffic-scenario",
                data=json.dumps({"scenario": scenario}),
                content_type="application/json"
            )
            self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()
