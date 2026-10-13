# Tutorial: Creating a Custom PACE Environment and Identifying Parameters

## Overview

This tutorial explains how to set up a custom robot environment within the **PACE (Precise Adaptation through Continuous Evolution)** framework in order to estimate the dynamics of your system through evolutionary parameter identification.

We will walk through the full pipeline, from defining your environment and actuators, to designing excitation trajectories and running the CMA-ES-based optimization. For clarity and consistency, the examples below use **ANYmal** as the reference robot. When adapting this tutorial to your own platform, simply replace occurrences of `anymal` with your robot's name and adjust the corresponding parameters.

The tutorial covers:

* Creating and configuring a PACE environment
* Defining actuator models and optimization boundaries
* Registering the environment with IsaacLab
* Designing excitation trajectories
* Running evolutionary parameter fitting
* Inspecting and comparing optimization results

---

## Creating the Environment

The core of the PACE framework is the definition and registration of a task-specific simulation environment. This environment specifies the robot configuration, its actuators, and the parameter ranges used during system identification.

The reference implementation for ANYmal can be found at:

```
pace-sim2real/source/pace_sim2real/pace_sim2real/tasks/manager_based/pace/anymal_pace_env_cfg.py
```

This file provides the complete configuration of the robotic system and its associated PACE parameters.

```python
from isaaclab.utils import configclass

from isaaclab_assets.robots.anymal import ANYMAL_D_CFG
from isaaclab.assets import ArticulationCfg
from pace_sim2real.utils import PaceDCMotorCfg
from pace_sim2real import PaceSim2realEnvCfg, PaceSim2realSceneCfg, PaceCfg
import torch

ANYDRIVE_PACE_ACTUATOR_CFG = PaceDCMotorCfg(
    joint_names_expr=[".*HAA", ".*HFE", ".*KFE"],
    saturation_effort=140.0,
    effort_limit=89.0,
    velocity_limit=8.5,
    stiffness={".*": 85.0},  # P gain in Nm/rad
    damping={".*": 0.6},  # D gain in Nm s/rad
    encoder_bias={".*": 0.0},  # encoder bias in radians
    # note: modeling coulomb friction if friction = dynamic_friction
    # > in newer Isaac Sim versions, friction is renamed to static_friction
    friction={".*": 0.0},  # static friction coefficient (Nm)
    dynamic_friction={".*": 0.0},  # dynamic friction coefficient (Nm)
    viscous_friction={".*": 0.0},  # viscous friction coefficient (Nm s/rad)
    max_delay=10,  # max delay in simulation steps
)


@configclass
class AnymalDPaceCfg(PaceCfg):
    """Pace configuration for Anymal-D robot."""
    robot_name: str = "anymal_d_sim"
    data_dir: str = "anymal_d_sim/chirp_data.pt"  # located in pace_sim2real/data/anymal_d_sim/chirp_data.pt
    bounds_params: torch.Tensor = torch.zeros((49, 2))  # 12 + 12 + 12 + 12 + 1 = 49 parameters to optimize
    separate_dynamic_friction: bool = True  # appends 12 dynamic/static friction ratios -> 61 parameters
    joint_order: list[str] = [
        "LF_HAA",
        "LF_HFE",
        "LF_KFE",
        "RF_HAA",
        "RF_HFE",
        "RF_KFE",
        "LH_HAA",
        "LH_HFE",
        "LH_KFE",
        "RH_HAA",
        "RH_HFE",
        "RH_KFE",
    ]

    def __post_init__(self):
        # set bounds for parameters
        self.bounds_params[:12, 0] = 1e-5
        self.bounds_params[:12, 1] = 1.0  # armature between 1e-5 - 1.0 [kgm2]
        self.bounds_params[12:24, 1] = 7.0  # dof_damping between 0.0 - 7.0 [Nm s/rad]
        self.bounds_params[24:36, 1] = 0.5  # friction between 0.0 - 0.5
        self.bounds_params[36:48, 0] = -0.1
        self.bounds_params[36:48, 1] = 0.1  # bias between -0.1 - 0.1 [rad]
        self.bounds_params[48, 1] = 10.0  # delay between 0.0 - 10.0 [sim steps]


@configclass
class ANYmalDPaceSceneCfg(PaceSim2realSceneCfg):
    """Configuration for Anymal-D robot in Pace Sim2Real environment."""
    robot: ArticulationCfg = ANYMAL_D_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot", init_state=ArticulationCfg.InitialStateCfg(pos=(0.0, 0.0, 1.0)),
                                                  actuators={"legs": ANYDRIVE_PACE_ACTUATOR_CFG})


@configclass
class AnymalDPaceEnvCfg(PaceSim2realEnvCfg):

    scene: ANYmalDPaceSceneCfg = ANYmalDPaceSceneCfg()
    sim2real: PaceCfg = AnymalDPaceCfg()

    def __post_init__(self):
        # post init of parent
        super().__post_init__()

        # robot sim and control settings
        self.sim.dt = 0.0025  # 400Hz simulation
        self.decimation = 1  # 400Hz control
```

