"""
Traffic Simulation & Dynamic Road Incident Engine
Handles scenarios such as Peak Rush Hour, Flash Floods/Monsoon, Random Accidents, and Road Closures.
"""

import random
from typing import Dict, Any, List
from .graph import RoadNetworkGraph

SCENARIOS = {
    "NORMAL": "Normal Mid-Day Traffic (Moderate Flow)",
    "RUSH_HOUR": "Peak Evening Rush Hour (Severe Congestion across main arterials)",
    "MONSOON": "Heavy Monsoon Rain (Reduced Speeds & High Delays)",
    "VIP_CLEAR": "Midnight Clear / VIP Green Corridor (Free Flow Speed)",
    "ACCIDENT_SPIKE": "Sudden Collision on Major Highway Segment"
}

def apply_traffic_scenario(graph: RoadNetworkGraph, scenario_name: str) -> Dict[str, Any]:
    scenario_name = scenario_name.upper()
    affected_edges: List[str] = []

    if scenario_name == "NORMAL":
        for u in graph.adj:
            for v, edge in graph.adj[u].items():
                if edge.status != "BLOCKED":
                    edge.traffic_factor = 1.3
                    edge.status = "OPEN"
        affected_edges.append("All roads normalized to 1.3x baseline.")

    elif scenario_name == "RUSH_HOUR":
        for u in graph.adj:
            for v, edge in graph.adj[u].items():
                if "Ring Road" in edge.road_name or "Ashram" in edge.road_name or "ITO" in edge.road_name:
                    edge.traffic_factor = round(random.uniform(3.2, 4.8), 2)
                    edge.status = "CONGESTED"
                elif "Barapullah" in edge.road_name:
                    edge.traffic_factor = 1.2  # Elevated priority remains relatively clear
                    edge.status = "EMERGENCY_LANE"
                else:
                    edge.traffic_factor = round(random.uniform(1.8, 2.6), 2)
                    edge.status = "OPEN"
        affected_edges.append("Heavy delays on Ring Road & Ashram bottlenecks.")

    elif scenario_name == "MONSOON":
        for u in graph.adj:
            for v, edge in graph.adj[u].items():
                edge.traffic_factor = round(random.uniform(2.5, 4.2), 2)
                edge.base_speed_kmh = max(20.0, edge.base_speed_kmh * 0.7)
                edge.status = "CONGESTED"
        affected_edges.append("Wet asphalt & waterlogging across all sectors; speeds dropped by 30%.")

    elif scenario_name == "VIP_CLEAR":
        for u in graph.adj:
            for v, edge in graph.adj[u].items():
                edge.traffic_factor = 1.0
                edge.status = "EMERGENCY_LANE" if "Barapullah" in edge.road_name else "OPEN"
        affected_edges.append("Traffic cleared; sirens and green wave corridor active.")

    elif scenario_name == "ACCIDENT_SPIKE":
        # Block or choke 2 random high-traffic edges
        candidate_pairs = []
        for u in graph.adj:
            for v in graph.adj[u]:
                if u < v:
                    candidate_pairs.append((u, v))
        if candidate_pairs:
            sample = random.sample(candidate_pairs, min(2, len(candidate_pairs)))
            for u, v in sample:
                edge = graph.adj[u][v]
                edge.status = "BLOCKED"
                graph.adj[v][u].status = "BLOCKED"
                affected_edges.append(f"Road closure: {edge.road_name} ({u} <-> {v})")

    return {
        "scenario": scenario_name,
        "description": SCENARIOS.get(scenario_name, "Custom scenario"),
        "notes": affected_edges
    }
