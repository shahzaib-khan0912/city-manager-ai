#flood simulation
import random

def trigger_flood(city, spread_steps=3, block_chance=0.75):
    #trigger flood event
    #step 1
    flooded = set(city.river_nodes)
    #pick river
    current = random.choice(city.river_nodes)
    #expand tributary
    extension_length = random.randint(3, 5)
    for _ in range(extension_length):
        valid_neighbors = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = current[0] + dx, current[1] + dy
            if 0 <= nx < city.GRID_SIZE and 0 <= ny < city.GRID_SIZE:
                if (nx, ny) not in flooded:
                    valid_neighbors.append((nx, ny))
        if not valid_neighbors:
            break#trapped
        current = random.choice(valid_neighbors)
        flooded.add(current)
    #update river
    city.river_nodes = list(flooded)
    #step 2
    blocked_count = 0
    blocked_edges = []
    for edge in city.edges:
        u_flooded = (edge.u.x, edge.u.y) in flooded
        v_flooded = (edge.v.x, edge.v.y) in flooded
        if u_flooded or v_flooded:
            if random.random() < block_chance:
                edge.blocked = True
                blocked_count += 1
                blocked_edges.append(((edge.u.x, edge.u.y), (edge.v.x, edge.v.y)))
    #step 3
    for (fx, fy) in flooded:
        node = city.nodes.get((fx, fy))
        if node:
            node.accessible = False
    #step 4
    city.update_all_edge_costs()
    print(f"Spread {spread_steps} tiles. "
          f"Flooded tiles: {len(flooded)}. "
          f"Edges blocked: {blocked_count}.")
    return {
        "flooded_tiles": len(flooded),
        "blocked_edges": blocked_count,
        "blocked_edge_pairs": blocked_edges,
    }

def reset_flood(city):
    #reset flood effects
    #reset flood effects
    for edge in city.edges:
        edge.blocked = False
    for node in city.nodes.values():
        node.accessible = True
    city._generate_river()
    city.update_all_edge_costs()
    print("Reset complete. New river generated.")
