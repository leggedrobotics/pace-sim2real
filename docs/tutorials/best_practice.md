# Best Practices for CMA-ES Optimization in PACE

This guide documents recommended practices for **safe, efficient, and reliable use of the CMA-ES optimizer in PACE**. It targets standard users who want robust results without diving into deep algorithmic customization.

These recommendations are derived from practical experience with system identification on real legged robots and large-scale simulation campaigns.

---

## 1. Choose Bounds Carefully

Parameter bounds define the effective search space of CMA-ES and have the strongest influence on convergence quality.

### Recommendations

* Base bounds on **physically plausible values**, not theoretical extremes.
* Use datasheets, prior experiments, or hand tuning as reference.
* Avoid overly wide bounds: this slows convergence and destabilizes covariance adaptation.
* Avoid overly tight bounds: this leads to local minima and poor generalization.

---

## 2. Population Size vs Runtime Trade-off

Population size directly controls exploration quality and computational cost.

### Practical guidance

* 256–512: fast prototyping
* 512–2048: standard identification
* 2048–4096+: high-fidelity identification / publication-grade results

Scaling behavior:

```
Runtime ∝ population_size × trajectory_length
GPU memory ∝ population_size × time_steps × joints
```

Note: Since we parallelize simulation environments, runtime does not scale linearly with population size and depends on your GPU hardware.

---

## 3. Avoid Overfitting to a Single Trajectory

A perfect fit to one trajectory does not guarantee real-world performance.

### Always validate on:

* Different excitation signals (e.g. varying chirp frequencies)
* Changed amplitudes
* Phase-shifted trajectories
* Different PD-gains

> Good identification minimizes error across a family of trajectories, not one sequence.

---

## 4. Understand Delay Optimization Limitations

In PACE, delay is internally discretized to an integer value. By default, it delays the commanded targets (`delay_mode = "command"`); set `delay_mode = "effort"` to delay the computed torque instead, as in versions before v0.2.0. Keep the same mode for identification and deployment.

Consequences:

* Optimization landscape is discontinuous
* Small changes in parameters may cause sudden behavior jumps
* Convergence may appear noisy or unstable

### Recommendation

Use conservative delay bounds and monitor delay histograms during training.

---

## 5. Always Start in Simulation

Never apply unverified parameters directly to hardware.

### Mandatory workflow

1. Identify parameters in simulation
2. Validate on multiple trajectories
3. Apply conservative limits
4. Gradually deploy to hardware
5. Monitor safety metrics (torque, temperature, velocity)

---

## 6. Monitor TensorBoard Actively

TensorBoard is not optional — it is a diagnostic tool.

### Healthy convergence patterns

* Histogram narrowing over iterations
* Slowly improving best score
* Stable mean evolution

### Warning signs

* Histogram collapse early (premature convergence)
* Multi-modal distributions persisting
* Oscillating delay or bias values

---

## 7. Reproducibility & Logging

For traceable experiments, always log:

* Parameter bounds
* Trajectory settings
* Robot model version

Even with fixed seeds:

* Floating-point noise may cause tiny variations
* Physics determinism may depend on hardware and driver versions

---

## 8. Memory & Performance Awareness

PACE stores population trajectories and histories for analysis.

Be mindful that:

```
Memory ≈ iterations × population × time_steps × joints
```

Large experiments can exceed GPU memory silently.

### Recommendations

* Reduce `save_interval`
* Disable full history unless needed
* Monitor GPU usage during early runs

---

## 9. Hardware Safety Checklist

Before deploying to real robots:

* ✅ Simulator behavior stable
* ✅ No joint oscillations
* ✅ Torque below safe thresholds
* ✅ Temperatures monitored
* ✅ Emergency stop tested

---

## 10. Practical Workflow Summary

Recommended pipeline:

1. Define physically sound bounds
2. Run CMA-ES in simulation
3. Monitor convergence and histograms
4. Validate on unseen motions
5. Gradually introduce to hardware
6. Iterate and refine

---

## Final Note

CMA-ES in PACE is a powerful tool — but with power comes responsibility. Proper bounds, active monitoring, and careful validation are essential for safe and meaningful results. Following these best practices will significantly increase both identification quality and long-term hardware reliability.

---

If you deviate from these guidelines, do so intentionally and document your rationale.
