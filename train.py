import SnrEnv
import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback, BaseCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
import torch
import torch.nn as nn

def make_env():
    env = gym.make('SnrEnv-v0', render_mode=None)
    env = Monitor(env)
    return env

# Create the environment
env = DummyVecEnv([make_env for _ in range(1)])
eval_env = DummyVecEnv([make_env for _ in range(1)])

class CustomCNN(BaseFeaturesExtractor):
    def __init__(self, observation_space: gym.spaces.Box, features_dim: int = 256):
        super(CustomCNN, self).__init__(observation_space, features_dim)
        n_input_channels = 9  # This should be 9
        self.cnn = nn.Sequential(
            nn.Conv2d(n_input_channels, 32, kernel_size=8, stride=4, padding=0),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=4, stride=2, padding=0),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=0),
            nn.ReLU(),
            nn.Flatten(),
        )

        # Compute shape by doing one forward pass
        with torch.no_grad():
            n_flatten = self.cnn(torch.as_tensor(observation_space.sample()[None]).float()).shape[1]

        self.linear = nn.Sequential(nn.Linear(n_flatten, features_dim), nn.ReLU())

    def forward(self, observations: torch.Tensor) -> torch.Tensor:
        return self.linear(self.cnn(observations))

policy_kwargs = dict(
    features_extractor_class=CustomCNN,
    features_extractor_kwargs=dict(features_dim=256),
)

class TensorboardCallback(BaseCallback):
    def __init__(self, verbose=0):
        super(TensorboardCallback, self).__init__(verbose)
        self.step_count = 0
    
    def _on_step(self) -> bool:
        self.step_count += 1
        if self.step_count % 900 == 0:  # Log every 1000 steps
            value = self.training_env.get_attr('humans_saved')[0]
            self.logger.record('humans_saved', value)
            print(f"Step {self.step_count}: Humans saved: {value}")
        return True

# Create the callbacks
eval_callback = EvalCallback(eval_env, best_model_save_path='./logs/',
                             log_path='./logs/', eval_freq=900,
                             deterministic=True, render=False)

checkpoint_callback = CheckpointCallback(save_freq=9000, save_path='./logs/',
                                         name_prefix='snr_model3')

callback = [checkpoint_callback, eval_callback, TensorboardCallback()]

model = PPO("CnnPolicy", env, verbose=1, tensorboard_log="./tensorboard_logs/", 
            n_steps=2048, batch_size=64, n_epochs=10, learning_rate=1e-4, 
            policy_kwargs=policy_kwargs, ent_coef=0.015)

# Train the agent
model.learn(total_timesteps=1000000, callback=callback)

# Save the final trained model
model.save("ppo_search_rescue_final")

env.close()