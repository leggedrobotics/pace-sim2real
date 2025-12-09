# ⚙️ PACE — Sim-to-Real Transfer for Legged Robots
![License](https://img.shields.io/badge/license-Apache%202.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![Status](https://img.shields.io/badge/status-active_development-orange)

PACE is a framework for **sim-to-real transfer of diverse robotic systems**, combining data-driven system identification with evolutionary optimization.
It enables accurate actuator modeling and robust adaptation between simulation to reality by explicitly learning physically meaningful dynamics parameters.

---

## 🤖🐾 What is PACE?

PACE (Precise Adaptation through Continuous Evolution) bridges the gap between simulation and real hardware by:

* Estimating actuator and joint dynamics directly from measured data
* Using CMA-ES for parameter optimization
* Applying learned parameters to improve sim-to-real locomotion performance
* Supporting multiple robot platforms and actuator types

It is designed to integrate seamlessly with **NVIDIA Isaac Lab** and follows its task and environment conventions.

---

## 📦 Installation

### 1. Install Isaac Lab

Follow the official Isaac Lab installation guide:
[https://isaac-sim.github.io/IsaacLab/main/source/setup/installation/index.html](https://isaac-sim.github.io/IsaacLab/main/source/setup/installation/index.html)

We recommend using the **conda** or **uv** installation method, as this simplifies running Python scripts from the terminal and managing dependencies.

### 2. Clone this repository

Clone or copy this project separately from the Isaac Lab installation (i.e. outside the `IsaacLab` directory):

```bash
git clone https://github.com/leggedrobotics/pace-sim2real.git
cd pace-sim2real
```

### 3. Install PACE in editable mode

Using a Python interpreter that has Isaac Lab installed:

```bash
# Use 'PATH_TO_isaaclab.sh|bat -p' instead of 'python'
# if Isaac Lab is not installed in a Python venv or conda environment
python -m pip install -e source/pace_sim2real
```
### ⚠️ Isaac Sim version compatibility

PACE is developed and tested against **Isaac Sim 5.0 / Isaac Lab (latest)**.

If you run the examples on older versions (e.g. Isaac Sim 4.5), you may encounter warnings such as:

```bash
Setting joint viscous friction coefficients are not supported in Isaac Sim < 5.0
```

These warnings are expected and indicate that certain physics properties (e.g. joint viscous friction) are not supported by the older simulator version. While the examples may still run, the physical fidelity and sim-to-real accuracy will be reduced.

✅ Recommended: Isaac Sim 5.0 or newer  
⚠️ Legacy support: May run with limitations on < 5.0

---

## 📚 Documentation

The full PACE documentation is available online:

👉 https://pace.filipbjelonic.com

This documentation site is built using **MkDocs** with the **Material for MkDocs** theme.

---

## 🐾 Running an Example: ANYmal D

### 1. Activate the Isaac Lab environment

```bash
conda activate <isaaclab_env>
cd path/to/pace-sim2real
```

### 2. Collect excitation data

(Alternatively, place your own real-world data in `data/`)

```bash
python scripts/pace/data_collection.py
```

This will collect simulation data and store results in:

```
data/anymal_d_sim/chirp_data.pt
```

### 3. Run PACE parameter fitting

```bash
python scripts/pace/fit.py
```

This will estimate the actuator and joint parameters using CMA-ES and store results in:

```
logs/pace/anymal_d_sim/
```

---

## 🧭 Usage

Recommended imports for custom projects:

```python
from pace_sim2real import PaceCfg, PaceSim2realEnvCfg, CMAESOptimizer
from pace_sim2real.utils import PaceDCMotorCfg, PaceDCMotor
import pace_sim2real.tasks  # registers environments
```

Please refer to the official documentation for further information.

⚠️ PACE is under active development. APIs may evolve as the framework matures.

---

## 📜 License

© 2025 ETH Zurich, Robotic Systems Lab, Filip Bjelonic

This project is licensed under the Apache License, Version 2.0.
See the LICENSE file for details.

---

## 👥 Maintainers

The PACE project is actively maintained by:

- Filip Bjelonic (ETH Zurich, RSL)
- René Zurbrügg (ETH Zurich, RSL)
- Oliver Fischer (ETH Zurich, RSL)

The maintainers are responsible for reviewing contributions, managing issues, and guiding the technical direction of the framework.

---

## 🙏 Acknowledgements

We would like to thank the RSL Learning Group for many insightful discussions that influenced the development of PACE. We are especially grateful to Konrad and Matthias for valuable technical input related to electronics and system integration.

We also acknowledge Zichong, Stephan, Efe, Yuntao, René, Clemens, Ryo, Alexander, and Fabio for employing and extending the PACE framework in their own research, providing valuable feedback and practical insights.

We further thank Oliver Fischer and René Zurbrügg for their direct contributions to the codebase and their ongoing support as project maintainers.

We also thank the early testers — Oliver, Clemens and Yasmine — who evaluated the framework prior to its public release and provided valuable feedback on usability, stability, and documentation improvements.

---

## 🛠 Code Formatting

We provide a pre-commit configuration to automatically format and lint the codebase.

### Install pre-commit

```bash
pip install pre-commit
```

### Enable hooks

```bash
pre-commit install
```

### Run manually

```bash
pre-commit run --all-files
```

---

## 🧩 Troubleshooting

### Pylance: Missing Indexing of Extensions

In some VS Code versions, indexing for Isaac Lab extensions may be incomplete. Add your extension path to `.vscode/settings.json`:

```json
{
  "python.analysis.extraPaths": [
    "<path-to-ext-repo>/source/pace_sim2real"
  ]
}
```

---

### Pylance: Crash / High Memory Usage

If Pylance crashes due to excessive indexing, exclude unused omniverse packages by commenting them out in:

`.vscode/settings.json` → `python.analysis.extraPaths`

Examples of packages that can often be safely excluded:

```json
"<path-to-isaac-sim>/extscache/omni.anim.*",
"<path-to-isaac-sim>/extscache/omni.kit.*",
"<path-to-isaac-sim>/extscache/omni.graph.*",
"<path-to-isaac-sim>/extscache/omni.services.*"
```

---

## 🤝 Contributing & Feedback

Internal feedback is highly welcome during this phase.
Please report issues, unclear steps, or suggestions directly via GitHub issues or internal channels.

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute.

---

## 📖 How to cite

If you use **PACE Sim2Real** in your research, please cite our [paper](https://arxiv.org/pdf/2509.06342):

> F. Bjelonic, F. Tischhauser, and M. Hutter,  
> _Towards Bridging the Gap: Systematic Sim-to-Real Transfer for Diverse Legged Robots_, arXiv:2509.06342, 2025.

```bibtex
@article{bjelonic2025towards,
  title         = {Towards Bridging the Gap: Systematic Sim-to-Real Transfer for Diverse Legged Robots},
  author        = {Bjelonic, Filip and Tischhauser, Fabian and Hutter, Marco},
  journal       = {arXiv preprint arXiv:2509.06342},
  year          = {2025},
  eprint        = {2509.06342},
  archivePrefix = {arXiv},
  primaryClass  = {cs.RO},
}
```

---

**PACE** — bringing simulation and reality closer, one parameter at a time.
