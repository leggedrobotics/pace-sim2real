# © 2025 ETH Zurich, Robotic Systems Lab
# Author: Filip Bjelonic
# Licensed under the Apache License 2.0

from __future__ import annotations

import torch
from collections.abc import Sequence
from typing import TYPE_CHECKING

from isaaclab.actuators import DCMotor
from isaaclab.utils.types import ArticulationActions
from isaaclab.utils import DelayBuffer
if TYPE_CHECKING:
    # only for type checking
    from .pace_actuator_cfg import PaceDCMotorCfg


class PaceDCMotor(DCMotor):
    """Pace DC Motor actuator model with encoder bias and action delay.

    The actuator models a DC motor whose controller receives joint positions in the encoder
    frame by adding a per-joint encoder bias to the true joint positions. In other words,
    the controller operates on biased (encoder) positions rather than the true joint positions.

    A configurable delay (in simulation steps) represents the latency between command calculation and actuation.
    By default, the commanded targets are delayed and the PD controller acts on the current measurements
    (:attr:`PaceDCMotorCfg.delay_mode` = "command"). Alternatively, the computed torque is delayed ("effort").

    The software implementation is inspired by DelayedPDActuator.
    """

    cfg: PaceDCMotorCfg

    def __init__(self, cfg: PaceDCMotorCfg, *args, **kwargs):
        super().__init__(cfg, *args, **kwargs)
        if isinstance(cfg.encoder_bias, (list, tuple)):
            if len(cfg.encoder_bias) != self.num_joints:
                raise ValueError(
                    f"encoder_bias must have {self.num_joints} elements (one per joint), "
                    f"but got {len(cfg.encoder_bias)}: {cfg.encoder_bias}"
                )
        self.encoder_bias = self._parse_joint_parameter(cfg.encoder_bias, 0.0)

        if cfg.delay_mode not in ("command", "effort"):
            raise ValueError(f"delay_mode must be 'command' or 'effort', but got '{cfg.delay_mode}'.")
        # one buffer for the torque ("effort") or one per command signal ("command")
        buffer_names = ("effort",) if cfg.delay_mode == "effort" else ("position", "velocity", "effort")
        self.delay_buffers = {name: DelayBuffer(cfg.max_delay + 1, self._num_envs, device=self._device) for name in buffer_names}
        for buffer in self.delay_buffers.values():
            buffer.set_time_lag(cfg.max_delay, torch.arange(self._num_envs, device=self._device))

    def reset(self, env_ids: Sequence[int]):
        super().reset(env_ids)
        # reset buffers
        for buffer in self.delay_buffers.values():
            buffer.reset(env_ids)

    def update_encoder_bias(self, encoder_bias: torch.Tensor):
        self.encoder_bias = encoder_bias

    def update_time_lags(self, delay: int | torch.Tensor, env_ids: Sequence[int] | None = None):
        if env_ids is None:
            env_ids = torch.arange(self._num_envs, device=self._device)
        for buffer in self.delay_buffers.values():
            buffer.set_time_lag(delay, env_ids)

    def compute(
        self, control_action: ArticulationActions, joint_pos: torch.Tensor, joint_vel: torch.Tensor
    ) -> ArticulationActions:
        control_action = self._delay_command(control_action)
        # compute actuator model with encoder bias added to joint positions (joint position in encoder frame, not simulation frame)
        control_action_sim = super().compute(control_action, joint_pos - self.encoder_bias, joint_vel)
        control_action_sim.joint_efforts = self._delay_effort(control_action_sim.joint_efforts)
        return control_action_sim

    """
    Helper functions.
    """

    def _delay_command(self, control_action: ArticulationActions) -> ArticulationActions:
        """Delay the commanded targets (delay_mode "command")."""
        if self.cfg.delay_mode == "command":
            control_action.joint_positions = self.delay_buffers["position"].compute(control_action.joint_positions)
            control_action.joint_velocities = self.delay_buffers["velocity"].compute(control_action.joint_velocities)
            control_action.joint_efforts = self.delay_buffers["effort"].compute(control_action.joint_efforts)
        return control_action

    def _delay_effort(self, effort: torch.Tensor) -> torch.Tensor:
        """Delay the computed torque (delay_mode "effort")."""
        if self.cfg.delay_mode == "effort":
            return self.delay_buffers["effort"].compute(effort)
        return effort
