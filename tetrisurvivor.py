import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Set up the display
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tetri-Survivor")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CYAN = (0, 255, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
ORANGE = (255, 165, 0)

GRID_COLOR = (30, 30, 30)
PARTICLE_COLORS = [CYAN, YELLOW, PURPLE, GREEN, RED, BLUE, ORANGE]
BACKGROUND_COLOR = (10, 10, 10)

# Game settings
FPS = 60
GRID_SIZE = 20
PLAYER_SPEED = 0.1
TETROMINO_SPEED = 1
INITIAL_SPAWN_RATE = FPS  # Initial frames between spawns
MIN_SPAWN_RATE = 1  # Minimum frames between spawns
DIFFICULTY_INCREASE_INTERVAL = 30 * FPS  # 30 seconds * 60 frames per second
MAX_MOVEMENT_TIME = 5 * FPS  # 10 seconds * 60 frames per second
COOLDOWN_TIME = 5 * FPS  # 5 seconds * 60 frames per second
COOLDOWN_DECAY_RATE = 0.5  # How quickly the cooldown meter decays when not moving

# Game state
player_pos = [0, 0]  # Player position in grid coordinates
player_color = CYAN
tetrominoes = []
game_over = False
score = 0
spawn_rate = INITIAL_SPAWN_RATE
game_time = 0
movement_timers = {'W': 0, 'A': 0, 'S': 0, 'D': 0}
cooldown_timers = {'W': 0, 'A': 0, 'S': 0, 'D': 0}

# Tetromino shapes and colors
SHAPES = [
    ([[1, 1, 1, 1]], CYAN),    # I
    ([[1, 1], [1, 1]], YELLOW),  # O
    ([[1, 1, 1], [0, 1, 0]], PURPLE),  # T
    ([[1, 1, 1], [1, 0, 0]], ORANGE),  # L
    ([[1, 1, 1], [0, 0, 1]], BLUE),    # J
    ([[1, 1, 0], [0, 1, 1]], GREEN),   # S
    ([[0, 1, 1], [1, 1, 0]], RED)      # Z
]

# List of colors for easy cycling
COLORS = [shape[1] for shape in SHAPES]



class Tetromino:
    def __init__(self, x, y, shape=None, color=None):
        if shape is None or color is None:
            self.shape, self.color = random.choice(SHAPES)
        else:
            self.shape = shape
            self.color = color
        self.x = int(x)
        self.y = int(y)
        self.move_cooldown = 0

    def rotate(self, times=1):
        for _ in range(times):
            self.shape = list(zip(*self.shape[::-1]))

    def move_towards_player(self, player_x, player_y):
        if self.move_cooldown > 0:
            self.move_cooldown -= 1
            return

        dx = player_x - self.x
        dy = player_y - self.y
        
        if abs(dx) > abs(dy):
            self.x += 1 if dx > 0 else -1
        else:
            self.y += 1 if dy > 0 else -1
        
        self.move_cooldown = TETROMINO_SPEED * 60  # Reset cooldown

    def repel(self, player_x, player_y):
        if self.move_cooldown > 0:
            self.move_cooldown -= 1
            return

        dx = self.x - player_x
        dy = self.y - player_y
        
        if abs(dx) > abs(dy):
            self.x += 1 if dx > 0 else -1
        else:
            self.y += 1 if dy > 0 else -1
        
        self.move_cooldown = TETROMINO_SPEED * 60  # Reset cooldown

    def draw(self, surface, offset_x, offset_y):
        for y, row in enumerate(self.shape):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(surface, self.color,
                                     ((self.x + x - offset_x) * GRID_SIZE + WIDTH // 2,
                                      (self.y + y - offset_y) * GRID_SIZE + HEIGHT // 2,
                                      GRID_SIZE, GRID_SIZE))

