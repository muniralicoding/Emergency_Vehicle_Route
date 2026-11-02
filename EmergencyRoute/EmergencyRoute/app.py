"""
EmergencyRoute — Flask Application Server & REST API
Emergency Vehicle Route Optimizer with Graph Algorithms & Live Traffic Simulation
"""

from flask import Flask, render_template, jsonify, request
from core.city_network import create_default_city_network
from core.simulation import apply_traffic_scenario, SCENARIOS
from algorithms.comparison import benchmark_and_compare, find_nearest_available_hospital

app = Flask(__name__)

# Maintain current in-memory network graph
network = create_default_city_network()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/network", methods=["GET"])
def get_network():
    """Returns current state of nodes and road segments."""
    return jsonify({
        "status": "success",
        "graph": network.to_dict(),
        "scenarios": SCENARIOS
    })

@app.route("/api/optimize", methods=["POST"])
def optimize_route():
    """Calculates fastest route and benchmarks DAA algorithms."""
    data = request.get_json() or {}
    start_id = data.get("start_id")
    target_id = data.get("target_id")

    if not start_id or not target_id:
        return jsonify({"status": "error", "message": "start_id and target_id are required."}), 400

    if start_id not in network.nodes:
        return jsonify({"status": "error", "message": f"Start node '{start_id}' not found."}), 404

    if target_id not in network.nodes:
        return jsonify({"status": "error", "message": f"Target node '{target_id}' not found."}), 404

    results = benchmark_and_compare(network, start_id, target_id)
    return jsonify({"status": "success", "data": results})

@app.route("/api/nearest-hospital", methods=["POST"])
def dispatch_nearest_hospital():
    """Finds and ranks all hospitals based on live travel ETA and bed capacity."""
    data = request.get_json() or {}
    accident_id = data.get("accident_id")
    require_trauma = data.get("require_trauma", False)

    if not accident_id or accident_id not in network.nodes:
        return jsonify({"status": "error", "message": "Valid accident_id is required."}), 400

    results = find_nearest_available_hospital(network, accident_id, require_trauma)
    return jsonify({"status": "success", "data": results})

@app.route("/api/toggle-roadblock", methods=["POST"])
def toggle_roadblock():
    """Blocks or unblocks a road edge."""
    data = request.get_json() or {}
    u = data.get("u")
    v = data.get("v")
    blocked = data.get("blocked", True)

    if not u or not v:
        return jsonify({"status": "error", "message": "Both node endpoints 'u' and 'v' are required."}), 400

    edge = network.get_edge(u, v)
    if not edge:
        return jsonify({"status": "error", "message": f"Road segment between {u} and {v} not found."}), 404

    network.set_roadblock(u, v, blocked=blocked)
    return jsonify({
        "status": "success",
        "u": u,
        "v": v,
        "road_name": edge.road_name,
        "new_status": network.get_edge(u, v).status
    })

@app.route("/api/update-traffic", methods=["POST"])
def update_traffic():
    """Sets a custom traffic congestion multiplier on a road segment."""
    data = request.get_json() or {}
    u = data.get("u")
    v = data.get("v")
    factor = float(data.get("traffic_factor", 1.0))

    if not u or not v:
        return jsonify({"status": "error", "message": "Nodes 'u' and 'v' are required."}), 400

    edge = network.get_edge(u, v)
    if not edge:
        return jsonify({"status": "error", "message": "Road segment not found."}), 404

    network.set_traffic_factor(u, v, factor)
    updated_edge = network.get_edge(u, v)
    return jsonify({
        "status": "success",
        "u": u,
        "v": v,
        "traffic_factor": updated_edge.traffic_factor,
        "status_label": updated_edge.status,
        "travel_time_minutes": round(updated_edge.travel_time_minutes, 2)
    })

@app.route("/api/traffic-scenario", methods=["POST"])
def set_scenario():
    """Applies traffic scenarios: RUSH_HOUR, MONSOON, VIP_CLEAR, NORMAL, ACCIDENT_SPIKE."""
    data = request.get_json() or {}
    scenario = data.get("scenario", "NORMAL")

    res = apply_traffic_scenario(network, scenario)
    return jsonify({
        "status": "success",
        "scenario": res,
        "graph": network.to_dict()
    })

@app.route("/api/reset", methods=["POST"])
def reset_network():
    """Resets network graph to baseline configuration."""
    global network
    network = create_default_city_network()
    return jsonify({"status": "success", "message": "Network reset to initial state.", "graph": network.to_dict()})

if __name__ == "__main__":
    print("=" * 65)
    print("🚑 EmergencyRoute — Emergency Vehicle Route Optimizer")
    print("🌐 Server starting at http://127.0.0.1:5000")
    print("=" * 65)
    app.run(host="0.0.0.0", port=5000, debug=True)
