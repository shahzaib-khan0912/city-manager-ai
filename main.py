#citymind main entry
import random
from city_graph import CityGraph
from challenge1_layout import DEFAULT_COUNTS
from ui import CityMapUI

def _random_placement(city, building_counts=None):
    #random building scatter
    counts = dict(DEFAULT_COUNTS)
    if building_counts:
        counts.update(building_counts)
    total = sum(counts.values())
    grid_total = city.GRID_SIZE * city.GRID_SIZE
    if total > grid_total:
        print(f"Too many buildings ({total}) for grid ({grid_total}). Reducing.")
        #scale down
        scale = grid_total * 0.7 / total
        counts = {k: max(1, int(v * scale)) for k, v in counts.items()}
    city.reset_layout()
    #shuffle coords
    all_coords = list(city.nodes.keys())
    #avoid river
    river_set = set(city.river_nodes)
    available = [c for c in all_coords if c not in river_set]
    random.shuffle(available)
    idx = 0
    for building_type, count in counts.items():
        for _ in range(count):
            if idx >= len(available):
                break
            coord = available[idx]
            city.set_node_type(coord, building_type)
            #population density
            pop_map = {
                "Residential": (150, 300),
                "School": (200, 500),
                "Hospital": (50, 150),
                "Industrial": (50, 100),
                "PowerPlant": (10, 30),
            }
            lo, hi = pop_map.get(building_type, (0, 0))
            city.set_population_density(coord, random.randint(lo, hi))
            idx += 1
    placed = sum(1 for n in city.nodes.values() if n.location_type)
    print(f"Placed {placed} buildings randomly (no constraints).")

def main():
    print("=" * 50)
    print("  CityMind — Urban Intelligence System")
    print("=" * 50)
    #create city
    city = CityGraph()
    city.print_summary()
    print("\n-- Initial random building placement --")
    _random_placement(city)
    city.print_summary()
    print("\n-- Launching CityMind UI --")
    print("   Use buttons to run: CSP -> MST -> GA")
    ui = CityMapUI(city)
    ui.run()
if __name__ == "__main__":
    main()
