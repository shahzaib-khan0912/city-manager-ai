#genetic algorithm
import random
from collections import deque


def _bfs_shortest(city, start_coord):
    #bfs shortest path
    start_node = city.nodes.get(start_coord)
    if not start_node or not start_node.accessible:
        return {}
    dist = {start_coord: 0}
    queue = deque([start_node])
    while queue:
        node = queue.popleft()
        curr_coord = (node.x, node.y)
        for neighbor, edge in city.get_neighbors(node):
            n_coord = (neighbor.x, neighbor.y)
            if edge.blocked or not neighbor.accessible:
                continue
            if n_coord not in dist:
                dist[n_coord] = dist[curr_coord] + 1
                queue.append(neighbor)
    return dist

def _get_citizen_nodes(city):
    #get citizen nodes
    citizen_types = {"Residential", "School", "Hospital"}
    return [
        (node.x, node.y)
        for node in city.nodes.values()
        if node.location_type in citizen_types and node.accessible
    ]

def _get_valid_placement_nodes(city):
    #valid placement nodes
    return [
        (node.x, node.y)
        for node in city.nodes.values()
        if node.accessible and node.location_type is None
    ]
#fitness function

def _fitness(city, chromosome, citizen_nodes):
    penalty = city.GRID_SIZE * 10
    #pre compute bfs
    amb_distances = {}
    for amb_coord in chromosome:
        amb_distances[amb_coord] = _bfs_shortest(city, amb_coord)
    worst_case = 0
    for citizen in citizen_nodes:
        #minimum distance from
        min_dist = penalty
        for amb_coord in chromosome:
            d = amb_distances[amb_coord].get(citizen, penalty)
            if d < min_dist:
                min_dist = d
        if min_dist > worst_case:
            worst_case = min_dist
    return worst_case

def _init_population(valid_nodes, pop_size, num_ambulances):
    population = []
    for _ in range(pop_size):
        chromo = random.sample(valid_nodes, num_ambulances)
        population.append(chromo)
    return population

def _tournament_select(population, fitnesses, k=5):
    contestants = random.sample(range(len(population)), min(k, len(population)))
    best = min(contestants, key=lambda i: fitnesses[i])
    return population[best]

def _crossover(parent_a, parent_b):
    child = []
    used = set()
    for i in range(len(parent_a)):
        #50 50 chance
        donor = parent_a if random.random() < 0.5 else parent_b
        gene = donor[i]
        if gene not in used:
            child.append(gene)
            used.add(gene)
        else:
            #alternate parent
            alt = parent_b[i] if donor is parent_a else parent_a[i]
            if alt not in used:
                child.append(alt)
                used.add(alt)
    #fill remaining
    if len(child) < len(parent_a):
        all_genes = set(parent_a + parent_b)
        remaining = [g for g in all_genes if g not in used]
        random.shuffle(remaining)
        while len(child) < len(parent_a) and remaining:
            child.append(remaining.pop())
    return child

def _mutate(city, chromosome, valid_nodes, mutation_rate=0.3):
    if random.random() > mutation_rate:
        return chromosome
    idx = random.randint(0, len(chromosome) - 1)
    old_coord = chromosome[idx]
    node = city.nodes.get(old_coord)
    if not node:
        return chromosome
    #get accessible non
    neighbors = []
    for neighbor, edge in city.get_neighbors(node):
        if not edge.blocked and neighbor.accessible:
            n_coord = (neighbor.x, neighbor.y)
            if n_coord not in chromosome:#no two ambulances
                neighbors.append(n_coord)
    if neighbors:
        chromosome[idx] = random.choice(neighbors)
    else:
        #fallback move to
        available = [v for v in valid_nodes if v not in chromosome]
        if available:
            chromosome[idx] = random.choice(available)
    return chromosome

def evaluate_depots(city, num_ambulances=3, pop_size=60, generations=300,
                    stagnation_limit=30):
    citizen_nodes = _get_citizen_nodes(city)
    valid_nodes = _get_valid_placement_nodes(city)
    if not citizen_nodes:
        print("No citizen nodes found. Run Challenge 1 first.")
        return None
    if len(valid_nodes) < num_ambulances:
        print(f"Not enough accessible nodes ({len(valid_nodes)}) "
              f"for {num_ambulances} ambulances.")
        return None
    print(f"Running GA...")
    print(f"Citizens: {len(citizen_nodes)}")
    print(f"Positions: {len(valid_nodes)}")
    print(f"Population     : {pop_size}")
    print(f"Max generations: {generations}")
    #initialise population
    population = _init_population(valid_nodes, pop_size, num_ambulances)
    best_ever = None
    best_fitness_ever = float('inf')
    stagnation = 0
    #evolution loop
    for gen in range(generations):
        #evaluate fitness for
        fitnesses = [_fitness(city, chromo, citizen_nodes) for chromo in population]
        #track best
        gen_best_idx = min(range(len(fitnesses)), key=lambda i: fitnesses[i])
        gen_best_fitness = fitnesses[gen_best_idx]
        if gen_best_fitness < best_fitness_ever:
            best_fitness_ever = gen_best_fitness
            best_ever = list(population[gen_best_idx])
            stagnation = 0
        else:
            stagnation += 1
        #progress logging every
        if gen % 50 == 0 or gen == generations - 1:
            avg_fit = sum(fitnesses) / len(fitnesses)
            print(f"Gen {gen:3d} | Best: {best_fitness_ever} | "
                  f"Gen best: {gen_best_fitness} | Avg: {avg_fit:.1f}")
        #early stop on
        if stagnation >= stagnation_limit:
            print(f"Early stop at gen {gen} — "
                  f"no improvement for {stagnation_limit} generations.")
            break
        #build next generation
        next_pop = []
        #elitism keep the
        next_pop.append(list(best_ever))
        while len(next_pop) < pop_size:
            parent_a = _tournament_select(population, fitnesses)
            parent_b = _tournament_select(population, fitnesses)
            child = _crossover(list(parent_a), list(parent_b))
            child = _mutate(city, child, valid_nodes)
            #ensure child has
            if len(child) == num_ambulances:
                next_pop.append(child)
            else:
                #safety if crossover
                next_pop.append(_mutate(city, list(parent_a), valid_nodes))
        population = next_pop
    #store result in
    city.ambulance_positions = best_ever if best_ever else []
    excluded = set(city.ambulance_positions)
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
    num_civilians = min(5, len(civilian_candidates))
    city.trapped_civilians = random.sample(civilian_candidates, num_civilians)
    print(f"\n=== RESULT ===")
    print(f"Best positions     : {best_ever}")
    print(f"Worst-case distance: {best_fitness_ever} hops")
    print(f"Generations run    : {min(gen + 1, generations)}")
    print(f"Trapped civilians  : {num_civilians} placed at {city.trapped_civilians}")
    return {
        "best_positions": best_ever,
        "best_fitness": best_fitness_ever,
        "generations_run": min(gen + 1, generations),
        "civilians_placed": num_civilians,
    }
