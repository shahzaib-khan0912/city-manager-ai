import random
from collections import deque

DEFAULT_COUNTS = {
    "Hospital":       9,
    "Industrial":     10,
    "School":         15,
    "PowerPlant":     10,
    "Residential":   80,
    "AmbulanceDepot": 1,
}
#all valid building
ALL_TYPES = ["Hospital", "Industrial", "School", "PowerPlant",
             "Residential", "AmbulanceDepot"]
#bfs utility

def _bfs_distances(city, start_coord):
    #bfs from start
    start_node = city.nodes.get(start_coord)
    if not start_node:
        return {}
    dist = {start_coord: 0}
    queue = deque([start_node])
    while queue:
        node = queue.popleft()
        curr_coord = (node.x, node.y)
        for neighbor, edge in city.get_neighbors(node):
            n_coord = (neighbor.x, neighbor.y)
            if n_coord not in dist:
                dist[n_coord] = dist[curr_coord] + 1
                queue.append(neighbor)
    return dist

def _get_neighbors_4dir(x, y, grid_size=15):
    #returns valid 4
    result = []
    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < grid_size and 0 <= ny < grid_size:
            result.append((nx, ny))
    return result
#constraint checks

def _check_industrial_adjacency(city, coord, placement):
    #industrial adjacency check
    x, y = coord
    loc_type = placement.get(coord)
    if loc_type == "Industrial":
        for nx, ny in _get_neighbors_4dir(x, y, city.GRID_SIZE):
            if placement.get((nx, ny)) in ("School", "Hospital"):
                return False
    elif loc_type in ("School", "Hospital"):
        for nx, ny in _get_neighbors_4dir(x, y, city.GRID_SIZE):
            if placement.get((nx, ny)) == "Industrial":
                return False
    return True

def _check_residential_hospital_proximity(city, placement):
    #hospital proximity check
    hospitals   = [c for c, t in placement.items() if t == "Hospital"]
    residentials = [c for c, t in placement.items() if t == "Residential"]
    if not hospitals or not residentials:
        return True
    covered = set()
    for h in hospitals:
        for coord, d in _bfs_distances(city, h).items():
            if d <= 3:
                covered.add(coord)
    return all(r in covered for r in residentials)

def _check_powerplant_industrial_proximity(city, placement):
    #powerplant industrial check
    industrials = [c for c, t in placement.items() if t == "Industrial"]
    powerplants = [c for c, t in placement.items() if t == "PowerPlant"]
    if not powerplants:
        return True
    if not industrials:
        return False
    covered = set()
    for i in industrials:
        for coord, d in _bfs_distances(city, i).items():
            if d <= 2:
                covered.add(coord)
    return all(pp in covered for pp in powerplants)

def _is_placement_valid_local(city, coord, placement):
    #quick local check
    return _check_industrial_adjacency(city, coord, placement)

def _is_placement_valid_global(city, placement):
    #full global check
    return (_check_residential_hospital_proximity(city, placement) and
            _check_powerplant_industrial_proximity(city, placement))
#forward checking

def _init_domains(city, placement, available):
    #init domain dict
    return {coord: list(ALL_TYPES)
            for coord in available
            if coord not in placement}

def _forward_check(city, coord, placement, domains):
    #after placing a
    x, y = coord
    loc_type = placement[coord]
    for nx, ny in _get_neighbors_4dir(x, y, city.GRID_SIZE):
        n_coord = (nx, ny)
        #only prune unassigned
        if n_coord not in domains:
            continue
        if loc_type == "Industrial":
            domains[n_coord] = [t for t in domains[n_coord]
                                 if t not in ("School", "Hospital")]
        elif loc_type in ("School", "Hospital"):
            domains[n_coord] = [t for t in domains[n_coord]
                                 if t != "Industrial"]
        #dead end this
        if len(domains[n_coord]) == 0:
            return False
    return True
#candidate ranking

