"""
Multi-Route Comparison & Benchmark Engine
Analyzes algorithm performance, calculates backup routes, and provides
Intelligent Hospital Dispatch triage.
"""

from typing import Dict, List, Any, Optional
from core.graph import RoadNetworkGraph
from .dijkstra import dijkstra_shortest_path, RouteResult
from .a_star import a_star_search
from .greedy import greedy_best_first_search

def get_detailed_path_legs(graph: RoadNetworkGraph, path: List[str]) -> List[Dict[str, Any]]:
    legs = []
    for i in range(len(path) - 1):
        u = path[i]
        v = path[i + 1]
        edge = graph.adj.get(u, {}).get(v)
        node_u = graph.nodes.get(u)
        node_v = graph.nodes.get(v)

        if edge and node_u and node_v:
            legs.append({
                "from_id": u,
                "from_name": node_u.name,
                "to_id": v,
                "to_name": node_v.name,
                "road_name": edge.road_name,
                "distance_km": round(edge.distance_km, 2),
                "base_speed_kmh": edge.base_speed_kmh,
                "effective_speed_kmh": round(edge.effective_speed_kmh, 1),
                "traffic_factor": round(edge.traffic_factor, 2),
                "status": edge.status,
                "travel_time_min": round(edge.travel_time_minutes, 2)
            })
    return legs


def find_alternative_route(
    graph: RoadNetworkGraph,
    start_id: str,
    target_id: str,
    primary_path: List[str]
) -> Optional[RouteResult]:
    """Finds an alternative/backup route by penalizing primary edges."""
    if not primary_path or len(primary_path) < 2:
        return None

    # Apply heavy penalty to primary path edges
    penalties = {}
    for i in range(len(primary_path) - 1):
        u = primary_path[i]
        v = primary_path[i + 1]
        penalties[(u, v)] = 3.0
        penalties[(v, u)] = 3.0

    alt_result = dijkstra_shortest_path(
        graph,
        start_id=start_id,
        target_id=target_id,
        weight_mode="time",
        penalty_edges=penalties
    )

    if alt_result.success and alt_result.path != primary_path:
        alt_result.algorithm = "Alternative Backup Route"
        return alt_result
    return None


def benchmark_and_compare(
    graph: RoadNetworkGraph,
    start_id: str,
    target_id: str
) -> Dict[str, Any]:
    """
    Executes multiple algorithms for comprehensive DAA comparison and emergency routing.
    """
    # 1. Primary: Dijkstra Time-Optimized (Traffic-Aware)
    dijkstra_time = dijkstra_shortest_path(graph, start_id, target_id, weight_mode="time")

    # 2. Dijkstra Distance-Only (Ignores traffic congestion)
    dijkstra_dist = dijkstra_shortest_path(graph, start_id, target_id, weight_mode="distance")

    # 3. A* Search (Time-Optimized with Admissible Heuristic)
    a_star_res = a_star_search(graph, start_id, target_id, weight_mode="time")

    # 4. Greedy Best-First Search
    greedy_res = greedy_best_first_search(graph, start_id, target_id)

    # 5. Alternative Route
    alt_res = find_alternative_route(graph, start_id, target_id, dijkstra_time.path)

    # Minutes saved by being traffic-aware
    time_saved_min = 0.0
    if dijkstra_time.success and dijkstra_dist.success and dijkstra_dist.total_time_min:
        time_saved_min = max(0.0, dijkstra_dist.total_time_min - (dijkstra_time.total_time_min or 0.0))

    # Detailed path legs for the primary route
    primary_legs = get_detailed_path_legs(graph, dijkstra_time.path) if dijkstra_time.success else []

    return {
        "start_node": graph.nodes[start_id].to_dict() if start_id in graph.nodes else None,
        "target_node": graph.nodes[target_id].to_dict() if target_id in graph.nodes else None,
        "fastest_route": dijkstra_time.to_dict(),
        "shortest_route": dijkstra_dist.to_dict(),
        "a_star_route": a_star_res.to_dict(),
        "greedy_route": greedy_res.to_dict(),
        "alternative_route": alt_res.to_dict() if alt_res else None,
        "time_saved_minutes": round(time_saved_min, 2),
        "primary_legs": primary_legs,
        "algorithms_benchmark": [
            {
                "name": "Dijkstra (Traffic Time)",
                "optimal": True,
                "time_min": dijkstra_time.total_time_min,
                "distance_km": dijkstra_time.total_distance_km,
                "visited_nodes": len(dijkstra_time.visited_nodes),
                "relaxations": dijkstra_time.relaxations_count,
                "exec_time_ms": dijkstra_time.execution_time_ms,
                "complexity": "O((V + E) log V)"
            },
            {
                "name": "A* Search (Heuristic)",
                "optimal": True,
                "time_min": a_star_res.total_time_min,
                "distance_km": a_star_res.total_distance_km,
                "visited_nodes": len(a_star_res.visited_nodes),
                "relaxations": a_star_res.relaxations_count,
                "exec_time_ms": a_star_res.execution_time_ms,
                "complexity": "O(E) best, O(V log V) avg"
            },
            {
                "name": "Dijkstra (Distance Only)",
                "optimal": False,  # Distance-optimal, but time-suboptimal under traffic
                "time_min": dijkstra_dist.total_time_min,
                "distance_km": dijkstra_dist.total_distance_km,
                "visited_nodes": len(dijkstra_dist.visited_nodes),
                "relaxations": dijkstra_dist.relaxations_count,
                "exec_time_ms": dijkstra_dist.execution_time_ms,
                "complexity": "O((V + E) log V)"
            },
            {
                "name": "Greedy Best-First",
                "optimal": False,
                "time_min": greedy_res.total_time_min,
                "distance_km": greedy_res.total_distance_km,
                "visited_nodes": len(greedy_res.visited_nodes),
                "relaxations": greedy_res.relaxations_count,
                "exec_time_ms": greedy_res.execution_time_ms,
                "complexity": "O(V log V) worst-case"
            }
        ]
    }


def find_nearest_available_hospital(
    graph: RoadNetworkGraph,
    accident_node_id: str,
    require_trauma_center: bool = False
) -> Dict[str, Any]:
    """
    Evaluates all hospitals in the network and ranks them by real-time travel ETA
    and available ICU/Emergency beds.
    """
    if accident_node_id not in graph.nodes:
        return {"error": f"Accident node {accident_node_id} not found."}

    results = []
    for node_id, node in graph.nodes.items():
        if node.node_type == "hospital":
            if require_trauma_center and not node.trauma_center:
                continue

            route = dijkstra_shortest_path(graph, accident_node_id, node_id, weight_mode="time")
            if route.success and route.total_time_min is not None:
                results.append({
                    "hospital": node.to_dict(),
                    "travel_time_min": route.total_time_min,
                    "distance_km": route.total_distance_km,
                    "path": route.path,
                    "beds_available": node.beds_available or 0,
                    "trauma_center": node.trauma_center
                })

    # Sort primarily by lowest travel time, tiebreak by bed availability
    results.sort(key=lambda x: (x["travel_time_min"], -(x["beds_available"])))

    return {
        "accident_location": graph.nodes[accident_node_id].to_dict(),
        "ranked_hospitals": results,
        "recommended": results[0] if results else None
    }