def draw_cooldown_meters(surface):
    meter_width = 100
    meter_height = 10
    padding = 5
    start_y = HEIGHT - (meter_height + padding) * 4 - padding

    for i, key in enumerate(['W', 'A', 'S', 'D']):
        x = padding
        y = start_y + i * (meter_height + padding)
        
        # Draw background
        pygame.draw.rect(surface, (100, 100, 100), (x, y, meter_width, meter_height))
        
        # Draw movement meter
        movement_width = (movement_timers[key] / MAX_MOVEMENT_TIME) * meter_width
        pygame.draw.rect(surface, (0, 255, 0), (x, y, movement_width, meter_height))
        
        # Draw cooldown meter
        if cooldown_timers[key] > 0:
            cooldown_width = (cooldown_timers[key] / COOLDOWN_TIME) * meter_width
            pygame.draw.rect(surface, (255, 0, 0), (x, y, cooldown_width, meter_height))
        
        # Draw key label
        font = pygame.font.Font(None, 24)
        label = font.render(key, True, WHITE)
        surface.blit(label, (x + meter_width + padding, y))

def spawn_tetromino(player_x, player_y):
    spawn_distance = 20  # Grid cells away from the player
    angle = random.uniform(0, 2 * math.pi)
    x = player_x + int(math.cos(angle) * spawn_distance)
    y = player_y + int(math.sin(angle) * spawn_distance)
    tetromino = Tetromino(x, y)
    tetromino.rotate(random.randint(0, 3))  # Apply random rotation
    return tetromino