def _rank_candidates(city, building_type, placement, available):
    #returns a prioritised
    center = city.GRID_SIZE // 2
    candidates = [c for c in available if c not in placement]
    if building_type == "Hospital":
        #spread hospitals using
        seed_positions = [
            (center,     center    ),
            (center - 4, center - 4),
            (center + 4, center - 4),
            (center - 4, center + 4),
            (center + 4, center + 4),
        ]
        placed_hospitals = [c for c, t in placement.items() if t == "Hospital"]
        used_seeds = set()
        for ph in placed_hospitals:
            closest = min(seed_positions,
                          key=lambda s: abs(s[0]-ph[0]) + abs(s[1]-ph[1]))
            used_seeds.add(closest)
        remaining_seeds = [s for s in seed_positions if s not in used_seeds]
        if remaining_seeds:
            target = remaining_seeds[0]
            candidates.sort(key=lambda c: abs(c[0]-target[0]) + abs(c[1]-target[1]))
        elif placed_hospitals:
            candidates.sort(key=lambda c: -min(
                abs(c[0]-hx) + abs(c[1]-hy) for hx, hy in placed_hospitals))
    elif building_type == "Industrial":
        #prefer outskirts penalise

        def industrial_score(c):
            penalty = sum(
                10 for nx, ny in _get_neighbors_4dir(c[0], c[1], city.GRID_SIZE)
                if placement.get((nx, ny)) in ("School", "Hospital")
            )
            edge_dist = min(c[0], c[1],
                            city.GRID_SIZE-1-c[0], city.GRID_SIZE-1-c[1])
            return penalty + edge_dist
        candidates.sort(key=industrial_score)
    elif building_type == "PowerPlant":
        #pre filter must
        industrials = [c for c, t in placement.items() if t == "Industrial"]
        if industrials:
            covered = set()
            for i in industrials:
                for coord, d in _bfs_distances(city, i).items():
                    if d <= 2:
                        covered.add(coord)
            candidates = [c for c in candidates if c in covered]
            candidates.sort(key=lambda c: min(
                abs(c[0]-ix) + abs(c[1]-iy) for ix, iy in industrials))
    elif building_type == "Residential":
        #pre filter must
        hospitals = [c for c, t in placement.items() if t == "Hospital"]
        if hospitals:
            covered = set()
            for h in hospitals:
                for coord, d in _bfs_distances(city, h).items():
                    if d <= 3:
                        covered.add(coord)
            candidates = [c for c in candidates if c in covered]
            candidates.sort(key=lambda c: min(
                abs(c[0]-hx) + abs(c[1]-hy) for hx, hy in hospitals))
    elif building_type == "School":
        #penalise adjacency to
        candidates.sort(key=lambda c: sum(
            10 for nx, ny in _get_neighbors_4dir(c[0], c[1], city.GRID_SIZE)
            if placement.get((nx, ny)) == "Industrial"
        ))
    else:
        random.shuffle(candidates)
    return candidates
#csp backtracking solver

def _backtrack_place(city, building_type, total_needed, placed_count,
                     candidates, placement, available, domains):
    #recursive backtracking to
    if placed_count == total_needed:
        return True
    for coord in candidates:
        if coord not in available:
            continue
        #tentative placement
        placement[coord] = building_type
        available.discard(coord)
        #constraint 1 local
        if _is_placement_valid_local(city, coord, placement):
            #forward checking
            #save domain snapshots
            domain_snapshot = {c: list(d) for c, d in domains.items()}
            if coord in domains:
                del domains[coord]#assigned remove from
            fc_ok = _forward_check(city, coord, placement, domains)
            if fc_ok:
                #re rank for
                if building_type == "Hospital":
                    remaining = _rank_candidates(city, building_type,
                                                 placement, available)
                else:
                    remaining = [c for c in candidates if c in available]
                if _backtrack_place(city, building_type, total_needed,
                                    placed_count + 1, remaining,
                                    placement, available, domains):
                    return True
            #backtrack restore domains
            domains.clear()
            domains.update(domain_snapshot)
        #backtrack undo placement
        del placement[coord]
        available.add(coord)
    return False

def _select_positions(city, building_type, count, placement, available, domains):
    #entry point for
    candidates = _rank_candidates(city, building_type, placement, available)
    if building_type == "Residential":
        placed = 0
        for coord in candidates:
            if coord not in available:
                continue
            placement[coord] = building_type
            available.discard(coord)
            if coord in domains:
                del domains[coord]
            placed += 1
            if placed == count:
                return True
        return placed == count
    return _backtrack_place(city, building_type, count, 0,
                            candidates, placement, available, domains)

