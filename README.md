# CityMind — Urban Intelligence System

A Python simulation of a living city built entirely on classic AI algorithms. Every system — from where buildings go to how ambulances respond to a flood — is driven by a real algorithm working on a shared city graph.

---

## What This Is

CityMind models a 15×15 grid city with a procedurally generated river running through it. Buildings, roads, and emergency services are not hand-placed — they are computed. Five algorithms run in sequence, each one using the output of the last, on top of a shared `CityGraph` data structure that all modules read and write.

---

## The City Graph

Every cell in the 15×15 grid is a `Node`. Adjacent nodes are connected by `Edge` objects representing roads. Nodes carry:
- `location_type` — what building sits here
- `population_density` — number of occupants
- `risk_index` — crime/hazard risk score (written by the ML module)
- `accessible` — set to `False` when flooded

Edge `effective_cost` is dynamic. It starts at 1.0, drops to 0.8 for residential roads, and gets multiplied by 1.5× (High risk) or 1.2× (Medium risk) after the ML pipeline runs. Every routing algorithm automatically uses the updated costs.

---

## Algorithm 1 — CSP Building Layout (`challenge1_layout.py`)

Buildings are placed using a **Constraint Satisfaction Problem** solver with backtracking and forward checking.

**Hard constraints enforced:**
- Industrial zones cannot be placed adjacent (4-directional) to Schools or Hospitals
- Every Residential node must be within BFS distance ≤ 3 of at least one Hospital
- Every PowerPlant must be within BFS distance ≤ 2 of at least one Industrial zone

**How it works:**
1. Buildings are placed in a fixed order: `Hospital → AmbulanceDepot → Industrial → School → PowerPlant → Residential`
2. For each building type, candidates are ranked by heuristic before backtracking begins — hospitals are spread to pre-seeded quadrant targets; industrial zones are pushed to grid edges; power plants are pre-filtered to only positions within industrial coverage
3. After each placement, **forward checking** prunes the domains of unassigned neighbouring cells (e.g. placing Industrial removes School/Hospital from all 4 neighbours' domains). A domain wipe-out causes immediate backtrack
4. If global constraints still fail after backtracking, a **repair pass** relocates violating Residential nodes into hospital-covered cells
5. After layout, the hospital with the lowest total BFS distance sum to all other nodes is flagged as the **primary hospital**

**Default building counts:** 9 hospitals, 10 industrial, 15 schools, 10 power plants, 80 residential, 1 ambulance depot

---

## Algorithm 2 — Road Network MST (`challenge2_network.py`)

Connects all buildings with a minimum-cost road network using **Kruskal's algorithm**.

**Implementation details:**
- Union-Find with **path compression** and **union by rank** for near-O(α) operations
- Edges are sorted by `effective_cost` (already risk-weighted if ML has run) and greedily merged
- After the MST is built, the system checks if there are **two edge-disjoint paths** between the primary hospital and the ambulance depot
- If only one path exists in the MST, it searches the full graph for a second path via BFS on remaining edges and adds the minimum extra edges needed — ensuring the critical hospital↔depot link has redundancy even if one route fails

---

## Algorithm 3 — Ambulance Depot Placement via GA (`challenge3_ga.py`)

A **Genetic Algorithm** finds the optimal positions for 3 ambulance depots to minimise worst-case response time to any citizen.

**Fitness function:** worst-case BFS distance from the nearest depot to the furthest reachable citizen node (Residential, School, or Hospital). Blocked and inaccessible nodes are excluded.

**GA configuration:**
- Population size: 60 chromosomes, each a list of 3 grid coordinates
- Max generations: 300, with early stopping after 30 generations of no improvement
- **Selection:** tournament selection with k=5 contestants
- **Crossover:** gene-by-gene with 50/50 donor selection, duplicate-safe with fallback from the alternate parent
- **Mutation rate:** 30% — relocates one depot to an accessible neighbour; falls back to a random valid node if no neighbours are free
- **Elitism:** the best chromosome is always carried into the next generation unchanged

After the GA converges, 5 trapped civilians are randomly seeded at non-hospital, non-depot building nodes to set up the routing challenge.

---

## Algorithm 4 — Emergency Routing with A* (`challenge4_routing.py`)

**A\*** finds the shortest path between any two nodes using Manhattan distance as the admissible heuristic. Edge costs are the live `effective_cost` values (risk-weighted, flood-aware).

The full rescue mission runs as **multi-stop routing:**
1. Start from the ambulance depot closest to the first civilian
2. Route to each trapped civilian in sequence using A*
3. After all civilians are reached, route to the nearest hospital
4. Return to the starting depot

If a road is found to be blocked during travel (checked edge-by-edge on the computed path), the route is **dynamically recalculated** from the current position. When a flood event fires mid-mission, the entire rescue plan is re-evaluated from scratch against the updated graph.

---

## Algorithm 5 — Crime Risk Prediction Pipeline (`challenge5_ml.py`)

An **8-step ML pipeline** classifies every node in the city as High / Medium / Low risk and feeds the results back into the routing layer.

**Step-by-step:**

1. **Feature extraction** — for each of the 225 nodes, extract: population density, Euclidean distance to nearest industrial zone, distance to nearest hospital, distance to nearest power plant, binary flags for industrial and residential type

2. **Standardisation** — `StandardScaler` (zero mean, unit variance) applied across the feature matrix

3. **K-Means clustering** — fit with k=3 and k=4, select the model with lower inertia. Cluster labels become an additional feature

4. **Synthetic incident rate generation** — a weighted formula computes a ground-truth risk rate per node:
   - Population density contributes 40%
   - Proximity to industrial zones contributes 35%
   - Being an industrial node adds 25% bonus
   - Remoteness from hospitals adds 15%
   - Gaussian noise (σ=0.03) is added for realism

5. **Label generation** — rates > 0.60 → High, > 0.30 → Medium, else Low

6. **Decision Tree training** — `DecisionTreeClassifier` with max depth 5, balanced class weights, trained on the 7-feature augmented matrix (original 6 + cluster ID)

7. **Risk write-back** — predicted labels are converted to risk scores (High=0.85, Medium=0.45, Low=0.10) and written to each node's `risk_index`. Edge costs are immediately recalculated: High-risk edges cost 1.5×, Medium 1.2×

8. **Police deployment** — 10 police officers are assigned to the 10 nodes with the highest raw incident rates

---
## Running the Project

```bash
pip install pygame scikit-learn numpy
python main.py
```

The Pygame UI launches with a random city. Use the on-screen buttons to step through: **CSP → MST → GA → A\* → Flood → ML**

---

- **Pygame** — interactive grid visualisation
- **scikit-learn** — KMeans, DecisionTreeClassifier, StandardScaler
- **NumPy** — feature matrix construction
