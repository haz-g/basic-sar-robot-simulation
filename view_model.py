import gymnasium as gym
from stable_baselines3 import PPO
from SnrEnv import SnrEnv
import numpy as np

# Create the environment
env = gym.make('SnrEnv-v0', render_mode="human")

# Load the saved model
model = PPO.load("logs/snr_model2_20000_steps.zip")

# Run the model
obs, _ = env.reset()
for i in range(1000):  # Run for 1000 steps
    action, _states = model.predict(obs, deterministic=True)
    action = int(action)  # Convert to integer
    print(f"Model output action: {action}")
    obs, rewards, terminated, truncated, info = env.step(action)
    env.render()
    if terminated or truncated:
        obs, _ = env.reset()

env.close()