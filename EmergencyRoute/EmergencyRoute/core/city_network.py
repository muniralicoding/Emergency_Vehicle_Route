"""
City Network Definition
Defines realistic metropolitan road network with hospitals, major junctions,
expressways, arterial corridors, and accident hotspots.
"""

from .graph import RoadNetworkGraph, Node

def create_default_city_network() -> RoadNetworkGraph:
    g = RoadNetworkGraph()

    # --- 1. Nodes: Hospitals & Trauma Centers ---
    hospitals = [
        Node("HOSP_AIIMS", "AIIMS Apex Trauma Center", 28.5672, 77.2100, node_type="hospital", beds_available=14, trauma_center=True),
        Node("HOSP_SAF", "Safdarjung Emergency Hospital", 28.5700, 77.2060, node_type="hospital", beds_available=8, trauma_center=True),
        Node("HOSP_MAX", "Max Super Speciality Hospital", 28.5284, 77.2155, node_type="hospital", beds_available=5, trauma_center=False),
        Node("HOSP_APOLLO", "Indraprastha Apollo Hospital", 28.5398, 77.2831, node_type="hospital", beds_available=11, trauma_center=True),
        Node("HOSP_FORTIS", "Fortis Escorts Heart & Trauma", 28.5601, 77.2735, node_type="hospital", beds_available=7, trauma_center=False),
        Node("HOSP_LNJP", "LNJP Multi-Speciality Hospital", 28.6369, 77.2412, node_type="hospital", beds_available=9, trauma_center=True),
    ]

    # --- 2. Nodes: Intersections, Roundabouts & Hubs ---
    intersections = [
        Node("JNC_CP", "Connaught Place Central Hub", 28.6315, 77.2167, node_type="intersection"),
        Node("JNC_KAROL", "Karol Bagh Market Crossing", 28.6517, 77.1906, node_type="intersection"),
        Node("JNC_DHAULA", "Dhaula Kuan High-Speed Flyover", 28.5921, 77.1616, node_type="hub"),
        Node("JNC_RING_S", "South Extension Ring Road", 28.5724, 77.2215, node_type="intersection"),
        Node("JNC_LAJPAT", "Lajpat Nagar Flyover", 28.5702, 77.2418, node_type="intersection"),
        Node("JNC_NEHRU", "Nehru Place Commercial Hub", 28.5494, 77.2530, node_type="hub"),
        Node("JNC_SAKET", "Saket District Crossing", 28.5245, 77.2066, node_type="intersection"),
        Node("JNC_BARAPULLAH_E", "Barapullah Elevated East", 28.5830, 77.2600, node_type="hub"),
        Node("JNC_BARAPULLAH_W", "Barapullah Elevated West", 28.5780, 77.2180, node_type="hub"),
        Node("JNC_EXPR_TOLL", "Expressway Toll Plaza", 28.5520, 77.3050, node_type="hub"),
        Node("JNC_ITO", "ITO Junction (Heavy Transit)", 28.6289, 77.2411, node_type="intersection"),
        Node("JNC_AERO", "Aerocity Highway Link", 28.5535, 77.1216, node_type="hub"),
        Node("JNC_ASHRAM", "Ashram Chowk Underpass", 28.5714, 77.2590, node_type="intersection"),
    ]

    # --- 3. Nodes: Incident & Accident Hotspots ---
    incidents = [
        Node("ACC_EXPRESSWAY", "Expressway Multiple Collision Site", 28.5630, 77.3180, node_type="accident_spot"),
        Node("ACC_CENTRAL_MKT", "Karol Bagh Pedestrian Incident", 28.6480, 77.1850, node_type="accident_spot"),
        Node("ACC_RING_JAM", "Ring Road Overturn Site", 28.5740, 77.2300, node_type="accident_spot"),
        Node("ACC_AIRPORT_RD", "NH-48 Airport Highway Crash", 28.5680, 77.1350, node_type="accident_spot"),
    ]

    for n in hospitals + intersections + incidents:
        g.add_node(n)

    # --- 4. Edges: Road Segments with Realistic Distances and Speeds ---
    # distance in km, base_speed in km/h, initial traffic_factor (1.0 = clear, 1.8 = mild, 3.5 = heavy)
    edges_data = [
        # Connaught Place Connections
        ("JNC_CP", "JNC_KAROL", 3.8, 40.0, 2.8, "Pusa Road (Market Congestion)"),
        ("JNC_CP", "JNC_ITO", 2.4, 45.0, 2.5, "Vikas Marg Link"),
        ("JNC_CP", "JNC_DHAULA", 8.2, 60.0, 1.4, "Sardar Patel Marg Corridor"),
        ("JNC_CP", "HOSP_LNJP", 2.2, 35.0, 2.2, "Jawaharlal Nehru Marg"),

        # Karol Bagh Area
        ("JNC_KAROL", "ACC_CENTRAL_MKT", 1.2, 25.0, 3.8, "Arya Samaj Road"),
        ("ACC_CENTRAL_MKT", "JNC_DHAULA", 7.5, 55.0, 1.6, "Upper Ridge Road"),

        # Dhaula Kuan & Airport Belt
        ("JNC_DHAULA", "JNC_AERO", 6.0, 70.0, 1.2, "NH-48 Airport Expressway"),
        ("JNC_AERO", "ACC_AIRPORT_RD", 2.5, 75.0, 1.3, "Terminal Bypass Road"),
        ("JNC_DHAULA", "HOSP_AIIMS", 6.8, 55.0, 2.1, "Ring Road Moti Bagh Stretch"),
        ("JNC_DHAULA", "JNC_SAKET", 10.5, 60.0, 1.5, "Mehrauli-Gurgaon Link"),

        # AIIMS & Safdarjung Medical Enclave
        ("HOSP_AIIMS", "HOSP_SAF", 0.6, 30.0, 1.2, "Hospital Emergency Cross-Link"),
        ("HOSP_AIIMS", "JNC_RING_S", 1.4, 45.0, 2.6, "Ring Road South Ext Flyover"),
        ("HOSP_AIIMS", "JNC_BARAPULLAH_W", 1.8, 50.0, 1.3, "Barapullah Entry Ramp"),
        ("HOSP_SAF", "JNC_SAKET", 5.8, 50.0, 2.2, "Sri Aurobindo Marg"),

        # South Ring Road & Flyovers
        ("JNC_RING_S", "ACC_RING_JAM", 1.0, 35.0, 3.4, "Ring Road Underpass"),
        ("ACC_RING_JAM", "JNC_LAJPAT", 1.2, 40.0, 3.1, "Lajpat Ring Link"),
        ("JNC_LAJPAT", "JNC_ASHRAM", 2.1, 45.0, 3.5, "Ashram Bottleneck Stretch"),
        ("JNC_LAJPAT", "JNC_NEHRU", 3.2, 50.0, 2.0, "Lala Lajpat Rai Path"),

        # High-Speed Barapullah Elevated Corridor (Key Emergency Artery!)
        ("JNC_BARAPULLAH_W", "JNC_BARAPULLAH_E", 5.2, 75.0, 1.1, "Barapullah Elevated Emergency Expressway"),
        ("JNC_BARAPULLAH_E", "JNC_ASHRAM", 1.8, 55.0, 2.2, "Sarai Kale Khan Ramp"),
        ("JNC_BARAPULLAH_E", "JNC_ITO", 4.9, 60.0, 1.8, "Ring Road Bypass North"),

        # Ashram, Fortis & Apollo Corridor
        ("JNC_ASHRAM", "HOSP_FORTIS", 1.9, 45.0, 2.4, "Okhla Road Approach"),
        ("HOSP_FORTIS", "HOSP_APOLLO", 3.1, 55.0, 1.5, "Mathura Road Corridor"),
        ("JNC_ASHRAM", "JNC_EXPR_TOLL", 5.5, 65.0, 1.7, "DND Flyway Expressway"),

        # Expressway Toll & Incident
        ("JNC_EXPR_TOLL", "ACC_EXPRESSWAY", 2.3, 80.0, 4.2, "Expressway Incident Sector"),
        ("ACC_EXPRESSWAY", "HOSP_APOLLO", 4.2, 60.0, 2.0, "Sarita Vihar Link"),

        # Saket & Max Healthcare Area
        ("JNC_SAKET", "HOSP_MAX", 1.1, 40.0, 1.3, "Press Enclave Marg"),
        ("HOSP_MAX", "JNC_NEHRU", 4.3, 50.0, 2.4, "Outer Ring Road Chirag Dilli"),
        ("JNC_NEHRU", "HOSP_FORTIS", 3.8, 50.0, 2.1, "Kalkaji Mandir Road"),

        # Central ITO & LNJP
        ("JNC_ITO", "HOSP_LNJP", 1.5, 40.0, 2.8, "Bahadur Shah Zafar Marg"),
    ]

    for u, v, dist, speed, traffic, r_name in edges_data:
        g.add_edge(u, v, distance_km=dist, base_speed_kmh=speed, traffic_factor=traffic, road_name=r_name)

    # Mark Barapullah Elevated as designated Emergency Corridor
    g.set_emergency_lane("JNC_BARAPULLAH_W", "JNC_BARAPULLAH_E", enabled=True)

    return g
