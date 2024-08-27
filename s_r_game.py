import pygame
import random
import time

# Initialize Pygame - the code below calls the "init" method in the pygame module. Note, this is not the same as
# the __innit___ method. What running this method does is essentially initialise all other methods in the pygame
# module/package. Likely giving them each some arbitrary initial value to be updated by our game.
pygame.init()

# Constants - Here we are defining important constants to be used elsewhere in our code, python has a technique where
# you can define multiple variables on the same line using commas. I've included colours into the constants because it
# makes sense I personally think.
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

# Load images - this is an important step and essentially tells the pygame module what images we're working with. It calls
# a method .load() to a method .image of pygame, likely doing some kind of data loading of the images to memory? Not too sure
# we're also assigning whatever this image returns (it must therefore return something!) to the variable names stated. Interestingly
# we're storing the data returned as a list for the humans images.
map = pygame.image.load('map.png')
robot = pygame.image.load('robot.png')
humans = [pygame.image.load(f'human_{i}.png') for i in range(1, 4)]

# Remove black backgrounds - this calls a method on both each pygame.image.load() method initialised in the code chunk above
# This method (or method (.set_colorkey) of a method (.load) of a method? (.image) of a module (pygame)) "keys out" whatever
# coloured pixels we pass into it from the image data specified and replaces it with transparent values.
robot.set_colorkey(BLACK)
for img in humans:
    img.set_colorkey(BLACK)

# Create small semi-transparent versions of human images for UI - okay here we're just taking the human images and making new semi
# transparent images from them for the display UI
ui_humans = []
for img in humans:
    small_img = pygame.transform.scale(img, (30, 30))
    small_img.set_alpha(128)  # Set semi-transparent
    ui_humans.append(small_img)

# Create the game window - does what it says on the tin, this is the game window we interact with so 750x750.
screen = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
pygame.display.set_caption("Search and Rescue Robot Game")

# Create a surface for the entire map - this creares a new pygame surface to be blitted on to. This is important in pygame
# since we can't just throw in images arbitrarily they must be attached to something and in Pygame it is the surface.
# first we have to define the surface and we want it to be the same dimension as our image which we're then "blitting"
# which just means "pasting" to this surface, from it's upper leftmost position (0,0) this means, our images upper left corner
# will be blitted to the surface's upper left corner, if it wasn't "(0,0)" the image might be displaced on the surface.
map_surface = pygame.Surface((MAP_WIDTH, MAP_HEIGHT))
map_surface.blit(map, (0, 0))

# Find valid floor positions - here we're creating an empty list, and then for all pixels across the width and height of the
# map surface (our blitted map image), we're checking its colour to see if it matches the floor colour and we're checking
# pixels in steps of 20 which denotes our tile size. So these for loops essentially call the .get_at() method of the  pygame.Surface()
# method. this likely tells us the colour value of that pixel at that point. The for loops by starting at the top left position
# and essentially scanning "down" each 20 pixel step row along the top row of pixels of the image, stopping for each column and scanning
# down in steps of 20 too. anytime it finds a colour matching our previously defined FLOOR_COLOR variable we add it to the list by appending
# to floor_positions. This will be important to know later when we're doing our physics collisions as it essentially maps out
# everywhere the agent can move.
floor_positions = []
for x in range(0, MAP_WIDTH, TILE_SIZE):
    for y in range(0, MAP_HEIGHT, TILE_SIZE):
        if map_surface.get_at((x, y)) == FLOOR_COLOR:
            floor_positions.append((x, y))

# Find the golden square position - this does a similar thing to the above loop but this time looks for the starting position
# defined as "golden_pos" i think the second if statement is to ensure no double counting perhaps? It assigns its answer, to golden_pos.
golden_pos = None
for x in range(0, MAP_WIDTH, TILE_SIZE):
    for y in range(0, MAP_HEIGHT, TILE_SIZE):
        if map_surface.get_at((x, y)) == GOLD:
            golden_pos = (x, y)
            break
    if golden_pos:
        break

