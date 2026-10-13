Changelog
---------

0.2.0 (2026-10-13)
~~~~~~~~~~~~~~~~~~

Added
^^^^^

* Added ``delay_mode`` to :class:`PaceDCMotorCfg` to choose where the actuator delay acts. ``"command"`` delays the
  position/velocity targets and feed-forward torques, ``"effort"`` delays the computed torque.
* Added ``separate_dynamic_friction`` to :class:`PaceCfg` to identify static and dynamic friction separately. Dynamic
  friction is identified as a ratio of the static friction within ``friction_ratio_bounds`` (defaults to ``(0.0, 1.0)``),
  which appends one parameter per joint after the delay.
* Added a GitHub star history page to the documentation.

Changed
^^^^^^^

* The ANYmal example identifies static and dynamic friction separately (61 instead of 49 parameters), and the
  synthetic data uses a dynamic friction of half the static friction.
* Split the license file into license and copyright notice.
* Updated the citation to the published IJRR article.

Fixed
^^^^^

* **Breaking:** The actuator delay was applied to the computed torque, while the paper describes a delay of the
  commands. The delay now acts on the position/velocity targets and feed-forward torques (``delay_mode="command"``,
  the new default), which also keeps the PD loop stable for large delays. The results in the paper were produced with
  the previous implementation, which remains available via ``delay_mode="effort"``.
* Fixed ``plot_trajectory.py`` printing the last parameter instead of the delay.
* Removed the deprecated polyfill.io dependency from the documentation.


0.1.2 (2026-03-12)
~~~~~~~~~~~~~~~~~~

Changed
^^^^^^^

* Set both static and dynamic friction in the simulator to model Coulomb friction in Isaac Sim 5.0.
* Improved ``encoder_bias`` parsing of :class:`PaceDCMotor`.


0.1.1 (2026-01-30)
~~~~~~~~~~~~~~~~~~

Fixed
^^^^^

* Disabled the default joint position offset of the actions to avoid spawn failures on robots where 0.0 is not a
  feasible joint position.
* Fixed the documentation deployment and added contributing guidelines.


0.1.0 (2025-09-30)
~~~~~~~~~~~~~~~~~~

Added
^^^^^

* Created an initial template for building an extension or project based on Isaac Lab
