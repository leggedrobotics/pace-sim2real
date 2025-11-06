from isaaclab.utils import configclass

# from isaaclab.envs import ManagerBasedRLEnvCfg
from isaaclab_tasks.manager_based.locomotion.velocity.velocity_env_cfg import LocomotionVelocityRoughEnvCfg


from isaaclab_assets.robots.anymal import ANYMAL_D_CFG
from isaaclab.assets import ArticulationCfg
from isaaclab.actuators import DCMotorCfg
from pace_sim2real.utils.pace_actuator_cfg import PaceDCMotorCfg
from pace_sim2real.tasks.manager_based.pace_sim2real.pace_sim2real_env_cfg import PaceSim2realEnvCfg, PaceSim2realSceneCfg


ANYDRIVE_3_SIMPLE_ACTUATOR_CFG = PaceDCMotorCfg(
    joint_names_expr=[".*HAA", ".*HFE", ".*KFE"],
    saturation_effort=140.0,
    effort_limit=89.0,
    velocity_limit=8.5,
    stiffness={".*": 85.0},  # P gain in Nm/rad
    damping={".*": 0.6},  # D gain in Nm s/rad
    encoder_bias=[0.0] * 12,  # encoder bias in radians
    max_delay=10,  # max delay in simulation steps
)


@configclass
class ANYmalDPaceEnvCfg(PaceSim2realSceneCfg):
    """Configuration for Anymal-D robot in Pace Sim2Real environment."""
    robot: ArticulationCfg = ANYMAL_D_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot", init_state=ArticulationCfg.InitialStateCfg(pos=(0.0, 0.0, 1.0)),
                                                  actuators={"legs": ANYDRIVE_3_SIMPLE_ACTUATOR_CFG})


@configclass
class AnymalDPaceEnvCfg(PaceSim2realEnvCfg):

    scene: ANYmalDPaceEnvCfg = ANYmalDPaceEnvCfg()

    def __post_init__(self):
        # post init of parent
        super().__post_init__()

        # robot sim and control settings
        self.sim.dt = 0.0025  # 400Hz simulation
        self.decimation = 1  # 400Hz control