# Set up the robot - okay here we're building a rect which is essentially a rectangle super imposed over our image and its useful
# for handling collision logic in pygame. we're then pinning this rectanlge's top left edge to our golden_pos which makes sense based
# on how we defined our searching for golden loop
robot_rect = robot.get_rect()
robot_rect.topleft = golden_pos

# Set up the humans - here we're creating an empty loop likely to be used in the function below and then, interestingly we're creating 
# a list where we essentially have "False" for every entry written as many times as we have humans. Presumably the first acts to contain
# information of each of the recetanlgles we will created for our humans and the second acts to keep track of capture for each of our humans too.
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

# The above function when called (as below) asks for know parameters but essentially imports the global definitions of "human_rects", "rescued_humans"
# this is likely an initialisation stage for each new episodes so human_rects are emptied and rescued humans are reset to effectively "none"
# then it re-defines them in the same way again (is this not a redundant step or is this some kind of fail safe?) before creating
# a new variable denoted as "available_positions" which is essentially a copy of the floor position list which itself, tells us the upper left hand corner
# coordinates for all available path tiles in the maze environment. we then iterate three times over the if statement "if available_positions:"
# this is an interesting if statement it's essentially saying if "list" which i think would just return True? since there's entries in the list. But not sure
# anyways what it then does is selects randomly from the list to extract one tuple of valid x,y coordinates, creates a rect for a specific human
# appends the rect's topleft side to the selected pixel position and then adds this position to the human rects list as a tuple contain the human number
# and the human_rect which i'm not sure what that returns as a value perhaps the position
reset_humans()

# Set up timing - this is just introducing a game clock into the pygame environment to track time. We also define too variables, the start time which is set
# to "None" - not entirely sure what that means. and then the "quickest_rescue" variable is being set to infinite
clock = pygame.time.Clock()
start_time = None
quickest_rescue = float('inf')

# Movement cooldown - i'm not sure what these variables do, perhaps the function defined below will reveal. Nope it didn't these seem to be
# variables used in the frame loop wihtin the game itself. When i read that i will likely understand this better.
last_move_time = 0
move_cooldown = 100  # milliseconds

# Function to draw time box and human icons - so this function basically allows us to create a box in the game for which we dynamically pass
# in and update information about (time left, quickest rescue and rescued humans etc.) this then causes either the text to dynamically update
# or the humans to turn opaque. Clearly it expects a list from the rescued_humans parameter denoting each human so the correct one
# can be made opaque.
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

# Game loop - the variables below initiate some values for our loop, like when to kill the game, the starting time left, starting
# number of humans saved and so on.
running = True
humans_saved = 0
game_over = False
time_left = GAME_DURATION  # Initialize time_left here

while running:
# while running is essentially an infinite loop of "while True" since running is initiaited to "True"
# when we talk about the events in the pygame method "event.get()" we're essentially reading off data that gets recorded
# and returned by pygame which likely handles all the processing of our keys and mouse clicks. Here we're essentially tapping
# into this data stream a bit like topics in ROS. if we find that the event returned has type pygame.QUIT we know the user
# has essentially asked to quit the game likely by clicking exit on the window, so we know to stop running and make running = False
# to break the loop. Otherwise we're looking to see essentially when the game_over variable evaluates to True and we're pressing any key 
# then resetting the game including all the variables defined above and the function to reset human positions randomly.
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
                time_left = GAME_DURATION  # Reset time_left here

