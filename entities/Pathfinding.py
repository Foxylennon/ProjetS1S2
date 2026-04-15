import heapq
import math

class NavGrid:
    """Grille de navigation pour l'algorithme A*"""
    
    def __init__(self, width, height, cell_size):
        self.cell_size = cell_size
        self.cols = int(math.ceil(width / cell_size))
        self.rows = int(math.ceil(height / cell_size))
        # 0 = marchable, 1 = obstacle
        self.grid = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        
    def add_walls(self, walls):
        """Marque les cellules couvertes par les murs comme obstacles."""
        for wall in walls:
            # Légère marge pour éviter que l'ennemi se frotte trop contre les angles
            margin = 2
            left_col = max(0, int((wall.rect.left - margin) // self.cell_size))
            right_col = min(self.cols - 1, int((wall.rect.right + margin) // self.cell_size))
            top_row = max(0, int((wall.rect.top - margin) // self.cell_size))
            bottom_row = min(self.rows - 1, int((wall.rect.bottom + margin) // self.cell_size))
            
            for r in range(top_row, bottom_row + 1):
                for c in range(left_col, right_col + 1):
                    self.grid[r][c] = 1

    def _get_neighbors(self, node):
        r, c = node
        neighbors = []
        # Support pour les mouvements diagonaux (8 directions)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                if self.grid[nr][nc] == 0:
                    # Ne pas autoriser le franchissement de mur en diagonale ("corner cutting")
                    if abs(dr) == 1 and abs(dc) == 1:
                        if self.grid[r+dr][c] == 1 or self.grid[r][c+dc] == 1:
                            continue
                    neighbors.append((nr, nc))
        return neighbors

    def find_path(self, start_pos, target_pos):
        """Pathfinding A-Star standard. Renvoie une liste de coordonnées en pixels (Waypoints)."""
        start_node = (int(start_pos[1] // self.cell_size), int(start_pos[0] // self.cell_size))
        target_node = (int(target_pos[1] // self.cell_size), int(target_pos[0] // self.cell_size))
        
        # Clamp pour s'assurer qu'on ne cherche pas hors de l'écran
        start_node = (max(0, min(self.rows - 1, start_node[0])), max(0, min(self.cols - 1, start_node[1])))
        target_node = (max(0, min(self.rows - 1, target_node[0])), max(0, min(self.cols - 1, target_node[1])))

        # Si le noeud de départ ou d'arrivée est identique ou dans un mur, on stoppe (la fallback glissera l'IA)
        if self.grid[target_node[0]][target_node[1]] == 1 or start_node == target_node:
            return []

        open_set = []
        heapq.heappush(open_set, (0, start_node))
        came_from = {}
        
        g_score = {start_node: 0}
        
        def heuristic(a, b):
            # Distance euclidienne ou de Tchebychev
            return math.hypot(a[0]-b[0], a[1]-b[1])

        while open_set:
            _, current = heapq.heappop(open_set)
            
            if current == target_node:
                break
                
            for neighbor in self._get_neighbors(current):
                # Le coût de voyage est sqrt(2) ~ 1.414 pour la diagonale, 1 pour vertical/horizontal
                is_diagonal = (current[0] != neighbor[0] and current[1] != neighbor[1])
                tentative_g_score = g_score[current] + (1.414 if is_diagonal else 1.0)
                
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score = tentative_g_score + heuristic(neighbor, target_node)
                    heapq.heappush(open_set, (f_score, neighbor))
                    
        # Rétrospection pour créer le chemin
        path = []
        current = target_node
        if current in came_from or current == start_node:
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.reverse()
            
        # Conversion noeuds matriciels -> position en pixels du jeu (centre de la case)
        pixel_path = []
        for r, c in path:
            pixel_path.append((c * self.cell_size + self.cell_size / 2, r * self.cell_size + self.cell_size / 2))
            
        return pixel_path
