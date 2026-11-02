"""
A* Search Algorithm Implementation
Combines actual cost g(n) with an admissible heuristic h(n) toward the target hospital.
Heuristic: Haversine distance divided by maximum network speed (strictly admissible).
"""

import heapq
import time
from typing import Dict, List, Tuple, Optional, Any
from core.graph import RoadNetworkGraph
from .dijkstra import RouteResult

def get_max_network_speed(graph: RoadNetworkGraph) -> float:
    max_s = 50.0
    for u in graph.adj:
        for v, edge in graph.adj[u].items():
            if edge.base_speed_kmh > max_s:
                max_s = edge.base_speed_kmh
    return max_s

def a_star_search(
    graph: RoadNetworkGraph,
    start_id: str,
    target_id: str,
    weight_mode: str = "time"
) -> RouteResult:
    """
    Computes optimal route using A* search.
    - f(n) = g(n) + h(n)
    - Admissible heuristic guarantees optimality while minimizing search frontier.
    """
    start_perf = time.perf_counter()

    if start_id not in graph.nodes or target_id not in graph.nodes:
        return RouteResult(
            algorithm="A* Search",
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
            algorithm="A* Search",
            path=[start_id],
            total_time_min=0.0,
            total_distance_km=0.0,
            visited_nodes=[start_id],
            relaxations_count=0,
            execution_time_ms=0.0,
            success=True
        )

    max_speed = get_max_network_speed(graph)

    def heuristic(node_id: str) -> float:
        straight_dist = graph.haversine_distance(node_id, target_id)
        if weight_mode == "time":
            # Time in minutes at maximum possible network velocity
            return (straight_dist / max_speed) * 60.0
        return straight_dist

    g_score: Dict[str, float] = {node_id: float('inf') for node_id in graph.nodes}
    f_score: Dict[str, float] = {node_id: float('inf') for node_id in graph.nodes}
    predecessor: Dict[str, Optional[str]] = {node_id: None for node_id in graph.nodes}

    g_score[start_id] = 0.0
    f_score[start_id] = heuristic(start_id)

    # Priority queue stores (f_score, g_score, node_id)
    pq: List[Tuple[float, float, str]] = [(f_score[start_id], 0.0, start_id)]
    visited_order: List[str] = []
    visited_set = set()
    relaxations = 0

    while pq:
        curr_f, curr_g, u = heapq.heappop(pq)

        if u in visited_set:
            continue
        visited_set.add(u)
        visited_order.append(u)

        if u == target_id:
            break

        if curr_g > g_score[u]:
            continue

        for v, edge in graph.adj[u].items():
            if edge.status == "BLOCKED":
                continue

            weight = edge.travel_time_minutes if weight_mode == "time" else edge.distance_km
            if weight == float('inf'):
                continue

            relaxations += 1
            tentative_g = curr_g + weight

            if tentative_g < g_score[v]:
                predecessor[v] = u
                g_score[v] = tentative_g
                f_score[v] = tentative_g + heuristic(v)
                heapq.heappush(pq, (f_score[v], tentative_g, v))

    end_perf = time.perf_counter()
    exec_ms = (end_perf - start_perf) * 1000.0

    if g_score[target_id] == float('inf'):
        return RouteResult(
            algorithm="A* Search",
            path=[],
            total_time_min=float('inf'),
            total_distance_km=0.0,
            visited_nodes=visited_order,
            relaxations_count=relaxations,
            execution_time_ms=exec_ms,
            success=False,
            error_message="No viable path to hospital found using A*."
        )

    # Reconstruct path
    path = []
    curr = target_id
    while curr is not None:
        path.append(curr)
        curr = predecessor[curr]
    path.reverse()

    total_time = 0.0
    total_dist = 0.0
    for i in range(len(path) - 1):
        u_p = path[i]
        v_p = path[i + 1]
        e = graph.adj[u_p][v_p]
        total_time += e.travel_time_minutes
        total_dist += e.distance_km

    return RouteResult(
        algorithm="A* Search",
        path=path,
        total_time_min=total_time,
        total_distance_km=total_dist,
        visited_nodes=visited_order,
        relaxations_count=relaxations,
        execution_time_ms=exec_ms,
        success=True
    )
