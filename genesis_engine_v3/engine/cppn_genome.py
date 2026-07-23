import math
import random

class CPPNNode:
    def __init__(self, node_id, node_type, activation='linear', name=None):
        self.id = node_id
        self.type = node_type  # 'input', 'hidden', 'output'
        self.activation = activation
        self.name = name
        self.value = 0.0

    def activate(self, x):
        if self.activation == 'sin':
            return math.sin(x)
        elif self.activation == 'cos':
            return math.cos(x)
        elif self.activation == 'tanh':
            return math.tanh(x)
        elif self.activation == 'gaussian':
            return math.exp(-x * x)
        elif self.activation == 'linear':
            return x
        return x

    def copy(self):
        return CPPNNode(self.id, self.type, self.activation, self.name)


class CPPNConnection:
    def __init__(self, from_node, to_node, weight, innovation_id, enabled=True):
        self.from_node = from_node
        self.to_node = to_node
        self.weight = weight
        self.innovation_id = innovation_id
        self.enabled = enabled

    def copy(self):
        return CPPNConnection(self.from_node, self.to_node, self.weight, self.innovation_id, self.enabled)


class CPPNGenome:
    def __init__(self):
        self.nodes = {}  # id -> CPPNNode
        self.connections = {}  # innovation_id -> CPPNConnection
        self.next_node_id = 0
        self.next_innovation_id = 0

    def add_input_node(self, name=None):
        node = CPPNNode(self.next_node_id, 'input', name=name)
        self.nodes[node.id] = node
        self.next_node_id += 1
        return node.id

    def add_output_node(self, name=None, activation='tanh'):
        node = CPPNNode(self.next_node_id, 'output', activation=activation, name=name)
        self.nodes[node.id] = node
        self.next_node_id += 1
        return node.id

    def add_connection(self, from_id, to_id, weight):
        conn = CPPNConnection(from_id, to_id, weight, self.next_innovation_id, True)
        self.connections[conn.innovation_id] = conn
        self.next_innovation_id += 1
        return conn.innovation_id

    def activate(self, inputs):
        """
        inputs: dict mapping name -> float, or list of floats
        Returns outputs as dict (if input was dict) or list.
        Uses cached topological order and list indexing for maximum speed.
        """
        if not hasattr(self, '_topo_order'):
            # 1. build incoming connections map as list of tuples
            in_map = {}
            for c in self.connections.values():
                if c.enabled:
                    in_map.setdefault(c.to_node, []).append((c.from_node, c.weight))
            
            # 2. find topological order using DFS
            visited = {} # node_id -> state (0=unvisited, 1=visiting, 2=visited)
            topo_order = []
            
            def dfs(node_id):
                state = visited.get(node_id, 0)
                if state == 1:
                    return True # Cycle detected
                if state == 2:
                    return False
                
                visited[node_id] = 1
                for from_node, _ in in_map.get(node_id, []):
                    if dfs(from_node):
                        return True
                visited[node_id] = 2
                topo_order.append(node_id)
                return False

            output_nodes = [n for n in self.nodes.values() if n.type == 'output']
            for n in output_nodes:
                dfs(n.id)
                
            self._topo_order = topo_order
            self._output_nodes = sorted(output_nodes, key=lambda n: n.id)
            self._input_nodes = sorted([n for n in self.nodes.values() if n.type == 'input'], key=lambda n: n.id)
            self._in_map_tuples = in_map

        # Evaluate using topological order and list-based values
        values = [0.0] * self.next_node_id
        if isinstance(inputs, dict):
            for n in self._input_nodes:
                values[n.id] = inputs.get(n.name, 0.0)
        else:
            for i, n in enumerate(self._input_nodes):
                if i < len(inputs):
                    values[n.id] = inputs[i]

        for n_id in self._topo_order:
            if self.nodes[n_id].type == 'input':
                continue
            
            incoming = self._in_map_tuples.get(n_id, [])
            sum_val = 0.0
            for from_node, weight in incoming:
                sum_val += values[from_node] * weight
            values[n_id] = self.nodes[n_id].activate(sum_val)

        if isinstance(inputs, dict):
            return {n.name: values[n.id] for n in self._output_nodes}
        else:
            return [values[n.id] for n in self._output_nodes]

    def copy(self):
        new_genome = CPPNGenome()
        new_genome.next_node_id = self.next_node_id
        new_genome.next_innovation_id = self.next_innovation_id
        for n_id, node in self.nodes.items():
            new_genome.nodes[n_id] = node.copy()
        for c_id, conn in self.connections.items():
            new_genome.connections[c_id] = conn.copy()
        return new_genome

    def get_length(self):
        return len(self.nodes) + len(self.connections)
        
    @property
    def metabolic_cost(self):
        return len(self.connections) * 0.01
        
    @property
    def sequence(self):
        return []
        
    def to_string(self):
        return f"CPPN(n={len(self.nodes)}, c={len(self.connections)})"
        
    def mutate(self):
        if hasattr(self, '_in_map'): delattr(self, '_in_map')
        if hasattr(self, '_input_nodes'): delattr(self, '_input_nodes')
        if hasattr(self, '_output_nodes'): delattr(self, '_output_nodes')
        if hasattr(self, '_topo_order'): delattr(self, '_topo_order')

        
        if random.random() < 0.03:
            self.add_node_mutation()
        if random.random() < 0.05:
            self.add_connection_mutation()
        if random.random() < 0.10:
            self.mutate_activation_function()
        if random.random() < 0.80:
            self.mutate_weights()

    def mutate_weights(self):
        # modify each connection weight by small Gaussian noise
        for conn in self.connections.values():
            conn.weight += random.gauss(0, 0.1)

    def _creates_cycle(self, from_id, to_id):
        # We want to add an edge from_id -> to_id.
        # This creates a cycle if there's already a path from to_id -> from_id.
        visited = set()
        queue = [to_id]
        while queue:
            curr = queue.pop(0)
            if curr == from_id:
                return True
            if curr not in visited:
                visited.add(curr)
                outgoing = [c.to_node for c in self.connections.values() if c.from_node == curr and c.enabled]
                queue.extend(outgoing)
        return False

    def add_node_mutation(self):
        enabled_conns = [c for c in self.connections.values() if c.enabled]
        if not enabled_conns:
            return False

        old_conn = random.choice(enabled_conns)
        old_conn.enabled = False

        new_node = CPPNNode(self.next_node_id, 'hidden', activation='tanh')
        self.nodes[new_node.id] = new_node
        new_node_id = self.next_node_id
        self.next_node_id += 1

        # from_node -> new_node (weight 1.0)
        conn1 = CPPNConnection(old_conn.from_node, new_node_id, 1.0, self.next_innovation_id, True)
        self.connections[conn1.innovation_id] = conn1
        self.next_innovation_id += 1

        # new_node -> to_node (weight old_conn.weight)
        conn2 = CPPNConnection(new_node_id, old_conn.to_node, old_conn.weight, self.next_innovation_id, True)
        self.connections[conn2.innovation_id] = conn2
        self.next_innovation_id += 1

        return True

    def add_connection_mutation(self):
        node_ids = list(self.nodes.keys())
        for _ in range(10):
            n1 = random.choice(node_ids)
            n2 = random.choice(node_ids)

            if n1 == n2:
                continue
            if self.nodes[n2].type == 'input':
                continue

            exists = False
            for c in self.connections.values():
                if c.from_node == n1 and c.to_node == n2:
                    exists = True
                    # Re-enable if disabled
                    if not c.enabled:
                        c.enabled = True
                        return True
                    break

            if exists:
                continue

            if not self._creates_cycle(n1, n2):
                self.add_connection(n1, n2, random.gauss(0, 1.0))
                return True

        return False

    def mutate_activation_function(self):
        hidden_nodes = [n for n in self.nodes.values() if n.type == 'hidden']
        if not hidden_nodes:
            return False

        node = random.choice(hidden_nodes)
        activations = ['tanh', 'sin', 'cos', 'gaussian', 'linear']
        if node.activation in activations:
            activations.remove(node.activation)
        if not activations:
            return False
        node.activation = random.choice(activations)
        return True

    @staticmethod
    def crossover(parent1, parent2):
        child = CPPNGenome()
        child.next_node_id = max(parent1.next_node_id, parent2.next_node_id)
        child.next_innovation_id = max(parent1.next_innovation_id, parent2.next_innovation_id)

        # Inherit all nodes from both
        for p in [parent1, parent2]:
            for n_id, node in p.nodes.items():
                if n_id not in child.nodes:
                    child.nodes[n_id] = node.copy()

        # connections alignment
        all_innovations = set(parent1.connections.keys()).union(set(parent2.connections.keys()))
        for innov in all_innovations:
            in_p1 = innov in parent1.connections
            in_p2 = innov in parent2.connections

            if in_p1 and in_p2:
                # Randomly pick from whichever since we treat them equally
                parent = random.choice([parent1, parent2])
                conn = parent.connections[innov].copy()
                child.connections[innov] = conn
            elif in_p1:
                child.connections[innov] = parent1.connections[innov].copy()
            else:
                child.connections[innov] = parent2.connections[innov].copy()

        return child

    def compatibility_distance(self, other):
        # (c1 * E)/N + (c2 * D)/N + c3 * W
        c1, c2, c3 = 1.0, 1.0, 0.4

        innov1 = set(self.connections.keys())
        innov2 = set(other.connections.keys())

        max_innov1 = max(innov1) if innov1 else 0
        max_innov2 = max(innov2) if innov2 else 0

        N = max(len(self.connections), len(other.connections))
        if N < 1:
            return 0.0

        E = 0
        D = 0
        matching_weight_diff = 0.0
        matching_count = 0

        all_innov = innov1.union(innov2)
        for innov in all_innov:
            in1 = innov in self.connections
            in2 = innov in other.connections

            if in1 and in2:
                diff = abs(self.connections[innov].weight - other.connections[innov].weight)
                matching_weight_diff += diff
                matching_count += 1
            elif in1:
                if innov > max_innov2:
                    E += 1
                else:
                    D += 1
            else:
                if innov > max_innov1:
                    E += 1
                else:
                    D += 1

        W = (matching_weight_diff / matching_count) if matching_count > 0 else 0.0
        return (c1 * E) / N + (c2 * D) / N + c3 * W
