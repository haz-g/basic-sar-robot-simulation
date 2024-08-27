import gymnasium as gym
from gymnasium import spaces
import cv2
import numpy as np
import pygame
import random

class SnrEnv(gym.Env):
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 30}

    def __init__(self, render_mode=None, GAME_DURATION=30):
        super().__init__()
        pygame.init()

        # Game constants
        self.render_mode = render_mode
        self.MAP_WIDTH, self.MAP_HEIGHT = 580, 420
        self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT = 750, 750
        self.VIEWPORT_SIZE = 100
        self.SCALE_FACTOR = self.DISPLAY_WIDTH // self.VIEWPORT_SIZE
        self.TILE_SIZE = 20
        self.FPS = 30
        self.HUMAN_COUNT = 3
        self.GAME_DURATION = GAME_DURATION
        self.BLACK, self.WHITE = (0, 0, 0), (255, 255, 255)
        self.FLOOR_COLOR, self.GOLD = (45, 26, 43), (74, 50, 50)

        # Load and process images
        self.map = pygame.image.load('map.png')
        self.robot = pygame.image.load('robot.png')
        self.humans = [pygame.image.load(f'human_{i}.png') for i in range(1, 4)]
        self.robot.set_colorkey(self.BLACK)
        for img in self.humans:
            img.set_colorkey(self.BLACK)

        # Set up display
        if render_mode is None:
            pygame.display.set_mode((1, 1), pygame.NOFRAME)
        else:
            self.screen = pygame.display.set_mode((self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT))

        # Create map surface
        self.map_surface = pygame.Surface((self.MAP_WIDTH, self.MAP_HEIGHT))
        self.map_surface.blit(self.map, (0, 0))

        # Find floor and starting positions
        self.floor_positions = self._get_floor_positions()
        self.golden_pos = self._get_golden_position()
        self.path = self.floor_positions + [self.golden_pos]

        # Set up game objects
        self.robot_rect = self.robot.get_rect()
        self.robot_rect.topleft = self.golden_pos
        self.human_rects = []
        self.rescued_humans = [False] * self.HUMAN_COUNT
        self.spotted_humans = [False] * self.HUMAN_COUNT

        # Game state variables
        self.clock = pygame.time.Clock()
        self.quickest_rescue = float('inf')
        self.running = True
        self.humans_saved = 0
        self.game_over = False
        self.time_left = self.GAME_DURATION

        self.set_humans()

        # Define observation and action spaces
        self.observation_space = spaces.Box(low=0, high=255, shape=(84, 84, 9), dtype=np.uint8)
        self.frame_stack = np.zeros((84, 84, 3 * 3), dtype=np.uint8) 
        self.action_space = spaces.Discrete(4)  # 0: Up, 1: Right, 2: Down, 3: Left

    def _get_floor_positions(self):
        positions = []
        for x in range(0, self.MAP_WIDTH, self.TILE_SIZE):
            for y in range(0, self.MAP_HEIGHT, self.TILE_SIZE):
                if self.map_surface.get_at((x, y)) == self.FLOOR_COLOR:
                    positions.append((x, y))
        return positions

    def _get_golden_position(self):
        for x in range(0, self.MAP_WIDTH, self.TILE_SIZE):
            for y in range(0, self.MAP_HEIGHT, self.TILE_SIZE):
                if self.map_surface.get_at((x, y)) == self.GOLD:
                    return (x, y)
        return None

    def render_game_state(self, surface):
        # Calculate viewport
        viewport_x = max(0, min(self.robot_rect.centerx - self.VIEWPORT_SIZE // 2, self.MAP_WIDTH - self.VIEWPORT_SIZE))
        viewport_y = max(0, min(self.robot_rect.centery - self.VIEWPORT_SIZE // 2, self.MAP_HEIGHT - self.VIEWPORT_SIZE))
        viewport_surface = pygame.Surface((self.VIEWPORT_SIZE, self.VIEWPORT_SIZE))

        # Draw map, robot, and humans
        viewport_surface.blit(self.map_surface, (0, 0), (viewport_x, viewport_y, self.VIEWPORT_SIZE, self.VIEWPORT_SIZE))
        viewport_surface.blit(self.robot, (self.robot_rect.x - viewport_x, self.robot_rect.y - viewport_y))
        for human_index, human_rect in self.human_rects:
            viewport_surface.blit(self.humans[human_index], (human_rect.x - viewport_x, human_rect.y - viewport_y))

        # Scale and blit to main surface
        scaled_viewport = pygame.transform.scale(viewport_surface, (self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT))
        surface.blit(scaled_viewport, (0, 0))

    def get_rgb_observation(self):
        surface = pygame.Surface((self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT))
        self.render_game_state(surface)
        obs = pygame.surfarray.array3d(surface)
        obs = obs.transpose((1, 0, 2))
        obs = cv2.resize(obs, (84, 84), interpolation=cv2.INTER_AREA)
        return obs

    def get_observation(self):
        new_frame = self.get_rgb_observation()
        self.frame_stack = np.roll(self.frame_stack, shift=-3, axis=2)
        self.frame_stack[:, :, -3:] = new_frame
        return self.frame_stack

    def human_visibility(self, human_rect):
        distance = ((self.robot_rect.topleft[0] - human_rect[0])**2 + 
                    (self.robot_rect.topleft[1] - human_rect[1])**2)**0.5
        return max(0, 1 - (distance / self.VIEWPORT_SIZE))

    def set_humans(self):
        self.human_rects = []
        available_positions = self.floor_positions.copy()
        for i in range(self.HUMAN_COUNT):
            if available_positions:
                pos = random.choice(available_positions)
                available_positions.remove(pos)
                human_rect = self.humans[i].get_rect()
                human_rect.topleft = pos
                self.human_rects.append((i, human_rect))

    def render(self):
        if self.render_mode is None:
            return

        if self.render_mode == "human":
            if not hasattr(self, 'screen'):
                self.screen = pygame.display.set_mode((self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT))

            surface = pygame.Surface((self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT))
            self.render_game_state(surface)
            self.screen.blit(surface, (0, 0))
            pygame.display.flip()
            return None
        elif self.render_mode == "rgb_array":
            return self.get_rgb_observation()

    def step(self, action):
        done = False
        reward = -0.01  # Base reward

        # Move the agent
        dx, dy = {0: (0, -self.TILE_SIZE), 1: (self.TILE_SIZE, 0),
                  2: (0, self.TILE_SIZE), 3: (-self.TILE_SIZE, 0)}[action]
        new_x, new_y = self.robot_rect.x + dx, self.robot_rect.y + dy

        # Check if the new position is valid
        if (new_x, new_y) in self.path:
            self.robot_rect.x, self.robot_rect.y = new_x, new_y
            reward += 0.1  # Small reward for valid move
        else:
            reward -= 0.2  # Penalty for invalid move

        self.time_left -= 1 / self.FPS

        # Check for spotted and rescued humans
        for i, (_, human_rect) in enumerate(self.human_rects):
            proximity_score = self.human_visibility(human_rect)
            if proximity_score > 0:
                if not self.spotted_humans[i]:
                    reward += 0.5  # Reward for spotting a human for the first time
                    self.spotted_humans[i] = True
                reward += proximity_score * 0.5  # Reward based on proximity

            if self.robot_rect.colliderect(human_rect) and not self.rescued_humans[i]:
                self.rescued_humans[i] = True
                self.humans_saved += 1
                reward += 10.0  # Large reward for rescuing a human

        # Check if the game is over
        if self.humans_saved == self.HUMAN_COUNT or self.time_left <= 0:
            done = True
            time_factor = self.time_left / self.GAME_DURATION

            # Progressive reward for each human saved
            for i in range(self.humans_saved):
                reward += 5.0 ** (i + 1)

            if self.humans_saved == self.HUMAN_COUNT:
                reward += 25.0  # Big bonus for rescuing all humans
            elif self.humans_saved == 0:
                reward -= 20.0  # Penalty for not rescuing anyone

        obs = self.get_observation()
        info = {'humans_saved': self.humans_saved, 'time_left': self.time_left}

        return obs, reward, done, False, info

    def reset(self, seed=None, options=None):    
        # Reset game variables
        self.humans_saved = 0
        self.game_over = False
        self.time_left = self.GAME_DURATION
        self.rescued_humans = [False] * self.HUMAN_COUNT
        self.spotted_humans = [False] * self.HUMAN_COUNT
        self.robot_rect.topleft = self.golden_pos
        self.set_humans()

        initial_obs = self.get_rgb_observation()
        self.frame_stack = np.repeat(initial_obs, 3, axis=2)

        return self.frame_stack, {}

    def close(self):
        if self.screen is not None:
            pygame.display.quit()
            pygame.quit()

# Register the environment
from gymnasium.envs.registration import register
register(id='SnrEnv-v0', entry_point='SnrEnv:SnrEnv')