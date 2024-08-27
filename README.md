# Basic Search and Rescue Robot Simulation

A simplified Search and Rescue (SAR) robot simulation using reinforcement learning, built with Pygame and Stable Baselines 3. This project demonstrates basic RL concepts in a SAR context, serving as a foundation for more complex implementations.

## Project Overview

This project implements a basic environment where a robot agent must navigate a simplified maze to locate and rescue humans within a time limit. It uses Proximal Policy Optimization (PPO) for training the agent. The simulation provides a platform for understanding the fundamentals of applying reinforcement learning to search and rescue scenarios.

## Features

- Custom Gym environment using Pygame
- Reinforcement learning implementation with Stable Baselines 3
- Visual observation processing with frame stacking
- Custom CNN architecture for feature extraction
- Basic reward system for efficient movement and successful rescues
- TensorBoard integration for performance tracking

## Project Structure

- `SnrEnv.py`: Defines the custom Gym environment for the SAR simulation.
- `train.py`: Contains the training pipeline for the PPO agent.
- `view_model.py`: Allows visualization of a trained model's performance.
- `s_r_game.py`: Implements the core game logic and rendering.
- `search_rescue_env.py`: An alternative environment implementation (not used in main training).

## Future Work

This project serves as a stepping stone for more complex SAR robot implementations. Future work could involve:

- More realistic environment dynamics and obstacles
- Multi-agent scenarios with team coordination
- Integration with real-world robotics platforms
- Incorporation of sensor uncertainty and partial observability
- Advanced reward shaping for more nuanced behaviour

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
