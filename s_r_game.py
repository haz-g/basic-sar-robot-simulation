import pygame
import random
import time

# Initialize Pygame
pygame.init()

# Define game constants
MAP_WIDTH, MAP_HEIGHT = 580, 420
DISPLAY_WIDTH, DISPLAY_HEIGHT = 750, 750
VIEWPORT_SIZE = 100
SCALE_FACTOR = DISPLAY_WIDTH // VIEWPORT_SIZE
TILE_SIZE = 20
FPS = 30
HUMAN_COUNT = 3
GAME_DURATION = 30  # 30 seconds countdown
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
FLOOR_COLOR = (45, 26, 43)
GOLD = (74, 50, 50)
BOX_COLOR = (100, 100, 100, 180)  # Semi-transparent gray

# Load game images
map = pygame.image.load('map.png')
robot = pygame.image.load('robot.png')
humans = [pygame.image.load(f'human_{i}.png') for i in range(1, 4)]

# Remove black backgrounds from images
robot.set_colorkey(BLACK)
for img in humans:
    img.set_colorkey(BLACK)

# Create small semi-transparent versions of human images for UI
ui_humans = []
for img in humans:
    small_img = pygame.transform.scale(img, (30, 30))
    small_img.set_alpha(128)  # Set semi-transparent
    ui_humans.append(small_img)

# Create the game window
screen = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
pygame.display.set_caption("Search and Rescue Robot Game")

# Create a surface for the entire map
map_surface = pygame.Surface((MAP_WIDTH, MAP_HEIGHT))
map_surface.blit(map, (0, 0))

# Find valid floor positions
floor_positions = []
for x in range(0, MAP_WIDTH, TILE_SIZE):
    for y in range(0, MAP_HEIGHT, TILE_SIZE):
        if map_surface.get_at((x, y)) == FLOOR_COLOR:
            floor_positions.append((x, y))

# Find the golden square position (starting position)
golden_pos = None
for x in range(0, MAP_WIDTH, TILE_SIZE):
    for y in range(0, MAP_HEIGHT, TILE_SIZE):
        if map_surface.get_at((x, y)) == GOLD:
            golden_pos = (x, y)
            break
    if golden_pos:
        break

# Set up the robot
robot_rect = robot.get_rect()
robot_rect.topleft = golden_pos

# Set up the humans
human_rects = []
rescued_humans = [False] * HUMAN_COUNT

def reset_humans():
    global human_rects, rescued_humans
    human_rects = []
    rescued_humans = [False] * HUMAN_COUNT
    available_positions = floor_positions.copy()
    for i in range(HUMAN_COUNT):
        if available_positions:
            pos = random.choice(available_positions)
            available_positions.remove(pos)
            human_rect = humans[i].get_rect()
            human_rect.topleft = pos
            human_rects.append((i, human_rect))

# Initialize human positions
reset_humans()

# Set up timing
clock = pygame.time.Clock()
start_time = None
quickest_rescue = float('inf')

# Movement cooldown
last_move_time = 0
move_cooldown = 100  # milliseconds

# Function to draw time box and human icons
def draw_info_box(surface, time_left, quickest_rescue, rescued_humans):
    font = pygame.font.Font(None, 32)
    box_width = 300
    box_height = 90
    box_x = (DISPLAY_WIDTH - box_width) // 2
    box_y = 10

    # Draw semi-transparent box
    box_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
    box_surface.fill(BOX_COLOR)
    surface.blit(box_surface, (box_x, box_y))

    # Draw text
    time_left_text = font.render(f"Time Left: {time_left:.2f}", True, WHITE)
    quickest_rescue_text = font.render(f"Quickest rescue: {quickest_rescue:.2f}" if quickest_rescue != float('inf') else "Quickest rescue: N/A", True, WHITE)

    surface.blit(time_left_text, (box_x + 10, box_y + 5))
    surface.blit(quickest_rescue_text, (box_x + 10, box_y + 30))

    # Draw human icons
    icon_width = 30
    total_width = icon_width * HUMAN_COUNT
    start_x = box_x + (box_width - total_width) // 2
    for i in range(HUMAN_COUNT):
        img = ui_humans[i].copy()
        if rescued_humans[i]:
            img.set_alpha(255)  # Make opaque if rescued
        surface.blit(img, (start_x + i * icon_width, box_y + 55))

