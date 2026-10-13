# Advanced Tutorial: Tailoring the Optimization to Your Needs

This advanced tutorial explains how to **customize and extend the PACE optimization pipeline** for specialized research and hardware requirements. It is intended for users who want to go beyond the default setup and adapt the evolutionary process to their specific system identification or sim-to-real objectives.

The core optimization logic of PACE is implemented in:

```
pace-sim2real/source/pace_sim2real/pace_sim2real/optim/cma_es.py
```

This file defines the `CMAESOptimizer` class, which orchestrates population sampling, evaluation, simulator parameter updates, convergence monitoring, and logging. Understanding and modifying this class enables fine-grained control over the entire identification process.

The class can be imported using
```python
from pace_sim2real import CMAESOptimizer
```

---

## Extension Strategies

Advanced users typically follow one of two approaches:

### 1. Inherit and extend

Create a new optimizer file in the same directory and inherit from `CMAESOptimizer`:

```python
class CustomCMAESOptimizer(CMAESOptimizer):
    def tell(self, sim_dof_pos, real_dof_pos):
        # Custom loss or scoring logic
        pass
```

This maintains compatibility with future PACE updates while allowing isolated customization.

### 2. Direct modification

Modify `cma_es.py` directly if you need tight integration or experimental changes that deviate significantly from the default interface.

This is useful for:

* Research prototypes
* Heavily custom cost functions
* Alternative parameter representations

---

## Understanding the Optimization Pipeline

Each CMA-ES generation follows the sequence:

1. **ask()** – Sample a population of normalized parameters
2. **Simulator Update** – Apply parameters to simulator
3. **Simulation Rollout** – Generate joint trajectories
4. **tell(...)** – Accumulate score over trajectories
5. **evolve()** – CMA-ES update step
6. **Logging + Checkpointing**

This loop continues until either:

* `max_iteration` is reached, or
* Convergence is detected via `epsilon`

---

## Changing the Optimization Objective

The default objective minimizes joint position tracking error with bias compensation:

```python
def tell(self, sim_dof_pos, real_dof_pos):
    self.scores += torch.sum(torch.square(sim_dof_pos - real_dof_pos - self.sim_params[:, self.bias_idx]), dim=1)
```

Advanced objectives can be implemented inside the `tell()` method.

### Examples

#### Weighted joint position + velocity

```python
error_pos = torch.sum((sim_dof_pos - real_dof_pos)**2, dim=1)
error_vel = torch.sum((sim_dof_vel - real_dof_vel)**2, dim=1)
self.scores += 0.7 * error_pos + 0.3 * error_vel
```

#### Velocity-only identification

```python
self.scores += torch.sum((sim_dof_vel - real_dof_vel)**2, dim=1)
```

#### End-effector error

```python
error = torch.norm(sim_ee_pose - real_ee_pose, dim=1)
self.scores += error
```

This allows optimization tailored to:

* Contact dynamics
* Compliance tuning
* Task-space behavior

---

## Adding or Modifying Optimized Parameters

By default, the optimizer tunes:

* Joint armature
* Viscous damping
* Coulomb friction (optionally split into static and dynamic friction)
* Encoder bias
* Actuator delay

The parameter vector is structured as:

```
[ armature | damping | friction | bias | delay | friction ratio (optional) ]
```

The friction ratios are only present with `separate_dynamic_friction = True`.

### Adding new parameters

For example, to add torque saturation:

1. Extend bounds tensor
2. Increase param dimensionality
3. Add index slices
4. Apply to simulator in `update_simulator()`

Example:

```python
# append after all existing parameters (including the optional friction ratios)
start = 4 * num_joints + 1 + (num_joints if separate_dynamic_friction else 0)
torque_limit_idx = slice(start, start + num_joints)
```

Then write into the simulator accordingly.

---

## Parameter Normalization Strategy

All CMA-ES parameters operate in normalized space ∈ [-1, 1]. These are mapped to physical values via:

```
sim_params = bounds_min + (params + 1)/2 * (bounds_max - bounds_min)
```

This ensures numerical stability and consistent scaling across heterogeneous parameters.

---

## Convergence Control

Stopping occurs when:

* `iteration >= max_iteration`
* OR score variance < epsilon

The metric used:

```
(max_score - min_score) / min_score
```

You may replace this with more sophisticated criteria such as:

* Fitness gradient threshold
* Moving average plateaus
* Early stopping windows

---

## Logging & Monitoring

TensorBoard metrics recorded include:

* Parameter distributions per joint
* Best parameter evolution
* Score curves
* Delay histograms

Checkpoints saved:

* Best trajectory (`best_trajectory.pt`)
* Mean parameters
* Full progress (optional)

This enables:

* Offline analysis
* Reproducibility
* Debugging of convergence behavior

---

## Common Pitfalls and Tips

* Avoid multi-scale parameters without normalization
* Ensure score magnitude remains stable across iterations
* Use histograms to detect parameter collapse
* Do not mix physical units inside loss

---

## Recommended Workflow for Custom Optimizers

1. Clone base implementation
2. Define new loss component
3. Visualize score evolution
4. Analyze parameter histograms
5. Validate on multiple trajectories
6. Deploy to hardware carefully

---

## Summary

The CMA-ES optimizer in PACE is designed for extensibility, transparency, and research flexibility. By customizing its objective, parameters, and convergence logic, users can tailor the system identification process to highly specific real-world challenges — from actuator modeling to task-specific sim-to-real transfer.