def solve_layout(city, building_counts=None):
    #runs the csp
    counts = dict(DEFAULT_COUNTS)
    if building_counts:
        counts.update(building_counts)
    total = sum(counts.values())
    grid_total = city.GRID_SIZE * city.GRID_SIZE
    if total > grid_total:
        print(f"ERROR: {total} buildings requested, only {grid_total} cells available.")
        return None
    city.reset_layout()
    #allow placing buildings
    available = set(city.nodes.keys())
    placement = {}
    #initialise domains for
    domains = _init_domains(city, placement, available)
    order = ["Hospital", "AmbulanceDepot", "Industrial", "School", "PowerPlant",
             "Residential"]
    for building_type in order:
        count = counts.get(building_type, 0)
        if count == 0:
            continue
        print(f"Placing {count} × {building_type}...")
        success = _select_positions(city, building_type, count,
                                    placement, available, domains)
        if not success:
            reason = diagnose_conflict(city, placement, building_type, counts)
            print(f"FAILED to place {building_type}. {reason}")
            return None
    #global constraint check
    if not _is_placement_valid_global(city, placement):
        print("Global constraint check failed. Attempting repair...")
        if not _repair_residential_proximity(city, placement, available, counts):
            print("Repair failed. Try reducing building counts.")
            return None
    #write placement to
    for coord, loc_type in placement.items():
        city.set_node_type(coord, loc_type)
    #assign population densities
    #these values represent
    _POPULATION_BY_TYPE = {
        "Residential":    random.randint(150, 300),
        "School":         random.randint(200, 500),
        "Hospital":       random.randint(50, 150),
        "Industrial":     random.randint(50, 100),
        "PowerPlant":     random.randint(10, 30),
        "AmbulanceDepot": random.randint(5, 15),
    }
    for coord, loc_type in placement.items():
        pop = _POPULATION_BY_TYPE.get(loc_type, 0)
        #re roll per
        if loc_type == "Residential":
            pop = random.randint(150, 300)
        elif loc_type == "School":
            pop = random.randint(200, 500)
        elif loc_type == "Hospital":
            pop = random.randint(50, 150)
        elif loc_type == "Industrial":
            pop = random.randint(50, 100)
        elif loc_type == "AmbulanceDepot":
            pop = random.randint(5, 15)
        city.set_population_density(coord, pop)
    print(f"Layout complete — {len(placement)} buildings placed.")
    city.print_summary()
    return placement

def _repair_residential_proximity(city, placement, available, counts):
    #moves violating residential
    hospitals = [c for c, t in placement.items() if t == "Hospital"]
    if not hospitals:
        return False
    covered = set()
    for h in hospitals:
        for coord, d in _bfs_distances(city, h).items():
            if d <= 3:
                covered.add(coord)
    violators = [c for c, t in placement.items()
                 if t == "Residential" and c not in covered]
    for v_coord in violators:
        moved = False
        for target in covered:
            if target in available and target not in placement:
                del placement[v_coord]
                available.add(v_coord)
                placement[target] = "Residential"
                available.discard(target)
                if _is_placement_valid_local(city, target, placement):
                    moved = True
                    break
                else:
                    del placement[target]
                    available.add(target)
                    placement[v_coord] = "Residential"
                    available.discard(v_coord)
        if not moved:
            return False
    return _check_residential_hospital_proximity(city, placement)

def diagnose_conflict(city, placement, failed_type, counts):
    #returns a human
    if failed_type == "Industrial":
        blocked = sum(
            1 for coord in city.nodes
            if coord not in placement and
            any(placement.get((nx, ny)) in ("School", "Hospital")
                for nx, ny in _get_neighbors_4dir(coord[0], coord[1], city.GRID_SIZE))
        )
        return (f"Constraint 1 blocks {blocked} positions. "
                f"Reduce Industrial count or spread Hospitals/Schools.")
    elif failed_type == "Residential":
        h_count = sum(1 for t in placement.values() if t == "Hospital")
        return (f"Constraint 2: {h_count} hospitals give insufficient 3-hop coverage "
                f"for {counts.get('Residential', 0)} residentials.")
    elif failed_type == "PowerPlant":
        i_count = sum(1 for t in placement.values() if t == "Industrial")
        return (f"Constraint 3: {i_count} industrial zones give insufficient 2-hop "
                f"coverage for {counts.get('PowerPlant', 0)} power plants.")
    elif failed_type == "School":
        return "Constraint 1: too many Industrial zones blocking School placement."
    return f"No specific diagnosis for {failed_type}."

def identify_primary_hospital(city):
    #finds the most
    hospitals = [(coord, node) for coord, node in city.nodes.items()
                 if node.location_type == "Hospital"]
    if not hospitals:
        print("No hospitals found — cannot identify primary.")
        return
    best_coord = None
    best_total = float('inf')
    for h_coord, _ in hospitals:
        total = sum(_bfs_distances(city, h_coord).values())
        if total < best_total:
            best_total = total
            best_coord = h_coord
    if best_coord:
        city.set_primary_hospital(best_coord)
        print(f"Primary Hospital set at {best_coord} (centrality score: {best_total})")
