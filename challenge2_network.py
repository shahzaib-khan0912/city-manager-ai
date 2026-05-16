from collections import deque

class UnionFind:
    #union find structure

    def __init__(self):
        self.parent = {}
        self.rank = {}

    def make_set(self, x):
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])#path compression
        return self.parent[x]

    def union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False#cycle exists
        #union by rank
        if self.rank[rx] < self.rank[ry]:
            self.parent[rx] = ry
        elif self.rank[rx] > self.rank[ry]:
            self.parent[ry] = rx
        else:
            self.parent[ry] = rx
            self.rank[rx] += 1
        return True
#kruskal mst

def _kruskal_mst(city, building_nodes):
    #kruskal algorithm
    sorted_edges = sorted(city.edges, key=lambda e: e.effective_cost)
    uf = UnionFind()
    #make sets
    for coord in city.nodes:
        uf.make_set(coord)
    mst_edges = []
    non_mst_edges = []
    for edge in sorted_edges:
        u_coord = (edge.u.x, edge.u.y)
        v_coord = (edge.v.x, edge.v.y)
        if uf.union(u_coord, v_coord):
            mst_edges.append(edge)
        else:
            non_mst_edges.append(edge)
    return mst_edges, non_mst_edges
#edge disjoint path

def _bfs_path(adj_map, start, end):
    #bfs find path
    if start == end:
        return []
    visited = {start}
    queue = deque([(start, [])])
    while queue:
        curr, path = queue.popleft()
        for neighbor, edge in adj_map.get(curr, []):
            if neighbor not in visited:
                new_path = path + [edge]
                if neighbor == end:
                    return new_path
                visited.add(neighbor)
                queue.append((neighbor, new_path))
    return None

def _build_adj_from_edges(edges):
    #build adjacency map
    adj = {}
    for edge in edges:
        u = (edge.u.x, edge.u.y)
        v = (edge.v.x, edge.v.y)
        adj.setdefault(u, []).append((v, edge))
        adj.setdefault(v, []).append((u, edge))
    return adj

def find_edge_disjoint_paths(edges, start_coord, end_coord):
    #find disjoint paths
    adj = _build_adj_from_edges(edges)
    #find first path
    path1 = _bfs_path(adj, start_coord, end_coord)
    if path1 is None:
        return None, None
    #remove first path
    remaining_edges = [e for e in edges if e not in path1]
    adj2 = _build_adj_from_edges(remaining_edges)
    path2 = _bfs_path(adj2, start_coord, end_coord)
    return path1, path2
#redundancy enforcement

def _enforce_redundancy(city, mst_edges, non_mst_edges,
                         hospital_coord, depot_coord):
    #checks if two
    #1 find the
    adj_mst = _build_adj_from_edges(mst_edges)
    path1 = _bfs_path(adj_mst, hospital_coord, depot_coord)
    if not path1:
        print(f"WARNING: No path at all between Hospital {hospital_coord} "
              f"and Depot {depot_coord} in MST!")
        return []
    #2 check if
    remaining_mst = [e for e in mst_edges if e not in path1]
    adj_mst2 = _build_adj_from_edges(remaining_mst)
    path2_mst = _bfs_path(adj_mst2, hospital_coord, depot_coord)
    if path2_mst:
        print(f"Redundancy OK — two edge-disjoint paths exist in MST.")
        return []
    #3 find a
    print(f"Only one path in MST. Searching full graph for redundancy...")
    remaining_full = [e for e in city.edges if e not in path1 and not e.blocked]
    adj_full = _build_adj_from_edges(remaining_full)
    path2_full = _bfs_path(adj_full, hospital_coord, depot_coord)
    if not path2_full:
        print(f"WARNING: Could not find a second disjoint path in the entire graph! (Might be blocked by river)")
        return []
    #4 add the
    added_edges = []
    for edge in path2_full:
        if edge not in mst_edges:
            mst_edges.append(edge)
            edge.in_mst = True
            added_edges.append(edge)
    print(f"Added {len(added_edges)} redundancy edge(s) for second independent route.")
    return added_edges

def optimize_network(city):
    #runs kruskal s
    #find building nodes
    building_nodes = {coord for coord, node in city.nodes.items()
                      if node.location_type is not None}
    if not building_nodes:
        print("No buildings placed. Run Challenge 1 first.")
        return None
    #reset all mst
    for edge in city.edges:
        edge.in_mst = False
    #run kruskal
    mst_edges, non_mst_edges = _kruskal_mst(city, building_nodes)
    #flag mst edges
    for edge in mst_edges:
        edge.in_mst = True
    total_cost = sum(e.effective_cost for e in mst_edges)
    print(f"Kruskal complete. "
          f"{len(mst_edges)} MST edges, total cost: {total_cost:.2f}")
    #find primary hospital
    hospital_coord = None
    depot_coord = None
    for coord, node in city.nodes.items():
        if node.is_primary_hospital:
            hospital_coord = coord
    #use first ga
    if hasattr(city, 'ambulance_positions') and city.ambulance_positions:
        depot_coord = city.ambulance_positions[0]
    else:
        for coord, node in city.nodes.items():
            if node.location_type == "AmbulanceDepot" and depot_coord is None:
                depot_coord = coord
    redundancy_edges = []
    if hospital_coord and depot_coord:
        redundancy_edges = _enforce_redundancy(
            city, mst_edges, non_mst_edges,
            hospital_coord, depot_coord
        )
    else:
        if not hospital_coord:
            print("WARNING: No Primary Hospital set. "
                  "Run identify_primary_hospital() first.")
        if not depot_coord:
            print("No ambulance position set yet. "
                  "Redundancy will apply after Challenge 3 (GA) runs.")
    result = {
        "mst_edge_count": len(mst_edges),
        "total_cost": total_cost,
        "redundancy_added": len(redundancy_edges) > 0,
        "redundancy_edges_count": len(redundancy_edges)
    }
    print(f"Network optimization complete.")
    return result