The custom environment consists of:

* The robot model and its actuators
* The optimization parameter bounds for CMA-ES
* PACE-specific configuration linking simulation and real-world data

The following sections describe each component in detail.

---

## Creating the PACE DC Motors

```python
ANYDRIVE_PACE_ACTUATOR_CFG = PaceDCMotorCfg(
    joint_names_expr=[".*HAA", ".*HFE", ".*KFE"],
    saturation_effort=140.0,
    effort_limit=89.0,
    velocity_limit=8.5,
    stiffness={".*": 85.0},
    damping={".*": 0.6},
    encoder_bias={".*": 0.0},
    max_delay=10,
)
```

ANYmal uses a single drive type, but your robot may employ multiple actuator variants. In such cases, create one `PaceDCMotorCfg` per actuator type and associate the corresponding joints via `joint_names_expr`.

Key parameters include:

* `saturation_effort`: peak torque capability
* `effort_limit`: hardware-imposed torque limit
* `velocity_limit`: maximum joint velocity
* `stiffness` and `damping`: internal PD gains used by the real actuator
* `encoder_bias`: initial bias estimate (set to zero initially)
* `max_delay`: maximum expected actuator delay in simulation steps
* `delay_mode`: where the delay acts (defaults to `"command"`)
    * `"command"`: the position/velocity targets and feed-forward torques reach the drive late, while the PD controller runs on the current measurements. This matches drives with their own low-level control loop and stays stable for large delays.
    * `"effort"`: the torque computed from the current measurements is applied late, i.e. the feedback itself is delayed. This was the behavior before v0.2.0 and can be used to reproduce earlier results.

!!! note "Delay implementation before v0.2.0"
    The paper describes a delay of the commands, but versions before v0.2.0 delayed the computed torque. The results in the paper were obtained with this previous implementation, which corresponds to `delay_mode = "effort"`. Use it to reproduce the paper or earlier identification results.

If your robot uses a specialized actuator model, you can extend `PaceDCMotorCfg` by inheriting from your custom class and augmenting it with delay and encoder bias functionality.

---

## Defining PACE specific configs

```python
@configclass
class AnymalDPaceCfg(PaceCfg):
    ...
```

The `AnymalDPaceCfg` block defines algorithmic parameters and data linkage:

* `robot_name`: determines logging directory
* `data_dir`: path to recorded trajectory data
* `joint_order`: alignment with real data
* `bounds_params`: optimization limits
* `separate_dynamic_friction`: identify static and dynamic friction separately (defaults to `False`, i.e. Coulomb friction with static = dynamic)
* `friction_ratio_bounds`: bounds of the dynamic to static friction ratio (defaults to `(0.0, 1.0)`)

Optional CMA-ES settings (iterations, sigma, epsilon, logging frequency) can also be configured here.

IsaacLab determines joint ordering via breadth-first traversal, which may differ from the ordering used in your real robot’s control stack or logged data. To ensure correct alignment between simulated and real trajectories, explicitly define the joint order used on your physical system here.

PACE normalizes optimization parameters to the range [-1, 1]. However, the physically meaningful parameter limits are defined via `bounds_params`, which constrains the sampling domain of the CMA-ES optimizer.

The parameters are laid out as:

* Armature: `[0 : n_joints]`
* Viscous friction: `[n_joints : 2*n_joints]`
* Static friction: `[2*n_joints : 3*n_joints]`
* Encoder bias: `[3*n_joints : 4*n_joints]`
* Global delay: `[4*n_joints]`
* Dynamic to static friction ratio: `[4*n_joints + 1 : 5*n_joints + 1]` (only with `separate_dynamic_friction = True`)

You only define the bounds of the first `4*n_joints + 1` parameters. If `separate_dynamic_friction` is enabled, the ratio bounds are appended automatically from `friction_ratio_bounds`. The dynamic friction is then `ratio * static friction`, so it never exceeds the static friction.

```python
def __post_init__(self):
        # set bounds for parameters
        ...
```

The values should be chosen conservatively based on hardware knowledge or prior estimates, and can be refined iteratively as needed.

---

## Creating the Scene

```python
@configclass
class ANYmalDPaceSceneCfg(PaceSim2realSceneCfg):
    ...
```

Here, you inherit from `PaceSim2realSceneCfg` and specify your robot USD, initial pose, and associated actuators. Ensure the initial height prevents ground penetration or unwanted contacts. Actuator naming is flexible and purely user-defined.

---

## Registering the Environment

To expose the environment to the optimization pipeline, it must be registered within IsaacLab’s task registry:

```
pace-sim2real/source/pace_sim2real/pace_sim2real/tasks/manager_based/__init__.py
```

Following the naming convention `Isaac-Pace-<robot>-v0`:

```python
gym.register(
    id="Isaac-Pace-Anymal-D-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.pace.anymal_pace_env_cfg:AnymalDPaceEnvCfg"
    },
)
```

---

## Designing the Excitation Trajectory

