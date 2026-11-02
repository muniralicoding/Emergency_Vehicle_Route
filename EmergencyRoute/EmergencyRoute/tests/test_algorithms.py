"""
Unit Tests for EmergencyRoute DAA Algorithms & Network
"""

import unittest
from core.city_network import create_default_city_network
from algorithms.dijkstra import dijkstra_shortest_path
from algorithms.a_star import a_star_search
from algorithms.greedy import greedy_best_first_search
from algorithms.comparison import benchmark_and_compare, find_nearest_available_hospital

class TestEmergencyRouteAlgorithms(unittest.TestCase):
    def setUp(self):
        self.graph = create_default_city_network()

    def test_dijkstra_path_found(self):
        # Route from Airport Accident to AIIMS
        res = dijkstra_shortest_path(self.graph, "ACC_AIRPORT_RD", "HOSP_AIIMS", weight_mode="time")
        self.assertTrue(res.success)
        self.assertGreater(len(res.path), 1)
        self.assertEqual(res.path[0], "ACC_AIRPORT_RD")
        self.assertEqual(res.path[-1], "HOSP_AIIMS")
        self.assertIsNotNone(res.total_time_min)
        self.assertGreater(res.total_distance_km, 0.0)

    def test_a_star_optimality_matches_dijkstra(self):
        start = "ACC_EXPRESSWAY"
        target = "HOSP_AIIMS"
        dijkstra_res = dijkstra_shortest_path(self.graph, start, target, weight_mode="time")
        astar_res = a_star_search(self.graph, start, target, weight_mode="time")

        self.assertTrue(dijkstra_res.success)
        self.assertTrue(astar_res.success)
        # Optimal cost should match within floating point precision
        self.assertAlmostEqual(dijkstra_res.total_time_min, astar_res.total_time_min, places=1)
        # A* visited nodes should be <= Dijkstra visited nodes
        self.assertLessEqual(len(astar_res.visited_nodes), len(dijkstra_res.visited_nodes))

    def test_roadblock_rerouting(self):
        start = "JNC_BARAPULLAH_W"
        target = "JNC_BARAPULLAH_E"
        initial_res = dijkstra_shortest_path(self.graph, start, target, weight_mode="time")
        self.assertEqual(initial_res.path, [start, target])

        # Block the direct highway edge
        self.graph.set_roadblock(start, target, blocked=True)

        detour_res = dijkstra_shortest_path(self.graph, start, target, weight_mode="time")
        self.assertTrue(detour_res.success)
        # Ensure it does NOT use the direct edge
        self.assertNotEqual(detour_res.path, [start, target])
        self.assertIn(start, detour_res.path)
        self.assertIn(target, detour_res.path)

    def test_greedy_search_runs(self):
        res = greedy_best_first_search(self.graph, "ACC_CENTRAL_MKT", "HOSP_MAX")
        self.assertTrue(res.success)
        self.assertEqual(res.path[0], "ACC_CENTRAL_MKT")
        self.assertEqual(res.path[-1], "HOSP_MAX")

    def test_benchmark_engine(self):
        bench = benchmark_and_compare(self.graph, "ACC_RING_JAM", "HOSP_APOLLO")
        self.assertIn("fastest_route", bench)
        self.assertIn("shortest_route", bench)
        self.assertIn("algorithms_benchmark", bench)
        self.assertEqual(len(bench["algorithms_benchmark"]), 4)

    def test_nearest_hospital_triage(self):
        triage = find_nearest_available_hospital(self.graph, "ACC_AIRPORT_RD", require_trauma_center=True)
        self.assertIn("recommended", triage)
        self.assertIsNotNone(triage["recommended"])
        self.assertTrue(triage["recommended"]["trauma_center"])

if __name__ == "__main__":
    unittest.main()