# Particle system
particles = []

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(2, 5)
        self.speed = random.uniform(0.5, 2)
        self.angle = random.uniform(0, 2 * math.pi)
        self.lifetime = random.randint(30, 60)

    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.lifetime -= 1
        self.size = max(0, self.size - 0.1)

    def draw(self, surface, offset_x, offset_y):
        pygame.draw.circle(surface, self.color,
                           (int(self.x - offset_x * GRID_SIZE + WIDTH // 2),
                            int(self.y - offset_y * GRID_SIZE + HEIGHT // 2)),
                           int(self.size))

def draw_background_grid(surface, offset_x, offset_y):
    for x in range(0, WIDTH + GRID_SIZE, GRID_SIZE):
        pygame.draw.line(surface, GRID_COLOR,
                         (x - int(offset_x * GRID_SIZE) % GRID_SIZE, 0),
                         (x - int(offset_x * GRID_SIZE) % GRID_SIZE, HEIGHT))
    for y in range(0, HEIGHT + GRID_SIZE, GRID_SIZE):
        pygame.draw.line(surface, GRID_COLOR,
                         (0, y - int(offset_y * GRID_SIZE) % GRID_SIZE),
                         (WIDTH, y - int(offset_y * GRID_SIZE) % GRID_SIZE))

def create_particles(x, y, color, count=10):
    for _ in range(count):
        particles.append(Particle(x, y, color))

def update_particles():
    for particle in particles[:]:
        particle.update()
        if particle.lifetime <= 0:
            particles.remove(particle)

def draw_particles(surface, offset_x, offset_y):
    for particle in particles:
        particle.draw(surface, offset_x, offset_y)

def draw_player(surface, color, x, y):
    glow_radius = GRID_SIZE * 1.5
    glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(glow_surface, (*color, 100), (glow_radius, glow_radius), glow_radius)
    surface.blit(glow_surface, (x - glow_radius, y - glow_radius), special_flags=pygame.BLEND_ALPHA_SDL2)
    pygame.draw.circle(surface, color, (x, y), GRID_SIZE // 2)

def draw_ui(surface, score, game_time):
    font = pygame.font.Font(None, 36)
    score_text = font.render(f"Score: {score}", True, WHITE)
    time_text = font.render(f"Time: {game_time // 60}s", True, WHITE)
    surface.blit(score_text, (10, 10))
    surface.blit(time_text, (10, 50))


def check_adjacent(tetromino1, tetromino2):
    for y1, row1 in enumerate(tetromino1.shape):
        for x1, cell1 in enumerate(row1):
            if cell1:
                for y2, row2 in enumerate(tetromino2.shape):
                    for x2, cell2 in enumerate(row2):
                        if cell2:
                            if (abs(tetromino1.x + x1 - (tetromino2.x + x2)) == 1 and
                                tetromino1.y + y1 == tetromino2.y + y2) or \
                               (abs(tetromino1.y + y1 - (tetromino2.y + y2)) == 1 and
                                tetromino1.x + x1 == tetromino2.x + x2):
                                return True
    return False

def merge_tetrominoes(tetromino1, tetromino2):
    min_x = min(tetromino1.x, tetromino2.x)
    min_y = min(tetromino1.y, tetromino2.y)
    max_x = max(tetromino1.x + len(tetromino1.shape[0]), tetromino2.x + len(tetromino2.shape[0]))
    max_y = max(tetromino1.y + len(tetromino1.shape), tetromino2.y + len(tetromino2.shape))

    new_shape = [[0 for _ in range(max_x - min_x)] for _ in range(max_y - min_y)]

    for y, row in enumerate(tetromino1.shape):
        for x, cell in enumerate(row):
            if cell:
                new_shape[tetromino1.y - min_y + y][tetromino1.x - min_x + x] = 1

    for y, row in enumerate(tetromino2.shape):
        for x, cell in enumerate(row):
            if cell:
                new_shape[tetromino2.y - min_y + y][tetromino2.x - min_x + x] = 1

    merged = Tetromino(min_x, min_y, new_shape, WHITE)
    return merged

def find_connected_squares(shape, start_x, start_y):
    connected = set()
    stack = [(start_x, start_y)]
    
    while stack:
        x, y = stack.pop()
        if 0 <= y < len(shape) and 0 <= x < len(shape[y]) and shape[y][x] and (x, y) not in connected:
            connected.add((x, y))
            stack.extend([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])
    
    return connected

def handle_fragments(tetromino):
    fragments = []
    visited = set()
    
    for y, row in enumerate(tetromino.shape):
        for x, cell in enumerate(row):
            if cell and (x, y) not in visited:
                fragment = find_connected_squares(tetromino.shape, x, y)
                visited.update(fragment)
                fragments.append(fragment)
    
    new_tetrominoes = []
    new_shape = [[0 for _ in range(len(tetromino.shape[0]))] for _ in range(len(tetromino.shape))]
    
    for fragment in fragments:
        if len(fragment) == 4:
            # Create a new Tetromino for this fragment
            min_x = min(x for x, _ in fragment)
            min_y = min(y for _, y in fragment)
            max_x = max(x for x, _ in fragment)
            max_y = max(y for _, y in fragment)
            
            fragment_shape = [[0 for _ in range(max_x - min_x + 1)] for _ in range(max_y - min_y + 1)]
            for x, y in fragment:
                fragment_shape[y - min_y][x - min_x] = 1
            
            # Find the matching original Tetromino color
            for shape, color in SHAPES:
                if shape == fragment_shape:
                    new_tetrominoes.append(Tetromino(tetromino.x + min_x, tetromino.y + min_y, fragment_shape, color))
                    break
            else:
                # If no match found, keep it in the cluster
                for x, y in fragment:
                    new_shape[y][x] = 1
        elif len(fragment) > 4:
            # Keep larger fragments in the cluster
            for x, y in fragment:
                new_shape[y][x] = 1
    
    tetromino.shape = new_shape
    return new_tetrominoes

def check_and_destroy_lines(tetromino):
    global score
    rows_to_remove = []
    cols_to_remove = []

    # Check rows
    for y, row in enumerate(tetromino.shape):
        if sum(row) >= 10:
            rows_to_remove.append(y)

    # Check columns
    for x in range(len(tetromino.shape[0])):
        if sum(row[x] for row in tetromino.shape) >= 10:
            cols_to_remove.append(x)

    # Remove rows
    new_shape = [row for y, row in enumerate(tetromino.shape) if y not in rows_to_remove]

    # Remove columns
    new_shape = [[cell for x, cell in enumerate(row) if x not in cols_to_remove] for row in new_shape]

    lines_cleared = len(rows_to_remove) + len(cols_to_remove)
    if lines_cleared > 0:
        score += lines_cleared * 100
        tetromino.shape = new_shape
        return True
    return False

def main():
    global player_pos, player_color, tetrominoes, game_over, score, spawn_rate, game_time
    global movement_timers, cooldown_timers

    clock = pygame.time.Clock()
    spawn_counter = 0

    while not game_over:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    player_color = COLORS[(COLORS.index(player_color) - 1) % len(COLORS)]
                elif event.key == pygame.K_e:
                    player_color = COLORS[(COLORS.index(player_color) + 1) % len(COLORS)]

        keys = pygame.key.get_pressed()
        
        # Update movement and cooldown timers
        for key, direction in zip(['W', 'A', 'S', 'D'], [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]):
            if keys[direction] and cooldown_timers[key] == 0:
                movement_timers[key] += 1
                if movement_timers[key] >= MAX_MOVEMENT_TIME:
                    cooldown_timers[key] = COOLDOWN_TIME
                    movement_timers[key] = 0
            else:
                movement_timers[key] = max(0, movement_timers[key] - COOLDOWN_DECAY_RATE)
            
            if cooldown_timers[key] > 0:
                cooldown_timers[key] -= 1

        # Player movement
        if keys[pygame.K_w] and cooldown_timers['W'] == 0:
            player_pos[1] -= PLAYER_SPEED
        if keys[pygame.K_s] and cooldown_timers['S'] == 0:
            player_pos[1] += PLAYER_SPEED
        if keys[pygame.K_a] and cooldown_timers['A'] == 0:
            player_pos[0] -= PLAYER_SPEED
        if keys[pygame.K_d] and cooldown_timers['D'] == 0:
            player_pos[0] += PLAYER_SPEED

        # Increase difficulty
        game_time += 1
        if game_time % DIFFICULTY_INCREASE_INTERVAL == 0:
            spawn_rate = max(MIN_SPAWN_RATE, spawn_rate - 1)

        # Spawn new tetrominoes
        spawn_counter += 1
        if spawn_counter >= spawn_rate:
            tetrominoes.append(spawn_tetromino(player_pos[0], player_pos[1]))
            spawn_counter = 0

        # Update tetromino positions
        for tetromino in tetrominoes:
            if tetromino.color == player_color:
                tetromino.repel(player_pos[0], player_pos[1])
            else:
                tetromino.move_towards_player(player_pos[0], player_pos[1])

        # Check for adjacency and merge tetrominoes
        i = 0
        while i < len(tetrominoes):
            j = i + 1
            merged = False
            while j < len(tetrominoes):
                if check_adjacent(tetrominoes[i], tetrominoes[j]):
                    merged_tetromino = merge_tetrominoes(tetrominoes[i], tetrominoes[j])
                    tetrominoes.append(merged_tetromino)
                    tetrominoes.pop(j)
                    tetrominoes.pop(i)
                    merged = True
                    break
                j += 1
            if not merged:
                i += 1

        # Check for line destruction in clusters and handle fragments
        i = 0
        while i < len(tetrominoes):
            if tetrominoes[i].color == WHITE:
                if check_and_destroy_lines(tetrominoes[i]):
                    new_tetrominoes = handle_fragments(tetrominoes[i])
                    tetrominoes.extend(new_tetrominoes)
                    # If the tetromino is completely destroyed, remove it
                    if not any(any(row) for row in tetrominoes[i].shape):
                        tetrominoes.pop(i)
                        continue
            i += 1

        # Check for collision with player
        player_tetromino = Tetromino(player_pos[0], player_pos[1], [[1]], player_color)
        for tetromino in tetrominoes:
            if check_adjacent(tetromino, player_tetromino):
                game_over = True
                break

        # Draw everything
        screen.fill(BACKGROUND_COLOR)
        draw_background_grid(screen, player_pos[0], player_pos[1])
        update_particles()
        draw_particles(screen, player_pos[0], player_pos[1])
        
        for tetromino in tetrominoes:
            tetromino.draw(screen, player_pos[0], player_pos[1])
            if random.random() < 0.01:  # Occasionally create particles for tetrominoes
                create_particles(tetromino.x * GRID_SIZE, tetromino.y * GRID_SIZE, tetromino.color)

        draw_player(screen, player_color, WIDTH // 2, HEIGHT // 2)
        draw_ui(screen, score, game_time)
        draw_cooldown_meters(screen)  # New function to draw cooldown meters

        pygame.display.flip()
        clock.tick(FPS)

    print(f"Game Over! Final Score: {score}")

if __name__ == "__main__":
    main()
    pygame.quit()