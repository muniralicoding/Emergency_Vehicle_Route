# 🚑 EmergencyRoute — Emergency Vehicle Route Optimizer

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://python.org)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.1-black.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Map](https://img.shields.io/badge/Geospatial-Leaflet.js-green.svg?logo=leaflet&logoColor=white)](https://leafletjs.com/)
[![DAA](https://img.shields.io/badge/DAA-Dijkstra%20%7C%20A*%20%7C%20Greedy-orange.svg)](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
[![Tests](https://img.shields.io/badge/Tests-11%20Passed-brightgreen.svg)](tests/)

> **Emergency medical response system that calculates the fastest available hospital corridor using graph algorithms, live traffic density factors, dynamic roadblock re-routing, and hospital ICU bed triage.**

---

## 📌 Problem: The "Golden Hour" Emergency Challenge

In emergency medical services (EMS), the first **60 minutes** following traumatic injury or acute cardiac arrest is known as the **Golden Hour**. Every minute of transit delay increases patient mortality by **7% to 10%**.

Standard consumer GPS navigation engines optimize for passenger convenience and general traffic throughput, often routing drivers through congested arterials or ignoring:
1. **Dynamic Congestion Spikes**: Live bottlenecks that trap emergency vehicles.
2. **Dedicated Emergency Priority Corridors**: High-speed bypass flyovers and green wave corridors.
3. **Dynamic Road Closures / Accidents**: Inability to instantly re-calculate backup detours with low latency.
4. **Hospital Capacity Matching**: Routing an ambulance to a hospital that has zero available ICU beds or lacks trauma capabilities.

---

## 💡 Solution: How EmergencyRoute Solves This

`EmergencyRoute` models metropolitan road networks as weighted directed/undirected graphs $G = (V, E)$, dynamically updating edge weights according to live road conditions:

$$\text{Effective Speed: } v_{\text{eff}}(u, v) = \frac{v_{\text{base}}(u, v)}{\tau(u, v)}$$

$$\text{Dynamic Travel Weight (Minutes): } W(u, v) = \begin{cases} 
\frac{d(u, v)}{v_{\text{eff}}(u, v)} \times 60 & \text{if status} \neq \text{BLOCKED} \\ 
\infty & \text{if status} = \text{BLOCKED} 
\end{cases}$$

where:
* $d(u, v)$: Physical distance in kilometers.
* $v_{\text{base}}(u, v)$: Base speed limit (km/h).
* $\tau(u, v)$: Congestion multiplier ($\ge 1.0$, where $1.0 = \text{clear}$, $2.5 = \text{dense}$, $4.5+ = \text{gridlock}$).

---

## 🧠 DAA (Design and Analysis of Algorithms) Core

The project implements and empirically benchmarks three foundational graph algorithms:

| Algorithm | Optimality Guarantee | Time Complexity | Space Complexity | Real-World Role |
| :--- | :---: | :---: | :---: | :--- |
| **Dijkstra's Algorithm** | **Globally Optimal** | $O((|V| + |E|) \log |V|)$ | $O(\|V\|)$ | Primary engine: Guarantees absolute fastest path under dynamic time weights. |
| **A\* Search Algorithm** | **Globally Optimal** *(admissible)* | $O(\|E\|)$ best, $O(\|V\| \log \|V\|)$ avg | $O(\|V\|)$ | Directionally prunes search space towards hospital using Haversine heuristic. |
| **Greedy Best-First** | **Suboptimal** | $O(\|V\| \log \|V\|)$ worst | $O(\|V\|)$ | Educational comparison: Demonstrates how greedy choices get stuck in dead-ends/traffic. |
| **Naive Shortest Path** | **Distance-Optimal Only** | $O((|V| + |E|) \log |V|)$ | $O(\|V\|)$ | Baseline comparison: Computes shortest distance in km, highlighting minutes lost to traffic. |

### Admissible Heuristic Formulation for A*
To guarantee mathematical optimality, the heuristic $h(n)$ must never overestimate the true remaining cost $h^*(n)$:

$$h(n) = \frac{\text{HaversineDistance}(n, \text{Target})}{v_{\text{max\_network}}} \times 60 \text{ (minutes)}$$

Since straight-line distance is always $\le$ actual road distance, and $v_{\text{max\_network}} \ge$ any actual road speed limit, $h(n) \le h^*(n)$ is strictly satisfied.

---

## ✨ Key Features & GitHub Highlights

* 🗺️ **Interactive Geospatial Control Center**: Full Leaflet.js map with CartoDB Dark Matter tiles and custom glowing SVG beacons.
* 🚦 **Interactive Roadblock & Traffic Controls**: Click any road on the map to toggle roadblocks or adjust congestion sliders with instant path recalculation.
* 🚑 **Animated Ambulance Simulation**: Watch the ambulance navigate turn-by-turn along the chosen route in real time.
* 🔊 **Web Audio Synthesizer**: Native two-tone emergency siren sound generator (no external audio files required, toggleable with mute).
* 🏥 **Nearest Hospital Auto-Triage**: Evaluates all hospitals in the city, cross-referencing live travel ETA and available ICU/trauma beds.
* 🌦️ **Preset Weather & Traffic Scenarios**:
  * Normal Mid-Day Flow
  * Peak Evening Rush Hour
  * Monsoon Floods (wet roads, speed drops)
  * VIP Green Wave Corridor
  * Sudden Highway Collision Surge
* 📊 **Live Performance Analytics**: Interactive Chart.js graphs comparing travel time and explored search frontier nodes.

---

## 📁 Project Architecture

```
EmergencyRoute/
├── app.py                     # Flask web server & REST API endpoints
├── run.py                     # Convenience launcher script (auto-opens browser)
├── requirements.txt           # Minimal dependencies (Flask)
├── core/
│   ├── __init__.py
│   ├── graph.py               # Node, Edge & RoadNetworkGraph classes
│   ├── city_network.py        # Realistic metropolitan road graph (|V|=23, |E|=54)
│   └── simulation.py          # Real-world traffic scenarios & incident triggers
├── algorithms/
│   ├── __init__.py
│   ├── dijkstra.py            # Min-Heap Priority Queue Dijkstra implementation
│   ├── a_star.py              # A* search with admissible Haversine heuristic
│   ├── greedy.py              # Greedy Best-First Search
│   └── comparison.py          # Benchmark engine, alternative backup routes & triage
├── static/
│   ├── css/
│   │   └── style.css          # Dark operations center UI styling & pulse animations
│   └── js/
│       ├── map.js             # Leaflet.js map controller & layer manager
│       ├── simulation.js      # Ambulance movement animation & Web Audio siren
│       └── charts.js          # Chart.js travel time & node exploration charts
├── templates/
│   └── index.html             # Command Center Dashboard
├── tests/
│   ├── __init__.py
│   ├── test_algorithms.py     # Unit tests verifying Dijkstra, A*, Greedy, and detours
│   └── test_api.py            # Flask REST API integration tests
└── README.md                  # Comprehensive Documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
* Python 3.9+ (tested on Python 3.11)
* Modern web browser (Chrome, Edge, Firefox, Brave)

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/your-username/EmergencyRoute.git
cd EmergencyRoute

# Install dependencies (only lightweight Flask required)
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python run.py
```
Open **`http://127.0.0.1:5000`** in your browser.

### 4. Run the Test Suite
```bash
python -m unittest discover -s tests -p "test_*.py"
```
*(All 11 unit and API integration tests execute in < 50ms).*

---

## 🔌 REST API Reference

| Endpoint | Method | Description | Payload Example |
| :--- | :---: | :--- | :--- |
| `/api/network` | `GET` | Fetches full graph nodes and road edges with live congestion | None |
| `/api/optimize` | `POST` | Computes fastest route, benchmarks all algorithms | `{"start_id": "ACC_EXPRESSWAY", "target_id": "HOSP_AIIMS"}` |
| `/api/nearest-hospital`| `POST` | Evaluates closest hospital with available ICU beds | `{"accident_id": "ACC_AIRPORT_RD", "require_trauma": true}` |
| `/api/toggle-roadblock` | `POST` | Blocks or unblocks a road segment | `{"u": "JNC_CP", "v": "JNC_KAROL", "blocked": true}` |
| `/api/update-traffic` | `POST` | Sets custom traffic multiplier on an edge | `{"u": "JNC_ASHRAM", "v": "JNC_LAJPAT", "traffic_factor": 4.5}` |
| `/api/traffic-scenario`| `POST` | Applies traffic preset (RUSH_HOUR, MONSOON, etc.) | `{"scenario": "RUSH_HOUR"}` |
| `/api/reset` | `POST` | Restores network to baseline state | None |

---

## 📊 Sample DAA Comparative Output

| Algorithm | Path Time | Path Distance | Visited Vertices | Execution Time | Optimal? |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Dijkstra (Traffic-Aware)** | **7.84 min** | 9.4 km | 18 | 0.042 ms | ✅ Yes |
| **A\* Search (Heuristic)** | **7.84 min** | 9.4 km | 11 | 0.035 ms | ✅ Yes |
| **Dijkstra (Distance Only)** | 14.20 min | **6.8 km** | 18 | 0.038 ms | ❌ No (Stuck in Jam) |
| **Greedy Best-First** | 11.50 min | 8.2 km | 8 | 0.021 ms | ❌ No |

*Result: The traffic-aware route saves **6.36 minutes** by bypassing the jammed downtown core via the elevated emergency bypass, easily saving a critical life during the Golden Hour.*

---

## 📜 License
MIT License. Open-source for academic, portfolio, and research use.
