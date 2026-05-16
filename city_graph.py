import math
import random

class Node:
    #node in grid

    def __init__(self, node_id, x, y):
        self.id = node_id
        self.x = x
        self.y = y
        #core attributes
        self.location_type = None#building type
        self.population_density = 0.0#people count
        self.is_primary_hospital = False#primary hospital
        self.risk_index = 0.0#risk 0 to
        self.accessible = True#not flooded

    def __repr__(self):
        return f"Node({self.id}, {self.location_type} at ({self.x},{self.y}))"

class Edge:
    #road between nodes

    def __init__(self, u, v, base_cost=1.0):
        self.u = u#node u
        self.v = v#node v
        self.base_cost = base_cost
        self.blocked = False
        self.effective_cost = base_cost
        self.in_mst = False#in mst

    def update_effective_cost(self):
        #recalculate effective cost
        if self.blocked:
            self.effective_cost = float('inf')
            return
        cost = self.base_cost
        #residential cheaper
        if self.u.location_type == "Residential" or self.v.location_type == "Residential":
            cost = 0.8
        #risk penalty

        def _risk_multiplier(risk_idx):
            if risk_idx >= 0.7:
                return 1.5
            elif risk_idx >= 0.3:
                return 1.2
            else:
                return 1.0
        avg_multiplier = (_risk_multiplier(self.u.risk_index) +
                          _risk_multiplier(self.v.risk_index)) / 2.0
        self.effective_cost = cost * avg_multiplier

    def __repr__(self):
        status = "BLOCKED" if self.blocked else f"cost={self.effective_cost:.2f}"
        return f"Edge({self.u.id}<->{self.v.id}, {status})"

class CityGraph:
    #shared city graph
    GRID_SIZE = 15

    def __init__(self):
        self.nodes = {}#x y node
        self.edges = []#list of all
        self.adj = {}#node list of
        self.river_nodes = []#list of x
        self.ambulance_positions = []#set by challenge
        self.trapped_civilians = []#list of x
        self.routing_result = None#set by challenge
        self.police_positions = []#set by challenge
        self._build_grid()
        self._connect_grid()
        self._generate_river()
    #grid setup

    def _build_grid(self):
        #creates all 225
        node_id = 0
        for y in range(self.GRID_SIZE):
            for x in range(self.GRID_SIZE):
                node = Node(node_id, x, y)
                self.nodes[(x, y)] = node
                self.adj[node] = []
                node_id += 1

    def _connect_grid(self):
        #connects every node
        for y in range(self.GRID_SIZE):
            for x in range(self.GRID_SIZE):
                if x < self.GRID_SIZE - 1:
                    self.connect_nodes((x, y), (x + 1, y))
                if y < self.GRID_SIZE - 1:
                    self.connect_nodes((x, y), (x, y + 1))
    #river generation

    def _generate_river(self):
        #generates a single
        self.river_nodes = []
        #start from top
        if random.random() < 0.5:
            curr = (random.randint(2, self.GRID_SIZE - 3), 0)#top edge
        else:
            curr = (0, random.randint(2, self.GRID_SIZE - 3))#left edge
        self.river_nodes.append(curr)
        #river flows mostly
        while 0 <= curr[0] < self.GRID_SIZE and 0 <= curr[1] < self.GRID_SIZE:
            moves = [(1, 0), (0, 1), (-1, 0), (0, -1)]
            weights = [4, 4, 1, 1]#bias toward right
            dx, dy = random.choices(moves, weights=weights, k=1)[0]
            next_pos = (curr[0] + dx, curr[1] + dy)
            #stop if we
            if not (0 <= next_pos[0] < self.GRID_SIZE and 0 <= next_pos[1] < self.GRID_SIZE):
                break
            #avoid revisiting to
            if next_pos not in self.river_nodes:
                self.river_nodes.append(next_pos)
            curr = next_pos
            #stop once we
            if curr[0] == self.GRID_SIZE - 1 or curr[1] == self.GRID_SIZE - 1:
                break
    #graph methods used

    def connect_nodes(self, u_coord, v_coord, base_cost=1.0):
        #creates a bidirectional
        u = self.nodes.get(u_coord)
        v = self.nodes.get(v_coord)
        if not u or not v:
            return None
        #don t duplicate
        for neighbor, edge in self.adj[u]:
            if neighbor == v:
                return edge
        edge = Edge(u, v, base_cost)
        self.edges.append(edge)
        self.adj[u].append((v, edge))
        self.adj[v].append((u, edge))
        return edge

    def get_node(self, coord):
        #returns the node
        return self.nodes.get(coord)

    def get_neighbors(self, node):
        #returns list of
        return self.adj.get(node, [])

    def set_node_type(self, coord, location_type):
        #sets the location
        node = self.nodes.get(coord)
        if node:
            node.location_type = location_type
            #update edges since
            for _, edge in self.adj[node]:
                edge.update_effective_cost()

    def set_primary_hospital(self, coord):
        #marks a hospital
        node = self.nodes.get(coord)
        if node:
            node.is_primary_hospital = True

    def set_population_density(self, coord, value):
        #sets population density
        node = self.nodes.get(coord)
        if node:
            node.population_density = max(0.0, value)

    def update_risk(self, coord, value):
        #updates risk index
        node = self.nodes.get(coord)
        if node:
            node.risk_index = max(0.0, min(1.0, value))
            for _, edge in self.adj[node]:
                edge.update_effective_cost()

    def block_edge(self, u_coord, v_coord):
        #blocks the edge
        u = self.nodes.get(u_coord)
        v = self.nodes.get(v_coord)
        if u and v:
            for neighbor, edge in self.adj[u]:
                if neighbor == v:
                    edge.blocked = True
                    edge.effective_cost = float('inf')
                    return

    def unblock_edge(self, u_coord, v_coord):
        #unblocks an edge
        u = self.nodes.get(u_coord)
        v = self.nodes.get(v_coord)
        if u and v:
            for neighbor, edge in self.adj[u]:
                if neighbor == v:
                    edge.blocked = False
                    edge.update_effective_cost()
                    return

    def is_edge_blocked(self, u_coord, v_coord):
        #returns true if
        u = self.nodes.get(u_coord)
        v = self.nodes.get(v_coord)
        if u and v:
            for neighbor, edge in self.adj[u]:
                if neighbor == v:
                    return edge.blocked
        return False

    def update_all_edge_costs(self):
        #recalculates effective cost
        for edge in self.edges:
            edge.update_effective_cost()

    def get_all_nodes(self):
        #returns all node
        return list(self.nodes.values())

    def reset_layout(self):
        #clears all node
        for node in self.nodes.values():
            node.location_type = None
            node.population_density = 0.0
            node.is_primary_hospital = False
            node.risk_index = 0.0
            node.accessible = True
        self.ambulance_positions = []
        self.trapped_civilians = []
        self.routing_result = None
        self.police_positions = []
        self.update_all_edge_costs()
    #debug helpers

    def print_summary(self):
        #prints a quick
        types = {}
        for node in self.nodes.values():
            t = node.location_type or "Empty"
            types[t] = types.get(t, 0) + 1
        blocked = sum(1 for e in self.edges if e.blocked)
        print(f"\n[CityGraph Summary]")
        print(f"  Nodes     : {len(self.nodes)}")
        print(f"  Edges     : {len(self.edges)}")
        print(f"  Blocked   : {blocked}")
        print(f"  River     : {len(self.river_nodes)} tiles")
        print(f"  Types     : {types}\n")