Well-designed trajectories are critical for accurate parameter estimation. PACE provides a script to prototype and validate trajectories before deployment on real hardware:

```
pace-sim2real/scripts/pace/data_collection.py
```

The following section temporarily injects example parameters for testing and can be omitted.

```python
armature = torch.tensor([0.1] * len(joint_ids), device=env.unwrapped.device).unsqueeze(0)
damping = torch.tensor([4.5] * len(joint_ids), device=env.unwrapped.device).unsqueeze(0)
friction = torch.tensor([0.05] * len(joint_ids), device=env.unwrapped.device).unsqueeze(0)
dynamic_friction = 0.5 * friction
bias = torch.tensor([0.05] * 12, device=env.unwrapped.device).unsqueeze(0)
time_lag = torch.tensor([[5]], dtype=torch.int, device=env.unwrapped.device)
```

Trajectory design is controlled through:

* `trajectory_direction`: symmetric joint motion to cancel base forces
* `trajectory_bias`: center of oscillation
* `trajectory_scale`: oscillation amplitude

```python
duration = args_cli.duration  # seconds
sample_rate = 1 / env.unwrapped.sim.get_physics_dt()  # Hz
num_steps = int(duration * sample_rate)
t = torch.linspace(0, duration, steps=num_steps, device=env.unwrapped.device)
f0 = args_cli.min_frequency  # Hz
f1 = args_cli.max_frequency  # Hz

# Linear chirp: phase = 2*pi*(f0*t + (f1-f0)/(2*duration)*t^2)
phase = 2 * pi * (f0 * t + ((f1 - f0) / (2 * duration)) * t ** 2)
chirp_signal = torch.sin(phase)

trajectory = torch.zeros((num_steps, len(joint_ids)), device=env.unwrapped.device)
trajectory[:, :] = chirp_signal.unsqueeze(-1)
trajectory_directions = torch.tensor(
    [1.0, 1.0, 1.0, -1.0, 1.0, 1.0, 1.0, -1.0, -1.0, -1.0, -1.0, -1.0],
    device=env.unwrapped.device
)
trajectory_bias = torch.tensor(
    [0.0, 0.4, 0.8] * 4,
    device=env.unwrapped.device
)
trajectory_scale = torch.tensor(
    [0.25, 0.5, -2.0] * 4,
    device=env.unwrapped.device
)
trajectory[:, joint_ids] = (trajectory[:, joint_ids] + trajectory_bias.unsqueeze(0)) * trajectory_directions.unsqueeze(0) * trajectory_scale.unsqueeze(0)
```

While chirp-based signals provide a practical baseline, more advanced trajectory optimization approaches may further improve system identification quality.

---

## Evolutionary Parameter Fitting

Once data collection is complete and stored in the correct directory, launch the optimization using:

```bash
cd ~/pace-sim2real
python scripts/pace/fit.py --headless --num_envs=4096 --task=Isaac-Pace-Anymal-D-v0
```

This process utilizes the `CMAESOptimizer` located at:

```
pace-sim2real/source/pace_sim2real/pace_sim2real/optim/cma_es.py
```

---

## Logging and Optimization Inspection

All optimization logs are stored under:

```
pace-sim2real/logs/pace/anymal_d_sim
```

Key files include:

* `config.pt`: full configuration and dataset metadata
* `best_trajectory.pt`: best simulated joint trajectory
* `mean_xxx.pt`: mean parameter estimates per iteration

If logging of the full optimization process is enabled:

```python
save_optimization_process = True
```

Additional files include:

* `progress.pt`: best scores and complete parameter history over the iterations

---

## Comparing Trajectories

During or after optimization, visualize the current best trajectory using:

```bash
python scripts/pace/plot_trajectory.py --plot_trajectory --robot_name=anymal_d_sim
```

After completion, include `--plot_score` to visualize convergence behavior over iterations if desired.

---

## Deploying on Hardware

To use the identified parameters in your learning environment, integrate the PACE actuator model into your project.

Copy the following files (or directly import them in your learning environment):

* `pace-sim2real/source/pace_sim2real/pace_sim2real/utils/pace_actuator.py`
* `pace-sim2real/source/pace_sim2real/pace_sim2real/utils/pace_actuator_cfg.py`

Use the following procedure:

1. Import `PaceDCMotorCfg` (and optionally `PaceDCMotor`) into your project.
    ```python
    from pace_sim2real.utils import PaceDCMotorCfg, PaceDCMotor
    ```
2. During initialization, set:

    * `max_delay`
    * `encoder_bias`
    * `delay_mode` (must match the mode used during identification)

    using the values obtained from the parameter identification step.

3. Prior to training, configure your articulation object with the optimized parameters for:

    * `joint_armature`
    * `joint_viscous_friction`
    * `joint_friction`
    * `joint_dynamic_friction` (equal to `joint_friction`, or static friction × identified ratio with `separate_dynamic_friction = True`)

---

This concludes the complete workflow for creating a custom PACE environment and performing evolutionary system identification. Adjust parameters iteratively based on observed performance and physical plausibility to achieve optimal sim-to-real alignment.
