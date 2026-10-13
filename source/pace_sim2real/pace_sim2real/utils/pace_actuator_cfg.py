# © 2025 ETH Zurich, Robotic Systems Lab
# Author: Filip Bjelonic
# Licensed under the Apache License 2.0

from __future__ import annotations
import torch

from isaaclab.utils import configclass

from isaaclab.actuators import DCMotorCfg
from pace_sim2real.utils import pace_actuator


@configclass
class PaceDCMotorCfg(DCMotorCfg):
    """Configuration for Pace DC Motor actuator model.

    This class extends the base DCMotorCfg with Pace-specific parameters.
    """
    class_type: type = pace_actuator.PaceDCMotor
    encoder_bias: dict[str, float] | float | None = 0.0
    max_delay: torch.int | None = 0
    delay_mode: str = "command"
    """Where the delay acts. Defaults to "command".

    * "command": the targets (joint position, velocity and feed-forward effort) reach the drive late, while the PD
      controller runs on the current measurements, as on a drive with its own control loop.
    * "effort": the torque computed from the current measurements is applied late, i.e. the feedback itself is delayed.
    """