# if not game_over essentially reads as if True until game_over variabel is changed to false. So this will essentially run whilst
# in play and not when the game is finished. We've likely introduced this functionality because the game has a end screen where the 
# player can take a second before clicking space bar to reset. In any case what this does whilst the game is running is check how long
# has passed in millisecond since the last call and assigning that to the current_time_ms. We're looking at whether. It then evaluates
# if this is greater thant the move_cooldown allowed and if so updates the robot's position by the key clicked converted into a pixel
# delta to denote the movement dynamics it then ensures that the tile coordinates to be transitioned to is both within the game map
# width and height and within the allowed path coordinates, it only moves the robot if this is satisfied. then it updates start_time variable
# i'm not sure what that achieves though.
    if not game_over:
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

        # Check for human rescue - okay i'm not entirely sure what the square brackets and colon refers to for the human_rects list but
        # this is out list from earlier which contains the positions we set for our humans when we randomly placed them as well as who was
        # placed where (their index) and what it does is looks at whether the top left of our robot_rect rectangle has overlapped with the top
        # left of one of the human rectangles. If it does it removes that human from the game, updates the False value within the rescued_humans
        # for the relecvent human and sets it to True which makes it opague in the display box and then updates the humans_saved count
        # when this count reachers 3 the game is stopped and rescue time recorded and high score possibly overwritten but always overwritten on the first
        # succesful run from the intiial value of float('int')
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

        # Update current time and check for game over - so this begins by checking that start_time is not None and has a value
        # attributed to it that we can use for calculations. My understanding is that upon our first movement we're initialising the
        # start_time to our time.time() method which essentially returns the time elapsed in this episode. So we can calculate the time_left
        # but taking the max between 0 (so it stops naturally at 0 instead of going negative) and 30 - (time epalsed -...hmm in trying to
        # write this out i've realised my explanation is off. What i think is happening is that in order to dynamically update time left
        # we're subtracting from 30 the ever increasing difference between the time elapsed and the time at the start? I'm not sure why we'd
        # do this though and not just subtract time surpassed i.e. time.time() itself. Perhaps you can elaborate.
        if start_time is not None:
            time_left = max(0, GAME_DURATION - (time.time() - start_time))
            if time_left == 0:
                game_over = True

        # Calculate viewport - here we're simply setting variables for viewport x and y positions which takes the max between 0 and the min between
        # the centre coordinate values of the robot's rect minus the viewport size and the map width minus viewport size. I'm not sure why
        # or what this does or is useful for to be honest!
        viewport_x = max(0, min(robot_rect.centerx - VIEWPORT_SIZE // 2, MAP_WIDTH - VIEWPORT_SIZE))
        viewport_y = max(0, min(robot_rect.centery - VIEWPORT_SIZE // 2, MAP_HEIGHT - VIEWPORT_SIZE))

        # Create a surface for the viewport - this creates a new viewport surface of size 100x100 pixels
        viewport_surface = pygame.Surface((VIEWPORT_SIZE, VIEWPORT_SIZE))

        # Draw all elements to to viewport - this blits the map, robot and humans to this surface as the cordinate values passed
        # in and also does some scaling? OR no? Hmm maybe this and the above handles the movement of the map on the surface. Would
        # be nice if you could explain this a bit
        viewport_surface.blit(map_surface, (0, 0), (viewport_x, viewport_y, VIEWPORT_SIZE, VIEWPORT_SIZE))
        viewport_surface.blit(robot, (robot_rect.x - viewport_x, robot_rect.y - viewport_y))
        for human_index, human_rect in human_rects:
            viewport_surface.blit(humans[human_index], (human_rect.x - viewport_x, human_rect.y - viewport_y))

        # Scale viewport to fit screen - oh no i think this does the scaling!
        scaled_viewport = pygame.transform.scale(viewport_surface, (DISPLAY_WIDTH, DISPLAY_HEIGHT))

        # Draw scaled viewport to screen - okay, so it's one thing to create this new surface and scale it but we then also have to blit it to 
        # our main screen surface which is what the below does
        screen.blit(scaled_viewport, (0, 0))

        # Display times and human icons in box - finally we superimpose our info box on the game.
        draw_info_box(screen, time_left, quickest_rescue, rescued_humans)

    else:
        # Game over screen - simply this is displayed first when game over evaluates to True so the aplication doesn't quite or auto
        # restart when that happens. The below just is the formatting and dynamic display of variables (data) collected from the most
        # recent run
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

# perhaps the most important part, this actually calls the update to display the new information on the screen and then below defines
# how many times we do that per second. which for this game we defined as 30
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()