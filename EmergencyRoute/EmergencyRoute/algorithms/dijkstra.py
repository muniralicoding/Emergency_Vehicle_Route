"""
Dijkstra's Algorithm Implementation
Uses a Min-Priority Queue (heapq) to compute single-source shortest/fastest paths.
Guarantees global optimality on graphs with non-negative edge weights.
"""

import heapq
import time
from typing import Dict, List, Tuple, Optional, Any
from core.graph import RoadNetworkGraph

class RouteResult:
    def __init__(
        self,
        algorithm: str,
        path: List[str],
        total_time_min: float,
        total_distance_km: float,
        visited_nodes: List[str],
        relaxations_count: int,
        execution_time_ms: float,
        success: bool = True,
        error_message: str = ""
    ):
        self.algorithm = algorithm
        self.path = path
        self.total_time_min = round(total_time_min, 2) if total_time_min != float('inf') else None
        self.total_distance_km = round(total_distance_km, 2)
        self.visited_nodes = visited_nodes
        self.relaxations_count = relaxations_count
        self.execution_time_ms = round(execution_time_ms, 3)
        self.success = success
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "path": self.path,
            "total_time_min": self.total_time_min,
            "total_distance_km": self.total_distance_km,
            "visited_nodes": self.visited_nodes,
            "visited_count": len(self.visited_nodes),
            "relaxations_count": self.relaxations_count,
            "execution_time_ms": self.execution_time_ms,
            "success": self.success,
            "error_message": self.error_message
        }


def dijkstra_shortest_path(
    graph: RoadNetworkGraph,
    start_id: str,
    target_id: str,
    weight_mode: str = "time",
    penalty_edges: Optional[Dict[Tuple[str, str], float]] = None
) -> RouteResult:
    """
    Computes shortest path using Dijkstra's Algorithm with Min-Heap.
    - weight_mode: 'time' (minimizes travel minutes considering traffic) or 'distance' (km only).
    - penalty_edges: Optional dict of {(u, v): multiplier} to find diverse alternate routes.
    """
    start_perf = time.perf_counter()

    if start_id not in graph.nodes or target_id not in graph.nodes:
        return RouteResult(
            algorithm="Dijkstra",
            path=[],
            total_time_min=float('inf'),
            total_distance_km=0.0,
            visited_nodes=[],
            relaxations_count=0,
            execution_time_ms=0.0,
            success=False,
            error_message="Start or Target node does not exist in graph."
        )

    if start_id == target_id:
        return RouteResult(
            algorithm="Dijkstra",
            path=[start_id],
            total_time_min=0.0,
            total_distance_km=0.0,
            visited_nodes=[start_id],
            relaxations_count=0,
            execution_time_ms=0.0,
            success=True
        )

    # Initialize distances and predecessors
    distances: Dict[str, float] = {node_id: float('inf') for node_id in graph.nodes}
    predecessor: Dict[str, Optional[str]] = {node_id: None for node_id in graph.nodes}
    distances[start_id] = 0.0

    # Min-Heap stores tuples: (current_cost, node_id)
    pq: List[Tuple[float, str]] = [(0.0, start_id)]
    visited_order: List[str] = []
    visited_set = set()
    relaxations = 0

    while pq:
        curr_cost, u = heapq.heappop(pq)

        if u in visited_set:
            continue
        visited_set.add(u)
        visited_order.append(u)

        if u == target_id:
            break

        if curr_cost > distances[u]:
            continue

        for v, edge in graph.adj[u].items():
            if edge.status == "BLOCKED":
                continue

            # Determine edge weight
            if weight_mode == "time":
                weight = edge.travel_time_minutes
            else:
                weight = edge.distance_km

            if weight == float('inf'):
                continue

            # Apply penalty multiplier if calculating alternate route
            if penalty_edges:
                pair = (u, v)
                rev_pair = (v, u)
                if pair in penalty_edges:
                    weight *= penalty_edges[pair]
                elif rev_pair in penalty_edges:
                    weight *= penalty_edges[rev_pair]

            relaxations += 1
            new_cost = curr_cost + weight

            if new_cost < distances[v]:
                distances[v] = new_cost
                predecessor[v] = u
                heapq.heappush(pq, (new_cost, v))

    end_perf = time.perf_counter()
    exec_ms = (end_perf - start_perf) * 1000.0

    # Reconstruct path
    if distances[target_id] == float('inf'):
        return RouteResult(
            algorithm=f"Dijkstra ({weight_mode})",
            path=[],
            total_time_min=float('inf'),
            total_distance_km=0.0,
            visited_nodes=visited_order,
            relaxations_count=relaxations,
            execution_time_ms=exec_ms,
            success=False,
            error_message="No viable path found (Destination isolated or roads blocked)."
        )

    path = []
    curr = target_id
    while curr is not None:
        path.append(curr)
        curr = predecessor[curr]
    path.reverse()

    # Calculate actual physical distance and travel time along path
    total_time = 0.0
    total_dist = 0.0
    for i in range(len(path) - 1):
        u_p = path[i]
        v_p = path[i + 1]
        e = graph.adj[u_p][v_p]
        total_time += e.travel_time_minutes
        total_dist += e.distance_km

    return RouteResult(
        algorithm=f"Dijkstra ({weight_mode})",
        path=path,
        total_time_min=total_time,
        total_distance_km=total_dist,
        visited_nodes=visited_order,
        relaxations_count=relaxations,
        execution_time_ms=exec_ms,
        success=True
    )
