import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pygame
import random

class SearchRescueEnv(gym.Env):
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 30}

    def __init__(self):
        super(SearchRescueEnv, self).__init__()

        # Initialize Pygame
        pygame.init()

        # Constants
        self.MAP_WIDTH, self.MAP_HEIGHT = 580, 420
        self.TILE_SIZE = 20
        self.HUMAN_COUNT = 3
        self.GAME_DURATION = 30  # 30 seconds countdown

        # Colors
        self.FLOOR_COLOR = (45, 26, 43)
        self.GOLD = (74, 50, 50)

        # Load and process images
        self.map_img = pygame.image.load('map.png')
        self.robot_img = pygame.image.load('robot.png')
        self.human_imgs = [pygame.image.load(f'human_{i}.png') for i in range(1, 4)]

        # Remove black backgrounds and scale images
        self.robot_img.set_colorkey((0, 0, 0))
        self.robot_img = pygame.transform.scale(self.robot_img, (self.TILE_SIZE, self.TILE_SIZE))
        for img in self.human_imgs:
            img.set_colorkey((0, 0, 0))
            pygame.transform.scale(img, (self.TILE_SIZE, self.TILE_SIZE))

        # Create map surface
        self.map_surface = pygame.Surface((self.MAP_WIDTH, self.MAP_HEIGHT))
        self.map_surface.blit(self.map_img, (0, 0))

        # Find valid floor positions and golden square
        self.floor_positions = []
        self.golden_pos = None
        for x in range(0, self.MAP_WIDTH, self.TILE_SIZE):
            for y in range(0, self.MAP_HEIGHT, self.TILE_SIZE):
                if self.map_surface.get_at((x, y)) == self.FLOOR_COLOR:
                    self.floor_positions.append((x, y))
                elif self.map_surface.get_at((x, y)) == self.GOLD:
                    self.golden_pos = (x, y)

        # Define action and observation space
        self.action_space = spaces.Discrete(4)  # Up, Right, Down, Left
        
        # Observation space: robot position (2), human positions (3*2), time left (1)
        self.observation_space = spaces.Box(low=0, high=max(self.MAP_WIDTH, self.MAP_HEIGHT), 
                                            shape=(9,), dtype=np.float32)

        # Initialize state
        self.robot_pos = None
        self.human_positions = []
        self.rescued_humans = []
        self.time_left = self.GAME_DURATION
        self.humans_saved = 0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.robot_pos = self.golden_pos
        self.human_positions = []
        self.rescued_humans = [False] * self.HUMAN_COUNT
        self.time_left = self.GAME_DURATION
        self.humans_saved = 0

        # Place humans
        available_positions = self.floor_positions.copy()
        for _ in range(self.HUMAN_COUNT):
            if available_positions:
                pos = random.choice(available_positions)
                available_positions.remove(pos)
                self.human_positions.append(pos)

        return self._get_obs(), {}  # Return observation and an empty info dict

    def step(self, action):
        # Move robot
        dx, dy = {0: (0, -self.TILE_SIZE), 1: (self.TILE_SIZE, 0), 
                  2: (0, self.TILE_SIZE), 3: (-self.TILE_SIZE, 0)}[action]
        new_x = self.robot_pos[0] + dx
        new_y = self.robot_pos[1] + dy

        if (0 <= new_x < self.MAP_WIDTH and 0 <= new_y < self.MAP_HEIGHT and
            self.map_surface.get_at((new_x, new_y)) == self.FLOOR_COLOR):
            self.robot_pos = (new_x, new_y)

        # Check for human rescue
        for i, human_pos in enumerate(self.human_positions):
            if self.robot_pos == human_pos and not self.rescued_humans[i]:
                self.rescued_humans[i] = True
                self.humans_saved += 1

        # Update time
        self.time_left -= 1/30  # Assuming 30 FPS

        # Check for done condition
        done = self.humans_saved == self.HUMAN_COUNT or self.time_left <= 0

        # Calculate reward
        reward = 0
        if self.humans_saved == self.HUMAN_COUNT:
            reward = 100  # Big reward for rescuing all humans
        elif done:
            reward = -10  # Penalty for running out of time
        reward += self.humans_saved  # Small reward for each human saved

        return self._get_obs(), reward, done, False, {} 

    def _get_obs(self):
        obs = [self.robot_pos[0], self.robot_pos[1]]
        for i in range(self.HUMAN_COUNT):
            if i < len(self.human_positions) and not self.rescued_humans[i]:
                obs.extend(self.human_positions[i])
            else:
                obs.extend([-1, -1])  # Use -1 to indicate rescued or non-existent humans
        obs.append(self.time_left)
        return np.array(obs, dtype=np.float32)
    
    def render(self, mode='human'):
        pass

    def close(self):
        if hasattr(self, 'screen'):
            pygame.quit()

from gymnasium.envs.registration import register

register(
    id='SearchRescue-v0',
    entry_point='search_rescue_env:SearchRescueEnv',
)