# Game loop
running = True
humans_saved = 0
game_over = False
time_left = GAME_DURATION

while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and game_over:
            if event.key == pygame.K_SPACE:
                # Reset the game
                start_time = time.time()
                humans_saved = 0
                reset_humans()
                robot_rect.topleft = golden_pos
                game_over = False
                time_left = GAME_DURATION

    if not game_over:
        # Handle robot movement
        current_time_ms = pygame.time.get_ticks()
        if current_time_ms - last_move_time > move_cooldown:
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            if keys[pygame.K_LEFT]:
                dx = -TILE_SIZE
            elif keys[pygame.K_RIGHT]:
                dx = TILE_SIZE
            elif keys[pygame.K_UP]:
                dy = -TILE_SIZE
            elif keys[pygame.K_DOWN]:
                dy = TILE_SIZE

            if dx != 0 or dy != 0:
                new_x = robot_rect.x + dx
                new_y = robot_rect.y + dy
                if (0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT and
                    map_surface.get_at((new_x, new_y)) == FLOOR_COLOR):
                    robot_rect.x = new_x
                    robot_rect.y = new_y
                    last_move_time = current_time_ms

                    # Start timer on first movement
                    if start_time is None:
                        start_time = time.time()

        # Check for human rescue
        for human_index, human_rect in human_rects[:]:
            if robot_rect.colliderect(human_rect):
                human_rects.remove((human_index, human_rect))
                rescued_humans[human_index] = True
                humans_saved += 1

                if humans_saved == HUMAN_COUNT:
                    game_over = True
                    rescue_time = GAME_DURATION - time_left
                    if rescue_time < quickest_rescue:
                        quickest_rescue = rescue_time

        # Update current time and check for game over
        if start_time is not None:
            time_left = max(0, GAME_DURATION - (time.time() - start_time))
            if time_left == 0:
                game_over = True

        # Calculate viewport
        viewport_x = max(0, min(robot_rect.centerx - VIEWPORT_SIZE // 2, MAP_WIDTH - VIEWPORT_SIZE))
        viewport_y = max(0, min(robot_rect.centery - VIEWPORT_SIZE // 2, MAP_HEIGHT - VIEWPORT_SIZE))

        # Create a surface for the viewport
        viewport_surface = pygame.Surface((VIEWPORT_SIZE, VIEWPORT_SIZE))

        # Draw all elements to viewport
        viewport_surface.blit(map_surface, (0, 0), (viewport_x, viewport_y, VIEWPORT_SIZE, VIEWPORT_SIZE))
        viewport_surface.blit(robot, (robot_rect.x - viewport_x, robot_rect.y - viewport_y))
        for human_index, human_rect in human_rects:
            viewport_surface.blit(humans[human_index], (human_rect.x - viewport_x, human_rect.y - viewport_y))

        # Scale viewport to fit screen
        scaled_viewport = pygame.transform.scale(viewport_surface, (DISPLAY_WIDTH, DISPLAY_HEIGHT))

        # Draw scaled viewport to screen
        screen.blit(scaled_viewport, (0, 0))

        # Display times and human icons in box
        draw_info_box(screen, time_left, quickest_rescue, rescued_humans)

    else:
        # Game over screen
        font = pygame.font.Font(None, 40)
        if humans_saved == HUMAN_COUNT:
            text = font.render(f"All humans rescued in {GAME_DURATION - time_left:.2f} seconds!", True, WHITE)
        else:
            text = font.render(f"Time's up! {humans_saved} humans rescued.", True, WHITE)
        text_rect = text.get_rect(center=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2))
        screen.blit(text, text_rect)

        restart_font = pygame.font.Font(None, 32)
        restart_text = restart_font.render("Press SPACE to restart", True, WHITE)
        restart_rect = restart_text.get_rect(center=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2 + 50))
        screen.blit(restart_text, restart_rect)

    # Update the display
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()