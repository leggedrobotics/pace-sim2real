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

    cfg: PaceDCMotorCfg

    def __init__(self, cfg: PaceDCMotorCfg, *args, **kwargs):
        super().__init__(cfg, *args, **kwargs)
        if isinstance(cfg.encoder_bias, (list, tuple)):
            if len(cfg.encoder_bias) != self.num_joints:
                raise ValueError(
                    f"encoder_bias must have {self.num_joints} elements (one per joint), "
                    f"but got {len(cfg.encoder_bias)}: {cfg.encoder_bias}"
                )
        self.encoder_bias = torch.tensor(cfg.encoder_bias, device=self._device).unsqueeze(0).repeat(self._num_envs, 1)

        self.positions_delay_buffer = DelayBuffer(cfg.max_delay + 1, self._num_envs, device=self._device)
        self.velocities_delay_buffer = DelayBuffer(cfg.max_delay + 1, self._num_envs, device=self._device)
        self.efforts_delay_buffer = DelayBuffer(cfg.max_delay + 1, self._num_envs, device=self._device)

        self.positions_delay_buffer.set_time_lag(cfg.max_delay, torch.arange(self._num_envs, device=self._device))
        self.velocities_delay_buffer.set_time_lag(cfg.max_delay, torch.arange(self._num_envs, device=self._device))
        self.efforts_delay_buffer.set_time_lag(cfg.max_delay, torch.arange(self._num_envs, device=self._device))

    def reset(self, env_ids: Sequence[int]):
        super().reset(env_ids)
        # reset buffers
        self.positions_delay_buffer.reset(env_ids)
        self.velocities_delay_buffer.reset(env_ids)
        self.efforts_delay_buffer.reset(env_ids)

    def update_encoder_bias(self, encoder_bias: torch.Tensor, joint_ids: Sequence[int]):
        self.encoder_bias[:, joint_ids] = encoder_bias

    def update_time_lags(self, delay: int | torch.Tensor):
        env_ids = torch.arange(self._num_envs, device=self._device)
        self.positions_delay_buffer.set_time_lag(delay, env_ids)
        self.velocities_delay_buffer.set_time_lag(delay, env_ids)
        self.efforts_delay_buffer.set_time_lag(delay, env_ids)

    def compute(
        self, control_action: ArticulationActions, joint_pos: torch.Tensor, joint_vel: torch.Tensor
    ) -> ArticulationActions:
        control_action.joint_positions = self.positions_delay_buffer.compute(control_action.joint_positions)
        control_action.joint_velocities = self.velocities_delay_buffer.compute(control_action.joint_velocities)
        control_action.joint_efforts = self.efforts_delay_buffer.compute(control_action.joint_efforts)
        # compute actuator model
        return super().compute(control_action, joint_pos + self.encoder_bias, joint_vel)
