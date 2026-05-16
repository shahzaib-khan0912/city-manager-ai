import heapq
import math
from collections import defaultdict


def _manhattan_distance(coord1, coord2):
    #manhattan distance
    x1, y1 = coord1
    x2, y2 = coord2
    return abs(x1 - x2) + abs(y1 - y2)

def find_route(city, start_coord, goal_coord, avoid_blocked=True):
    start_node = city.get_node(start_coord)
    goal_node = city.get_node(goal_coord)
    if not start_node or not goal_node:
        return None
    if not start_node.accessible or not goal_node.accessible:
        return None
    open_set = []
    counter = 0
    heapq.heappush(open_set, (0.0, counter, start_node))
    counter += 1
    g_score = defaultdict(lambda: float('inf'))
    g_score[start_node] = 0.0
    came_from = {}
    closed = set()
    while open_set:
        f, _, current = heapq.heappop(open_set)
        if current in closed:
            continue
        if current == goal_node:
            #reconstruct path
            path = []
            node = goal_node
            while node in came_from:
                path.append((node.x, node.y))
                node = came_from[node]
            path.append((start_node.x, start_node.y))
            path.reverse()
            return path
        closed.add(current)
        current_coord = (current.x, current.y)
        for neighbor, edge in city.get_neighbors(current):
            if avoid_blocked and edge.blocked:
                continue
            edge_cost = edge.effective_cost
            tentative_g = g_score[current] + edge_cost
            if tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                neighbor_coord = (neighbor.x, neighbor.y)
                h = _manhattan_distance(neighbor_coord, goal_coord)
                f = tentative_g + h
                heapq.heappush(open_set, (f, counter, neighbor))
                counter += 1
    return None
#multi stop routing

def _find_edge_between(city, u_coord, v_coord):
    u_node = city.get_node(u_coord)
    v_node = city.get_node(v_coord)
    if not u_node or not v_node:
        return None
    for neighbor, edge in city.get_neighbors(u_node):
        if neighbor == v_node:
            return edge
    return None

def _calculate_path_cost(city, path):
    total = 0.0
    for i in range(len(path) - 1):
        edge = _find_edge_between(city, path[i], path[i + 1])
        if edge is None:
            return float('inf')
        total += edge.effective_cost
    return total

def _select_best_start(city):
    if city.ambulance_positions:
        if city.trapped_civilians:
            first_target = city.trapped_civilians[0]
            return min(city.ambulance_positions,
                       key=lambda pos: _manhattan_distance(pos, first_target))
        return city.ambulance_positions[0]
    hospitals = [
        (n.x, n.y) for n in city.get_all_nodes()
        if n.location_type == "Hospital"
    ]
    return hospitals[0] if hospitals else (7, 7)

def find_multi_stop_route(city, start_coord, waypoints):
    routes = []
    total_distance = 0.0
    blocked_count = 0
    current_pos = start_coord
    success = True
    for i, waypoint in enumerate(waypoints):
        while True:
            route = find_route(city, current_pos, waypoint)
            if route is None:
                success = False
                print(f"  Civ unreachable: {i+1} at {waypoint}")
                break
            blocked_during_route = False
            for j in range(len(route) - 1):
                u_coord = route[j]
                v_coord = route[j + 1]
                edge = _find_edge_between(city, u_coord, v_coord)
                if edge is None or edge.blocked:
                    blocked_during_route = True
                    blocked_count += 1
                    print(f"  Route blocked at {u_coord}->{v_coord}. Recalculating...")
                    break
            if blocked_during_route:
                continue
            routes.append(route)
            segment_cost = _calculate_path_cost(city, route)
            total_distance += segment_cost
            current_pos = waypoint
            print(f"  Civ {i+1} — distance: {segment_cost:.2f}")
            break
    return {
        'success': success,
        'routes': routes,
        'total_distance': total_distance,
        'blocked_count': blocked_count,
        'waypoints_reached': len(routes)
    }
#setup evaluation

def random_place_civilians(city, num_civilians=5):
    import random

    excluded = set()
    if hasattr(city, 'ambulance_positions') and city.ambulance_positions:
        excluded.update(city.ambulance_positions)
    for coord, node in city.nodes.items():
        if node.location_type == "Hospital":
            excluded.add(coord)
    civilian_candidates = [
        (node.x, node.y)
        for node in city.nodes.values()
        if node.location_type is not None
        and (node.x, node.y) not in excluded
        and node.accessible
    ]
    num_to_place = min(num_civilians, len(civilian_candidates))
    placed = random.sample(civilian_candidates, num_to_place)
    city.trapped_civilians = placed
    print(f"Randomly placed {len(placed)} trapped civilians at {placed}")
    return placed

def add_trapped_civilians(city, coords):
    city.trapped_civilians = list(coords)
    print(f"Added {len(coords)} trapped civilians at {coords}")

def evaluate_routing(city):
    if not city.trapped_civilians:
        print("No trapped civilians to rescue")
        return None
    start = _select_best_start(city)
    print(f"\nRouting from {start}")
    print(f"Must visit {len(city.trapped_civilians)} trapped civilians")
    waypoints = list(city.trapped_civilians)
    #1 nearest hospital
    last_civ = waypoints[-1]
    hospitals = [
        (n.x, n.y) for n in city.get_all_nodes()
        if n.location_type == "Hospital"
    ]
    if hospitals:
        nearest_hospital = min(hospitals, key=lambda h: _manhattan_distance(last_civ, h))
        waypoints.append(nearest_hospital)
        print(f"To hospital: {nearest_hospital}")
    #2 return to
    waypoints.append(start)
    print(f"To base: {start}")
    result = find_multi_stop_route(city, start, waypoints)
    city.routing_result = result
    if result['success']:
        print("Rescue Success")
        print(f"Distance: {result['total_distance']:.2f}")
    else:
        print(f"PARTIAL: Reached {result['waypoints_reached']}/{len(waypoints)} stops")
    return result

def handle_flood_event(city, blocked_edges):
    for (u_coord, v_coord) in blocked_edges:
        city.block_edge(u_coord, v_coord)
    summary = {
        'flooded_edges': len(blocked_edges),
        'rerouted': False,
        'routing_result': None,
    }
    if getattr(city, 'routing_result', None) and city.trapped_civilians:
        print("Flood detected during active mission. Recalculating route...")
        summary['rerouted'] = True
        summary['routing_result'] = evaluate_routing(city)
        return summary
    return summary
