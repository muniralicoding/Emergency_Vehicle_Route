"""
Greedy Best-First Search Implementation
Selects next node strictly minimizing heuristic distance h(n) to target.
DAA Role: Highlights the trade-off of greedy local optimization vs optimal dynamic programming/Dijkstra.
"""

import heapq
import time
from typing import Dict, List, Tuple, Optional, Any
from core.graph import RoadNetworkGraph
from .dijkstra import RouteResult

def greedy_best_first_search(
    graph: RoadNetworkGraph,
    start_id: str,
    target_id: str
) -> RouteResult:
    """
    Greedy Best-First Search:
    Priority Queue ordered purely by heuristic h(n) = haversine distance to target.
    """
    start_perf = time.perf_counter()

    if start_id not in graph.nodes or target_id not in graph.nodes:
        return RouteResult(
            algorithm="Greedy Best-First",
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
            algorithm="Greedy Best-First",
            path=[start_id],
            total_time_min=0.0,
            total_distance_km=0.0,
            visited_nodes=[start_id],
            relaxations_count=0,
            execution_time_ms=0.0,
            success=True
        )

    def heuristic(node_id: str) -> float:
        return graph.haversine_distance(node_id, target_id)

    # Priority queue stores: (h(n), node_id)
    pq: List[Tuple[float, str]] = [(heuristic(start_id), start_id)]
    predecessor: Dict[str, Optional[str]] = {node_id: None for node_id in graph.nodes}
    visited_set = set()
    visited_order: List[str] = []
    relaxations = 0

    target_reached = False

    while pq:
        h_val, u = heapq.heappop(pq)

        if u in visited_set:
            continue
        visited_set.add(u)
        visited_order.append(u)

        if u == target_id:
            target_reached = True
            break

        for v, edge in graph.adj[u].items():
            if edge.status == "BLOCKED":
                continue
            if v not in visited_set:
                relaxations += 1
                if predecessor[v] is None and v != start_id:
                    predecessor[v] = u
                heapq.heappush(pq, (heuristic(v), v))

    end_perf = time.perf_counter()
    exec_ms = (end_perf - start_perf) * 1000.0

    if not target_reached:
        return RouteResult(
            algorithm="Greedy Best-First",
            path=[],
            total_time_min=float('inf'),
            total_distance_km=0.0,
            visited_nodes=visited_order,
            relaxations_count=relaxations,
            execution_time_ms=exec_ms,
            success=False,
            error_message="Greedy search got stuck in a local minimum or dead-end."
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
        e = graph.adj[u_p].get(v_p)
        if e:
            total_time += e.travel_time_minutes
            total_dist += e.distance_km

    return RouteResult(
        algorithm="Greedy Best-First",
        path=path,
        total_time_min=total_time,
        total_distance_km=total_dist,
        visited_nodes=visited_order,
        relaxations_count=relaxations,
        execution_time_ms=exec_ms,
        success=True
    )
