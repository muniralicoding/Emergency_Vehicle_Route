"""
Graph Data Structure & Road Network Modeling
Models intersections as vertices and road segments as weighted directed/undirected edges.
"""

from typing import Dict, List, Optional, Tuple, Any
import math

class Node:
    def __init__(
        self,
        node_id: str,
        name: str,
        lat: float,
        lon: float,
        node_type: str = "intersection",
        beds_available: Optional[int] = None,
        trauma_center: bool = False
    ):
        self.id = node_id
        self.name = name
        self.lat = lat
        self.lon = lon
        self.node_type = node_type  # 'hospital', 'accident_spot', 'intersection', 'hub'
        self.beds_available = beds_available
        self.trauma_center = trauma_center

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "lat": self.lat,
            "lon": self.lon,
            "node_type": self.node_type,
            "beds_available": self.beds_available,
            "trauma_center": self.trauma_center
        }


class Edge:
    def __init__(
        self,
        u: str,
        v: str,
        distance_km: float,
        base_speed_kmh: float = 50.0,
        traffic_factor: float = 1.0,
        road_name: str = "",
        status: str = "OPEN"  # 'OPEN', 'CONGESTED', 'BLOCKED', 'EMERGENCY_LANE'
    ):
        self.u = u
        self.v = v
        self.distance_km = distance_km
        self.base_speed_kmh = max(base_speed_kmh, 5.0)
        self.traffic_factor = max(traffic_factor, 1.0)  # 1.0 = Free flow, 2.5 = Dense, 5.0 = Gridlock
        self.road_name = road_name or f"{u} <-> {v}"
        self.status = status

    @property
    def effective_speed_kmh(self) -> float:
        if self.status == "BLOCKED":
            return 0.0001
        if self.status == "EMERGENCY_LANE":
            # Emergency lane bypasses general congestion
            return self.base_speed_kmh * 1.1
        return max(self.base_speed_kmh / self.traffic_factor, 5.0)

    @property
    def travel_time_minutes(self) -> float:
        """Effective travel time in minutes based on distance, speed, and live congestion."""
        if self.status == "BLOCKED":
            return float('inf')
        hours = self.distance_km / self.effective_speed_kmh
        return hours * 60.0

    @property
    def free_flow_time_minutes(self) -> float:
        """Ideal travel time with zero traffic."""
        hours = self.distance_km / self.base_speed_kmh
        return hours * 60.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "u": self.u,
            "v": self.v,
            "road_name": self.road_name,
            "distance_km": round(self.distance_km, 2),
            "base_speed_kmh": self.base_speed_kmh,
            "traffic_factor": round(self.traffic_factor, 2),
            "status": self.status,
            "effective_speed_kmh": round(self.effective_speed_kmh, 1),
            "travel_time_minutes": round(self.travel_time_minutes, 2) if self.status != "BLOCKED" else None,
            "free_flow_time_minutes": round(self.free_flow_time_minutes, 2)
        }


class RoadNetworkGraph:
    """Graph representation of the city road network with dynamic weights."""

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        # Adjacency list: node_id -> dict of {neighbor_id: Edge}
        self.adj: Dict[str, Dict[str, Edge]] = {}

    def add_node(self, node: Node) -> None:
        self.nodes[node.id] = node
        if node.id not in self.adj:
            self.adj[node.id] = {}

    def add_edge(
        self,
        u: str,
        v: str,
        distance_km: float,
        base_speed_kmh: float = 50.0,
        traffic_factor: float = 1.0,
        road_name: str = "",
        status: str = "OPEN",
        bidirectional: bool = True
    ) -> None:
        if u not in self.nodes or v not in self.nodes:
            raise ValueError(f"Both nodes {u} and {v} must be present in the graph.")

        edge_uv = Edge(u, v, distance_km, base_speed_kmh, traffic_factor, road_name, status)
        self.adj[u][v] = edge_uv

        if bidirectional:
            edge_vu = Edge(v, u, distance_km, base_speed_kmh, traffic_factor, road_name, status)
            self.adj[v][u] = edge_vu

    def get_edge(self, u: str, v: str) -> Optional[Edge]:
        return self.adj.get(u, {}).get(v)

    def set_traffic_factor(self, u: str, v: str, factor: float, bidirectional: bool = True) -> None:
        if u in self.adj and v in self.adj[u]:
            self.adj[u][v].traffic_factor = max(1.0, factor)
            if factor > 3.0:
                self.adj[u][v].status = "CONGESTED"
            elif self.adj[u][v].status == "CONGESTED":
                self.adj[u][v].status = "OPEN"

        if bidirectional and v in self.adj and u in self.adj[v]:
            self.adj[v][u].traffic_factor = max(1.0, factor)
            if factor > 3.0:
                self.adj[v][u].status = "CONGESTED"
            elif self.adj[v][u].status == "CONGESTED":
                self.adj[v][u].status = "OPEN"

    def set_roadblock(self, u: str, v: str, blocked: bool = True, bidirectional: bool = True) -> None:
        status = "BLOCKED" if blocked else "OPEN"
        if u in self.adj and v in self.adj[u]:
            self.adj[u][v].status = status
        if bidirectional and v in self.adj and u in self.adj[v]:
            self.adj[v][u].status = status

    def set_emergency_lane(self, u: str, v: str, enabled: bool = True, bidirectional: bool = True) -> None:
        status = "EMERGENCY_LANE" if enabled else "OPEN"
        if u in self.adj and v in self.adj[u]:
            self.adj[u][v].status = status
        if bidirectional and v in self.adj and u in self.adj[v]:
            self.adj[v][u].status = status

    def haversine_distance(self, u_id: str, v_id: str) -> float:
        """Great circle distance in kilometers between two nodes."""
        node_u = self.nodes[u_id]
        node_v = self.nodes[v_id]
        R = 6371.0  # Earth radius in km

        lat1 = math.radians(node_u.lat)
        lon1 = math.radians(node_u.lon)
        lat2 = math.radians(node_v.lat)
        lon2 = math.radians(node_v.lon)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def to_dict(self) -> Dict[str, Any]:
        """Export serialized graph for UI / Map rendering."""
        edges_list = []
        seen = set()
        for u in self.adj:
            for v, edge in self.adj[u].items():
                pair_key = tuple(sorted([u, v]))
                if pair_key not in seen:
                    seen.add(pair_key)
                    edges_list.append(edge.to_dict())

        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": edges_list
        }
