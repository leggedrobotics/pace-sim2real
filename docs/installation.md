# Installation

This section describes how to install and set up the **PACE (Precise Adaptation through Continuous Evolution)** framework on your system. PACE is built on top of **NVIDIA Isaac Lab** and requires a working GPU-accelerated simulation environment.

---

## System Requirements

### Supported Operating Systems

* Ubuntu 20.04 or newer (tested and recommended: Ubuntu 22.04)

### Hardware

* NVIDIA GPU with CUDA support (RTX series recommended)
* At least 8 GB GPU memory (16 GB recommended for large-scale experiments)
* 16 GB system RAM (32 GB recommended)

### Software

* NVIDIA Driver
* CUDA Toolkit (compatible with your Isaac Sim version)
* Python >= 3.10
* Git

PACE is **developed and tested** with Isaac Sim 5.0, Isaac Lab 0.46.2 and Python 3.11.13. Other versions may work but are not officially supported at the moment.

### Isaac Sim compatibility notes

PACE is designed around the physics capabilities introduced in **Isaac Sim 5.0**, including:
- Joint viscous friction modeling
- Separate static and dynamic joint friction
- Improved articulation parameter handling
- More consistent actuator behavior

When running PACE on Isaac Sim versions **< 5.0**, you may see warnings such as:

```bash
Setting joint viscous friction coefficients are not supported in Isaac Sim < 5.0
Setting joint dynamic friction coefficients are not supported in Isaac Sim < 5.0
```

This means the simulator silently ignores these parameters. As a result:
- The simulation will run, but
- The actuator dynamics will not match the intended PACE model
- Sim-to-real performance may degrade
- With `separate_dynamic_friction = True`, the friction ratios have no effect and cannot be identified

For accurate system identification and controller transfer, we strongly recommend using:
> Isaac Sim 5.0 + Isaac Lab (current stable)

Future versions of PACE may rely even more heavily on features introduced in Isaac Sim 5.x.

---

## 1. Install Isaac Lab

PACE is implemented as an extension for Isaac Lab. Please follow the official Isaac Lab installation instructions first:

👉 [https://isaac-sim.github.io/IsaacLab/](https://isaac-sim.github.io/IsaacLab/)


## 2. Clone the PACE repository

Clone the PACE repository (outside of IsaacLab):

```bash
cd ~
git clone https://github.com/leggedrobotics/pace-sim2real.git
```

---

## 3. Install the PACE extension

Activate your Conda environment and install PACE

```bash
cd ~/pace-sim2real
# use 'PATH_TO_isaaclab.sh|bat -p' instead of 'python' if Isaac Lab is not installed in Python venv or conda
python -m pip install -e source/pace_sim2real
```

All required Python dependencies (including CMA-ES) are installed automatically during this step.

---

You are now ready to run PACE 🚀

Proceed to:

* **Examples** – run your first experiment
* **Guids** – how to set up your own robot and tasks
* **Concepts** – core ideas behind PACE and sim-to-real transfer
