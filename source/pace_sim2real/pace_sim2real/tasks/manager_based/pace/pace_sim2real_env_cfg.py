# © 2025 ETH Zurich, Robotic Systems Lab
# Author: Filip Bjelonic
# Licensed under the Apache License 2.0

# import math
from dataclasses import MISSING
import torch

import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg
from isaaclab.envs import ManagerBasedRLEnvCfg
# from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.managers import RewardTermCfg as RewTerm
# from isaaclab.managers import SceneEntityCfg
from isaaclab.managers import TerminationTermCfg as DoneTerm
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.utils import configclass
from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR

from . import mdp


##
# Scene definition
##


@configclass
class PaceSim2realSceneCfg(InteractiveSceneCfg):

    # ground plane
    ground = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(size=(100.0, 100.0)),
    )
    env_spacing: float = 2.5
    num_envs: int = 4096

    # robots
    robot: ArticulationCfg = MISSING

    # lights
    sky_light = AssetBaseCfg(
        prim_path="/World/skyLight",
        spawn=sim_utils.DomeLightCfg(
            intensity=750.0,
            texture_file=f"{ISAAC_NUCLEUS_DIR}/Materials/Textures/Skies/PolyHaven/kloofendal_43d_clear_puresky_4k.hdr",
        ),
    )


##
# MDP settings
##


@configclass
class ActionsCfg:
    """Action specifications for the MDP."""
    joint_pos = mdp.JointPositionActionCfg(asset_name="robot", joint_names=[".*"], scale=1.0, use_default_offset=False)  # actions = absolute joint position targets


@configclass
class ObservationsCfg:
    """Observation specifications for the MDP."""

    @configclass
    class PolicyCfg(ObsGroup):
        """Observations for policy group."""
        joint_pos = ObsTerm(func=mdp.joint_pos_rel)
        joint_vel = ObsTerm(func=mdp.joint_vel_rel)
        actions = ObsTerm(func=mdp.last_action)

        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = False

    # observation groups
    policy: PolicyCfg = PolicyCfg()


@configclass
class RewardsCfg:
    """Reward terms for the MDP."""
    dof_pos_limits = RewTerm(func=mdp.joint_pos_limits, weight=0.0)


@configclass
class TerminationsCfg:
    """Termination terms for the MDP."""
    time_out = DoneTerm(func=mdp.time_out, time_out=False)


@configclass
class CMAESOptimizerCfg:
    """CMA-ES optimizer configuration."""
    max_iteration: int = 200
    epsilon: float = 1e-2
    sigma: float = 0.5
    save_interval: int = 10
    save_optimization_process: bool = False  # consume more disk space if True, saves optimization process after finishing


@configclass
class PaceCfg:
    """Overall configuration for Pace Sim2Real task."""
    cmaes: CMAESOptimizerCfg = CMAESOptimizerCfg()

    robot_name: str = MISSING
    data_dir: str = MISSING
    joint_order: list = MISSING
    bounds_params: torch.Tensor = MISSING

    separate_dynamic_friction: bool = False
    """Identify static and dynamic friction separately. Defaults to False (static = dynamic / coulomb friction).

    The friction parameter is then the static friction, and n ratios r in :attr:`friction_ratio_bounds` are appended
    after all other parameters, with dynamic friction = r * static friction. This keeps dynamic <= static friction for
    every sample.
    """
    friction_ratio_bounds: tuple[float, float] = (0.0, 1.0)
    """Lower and upper bound of the ratio between dynamic and static friction."""

    def apply_friction_ratio(self):
        """Extend the parameter bounds by the dynamic to static friction ratios."""
        if not self.separate_dynamic_friction:
            return
        num_joints = len(self.joint_order)
        num_params = self.bounds_params.shape[0]
        num_before = 4 * num_joints + 1
        if num_params == num_before:
            ratio_bounds = torch.tensor(self.friction_ratio_bounds, dtype=self.bounds_params.dtype).repeat(num_joints, 1)
            self.bounds_params = torch.cat([self.bounds_params, ratio_bounds], dim=0)
        elif num_params != num_before + num_joints:
            raise ValueError(f"Expected {num_before} or {num_before + num_joints} bounds with separate dynamic friction, got {num_params}.")

##
# Environment configuration
##


@configclass
class PaceSim2realEnvCfg(ManagerBasedRLEnvCfg):
    # Scene settings
    scene: PaceSim2realSceneCfg = PaceSim2realSceneCfg()
    # Basic settings
    actions: ActionsCfg = ActionsCfg()  # action = joint position targets (scale = 1.0 -> impedance control)

    observations: ObservationsCfg = ObservationsCfg()
    rewards: RewardsCfg = RewardsCfg()
    terminations: TerminationsCfg = TerminationsCfg()

    sim2real: PaceCfg = PaceCfg()

    # Post initialization
    def __post_init__(self) -> None:
        """Post initialization."""
        # general settings
        self.decimation = 1
        self.episode_length_s = 99999.0  # long episodes
        # viewer settings
        self.viewer.lookat = (0.0, 0.0, 0.8)
        self.viewer.eye = (2.0, 2.0, 1.5)
        # simulation settings
        self.sim.dt = 0.0025  # 400Hz simulation
        self.sim.render_interval = 4  # render at 100Hz

        self.scene.robot.spawn.articulation_props.fix_root_link = True
        self.sim2real.apply_friction_ratio()
