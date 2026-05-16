# CityMind — Urban Intelligence System

A Python-based city simulation that applies classic AI and graph algorithms to urban planning, emergency routing, and disaster response on a 15×15 grid map.

## Features

| Module | Algorithm | Description |
|---|---|---|
| `challenge1_layout.py` | CSP (Constraint Satisfaction) | Optimally places buildings on the grid respecting zoning rules |
| `challenge2_network.py` | Kruskal's MST | Builds a minimum spanning road network connecting all key buildings |
| `challenge3_ga.py` | Genetic Algorithm | Evolves optimal ambulance depot placement to minimize response times |
| `challenge4_routing.py` | A\* Search | Finds shortest emergency routes between any two locations |
| `challenge5_ml.py` | K-Means + Decision Tree | Clusters city zones and predicts flood risk index per node |
| `flood_simulation.py` | BFS Flood Spread | Simulates river flooding, blocks roads, and marks nodes inaccessible |

## Project Structure

```
Project/
├── main.py               # Entry point — initializes city and launches UI
├── city_graph.py         # Core graph: Node, Edge, and CityGraph classes
├── ui.py                 # Pygame-based interactive map UI
├── challenge1_layout.py  # CSP building layout
├── challenge2_network.py # MST road network (Kruskal)
├── challenge3_ga.py      # Genetic algorithm for depot placement
├── challenge4_routing.py # A* emergency routing
├── challenge5_ml.py      # ML risk classification
├── flood_simulation.py   # Flood event simulation
└── assets/               # Fonts, building icons, sounds
```

## Getting Started

### Prerequisites

- Python 3.10+
- Pygame
- scikit-learn
- NumPy

### Installation

```bash
pip install pygame scikit-learn numpy
```

### Run

```bash
python main.py
```

The UI will launch with a randomly populated city. Use the on-screen buttons to run each algorithm step: **CSP → MST → GA**.

## Building Types

- **Residential** — High-density housing (150–300 residents)
- **School** — Educational facilities (200–500 occupants)
- **Hospital** — Medical centres with emergency priority
- **Industrial** — Factories and logistics hubs
- **PowerPlant** — City power infrastructure
- **AmbulanceDepot** — Emergency vehicle station (placed by GA)

## How It Works

1. A 15×15 grid graph is generated with a river running through it.
2. Buildings are placed randomly, then the CSP solver repositions them to satisfy constraints (e.g. hospitals away from industrial zones).
3. Kruskal's algorithm connects all buildings via a minimum-cost road network.
4. The Genetic Algorithm evolves the best ambulance depot location to minimise average BFS distance to citizens.
5. A* handles real-time routing for emergency vehicles.
6. A flood event can be triggered from the UI — spreading from the river, blocking roads, and disabling nodes. ML then re-evaluates risk scores across the city.
