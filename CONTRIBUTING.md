# Contributing to PACE

First off, thanks for your interest in contributing to **PACE** 💙\
This project is intended as a solid, research-grade foundation for sim-to-real transfer of legged robots, and external contributions are very welcome.

This document explains how to:

- report bugs and request features
- contribute code and documentation
- add **new examples** (e.g. for your own robots) that may appear on the [Examples](https://pace.filipbjelonic.com/examples/) page

---

## 1. Ways to contribute

You can help in many ways:

- **Bug reports** – crashes, incorrect behavior, unclear error messages  
- **Documentation improvements** – typos, unclear sections, better explanations, new guides  
- **New examples** – full PACE workflows for other robots (data collection, parameter fitting, evaluation)  
- **Core improvements** – actuator models, optimization utilities, environment wrappers, etc.  

If you plan a **larger change** (new robot integration, major API changes, etc.), please open a GitHub issue first so we can align on the design.

---

## 2. Development setup

Follow the installation instructions in the official documentation.

A typical setup:

```bash
# 1) Clone your fork
git clone git@github.com:<your-username>/pace-sim2real.git
cd pace-sim2real

# 2) Install PACE in editable mode inside the Isaac Lab environment
python -m pip install -e source/pace_sim2real

# 3) (Optional) Install pre-commit hooks
pip install pre-commit
pre-commit install
```
Before pushing:
```bash
pre-commit run --all-files
```
This will apply formatting and basic checks.

---

## 3. Git workflow

1. Fork the repository (external contributors)
2. Create a feature branch
    ```bash
    git checkout -b feature/my-robot-example
    ```
3. Make your changes (code + docs)
4. Run formatting checks:
    ```bash
    pre-commit run --all-files
    ```
5. Push and open a Pull Request against `main`\
    [https://github.com/leggedrobotics/pace-sim2real](https://github.com/leggedrobotics/pace-sim2real)

A PR should include:
- a short summary
- how it was tested (Isaac Lab version, GPU, commands)
- for examples: which robot / platform it applies to

---

## 4. Adding a new example

We especially welcome examples for additional robots that demonstrate:
- data collection
- PACE parameter identification
- evaluation and visualization
- (optionally) deployment

See existing examples:\
[https://pace.filipbjelonic.com/examples/](https://pace.filipbjelonic.com/examples/)

### 4.1. Code and scripts

Please add your scripts under scripts/pace/, for example:
```bash
scripts/pace/
  data_collection_<robot>.py
```

Guidelines:
- Reuse existing PACE components where possible
- Avoid hard-coded absolute paths
- Document any long-running processes
- Avoid committing large binary data; provide generation scripts instead

### 4.2 Documentation page

Each example needs a documentation page under:
```bash
docs/examples/
  anymal.md
  <your_robot>.md
```

Typical structure:

1. Overview
2. Data collection (commands, trajectory details)
3. Parameter identification
4. Evaluation and visualization
5. (Optional) Deployment instructions

Add it to the navigation in mkdocs.yml:
```yaml
nav:
  - Examples:
      - Overview: examples/index.md
      - ANYmal: examples/anymal.md
      - <Your Robot Name>: examples/<your_robot>.md
```

### 4.3. Checklist before submitting an example
- [x] Example runs with supported Isaac Sim / Isaac Lab versions
- [x] Documentation matches the scripts
- [x] No large binary files included
- [x] Example appears correctly in the “Examples” section

---

## 5. Reporting bugs & requesting features

Please use GitHub Issues:\
[https://github.com/leggedrobotics/pace-sim2real/issues](https://github.com/leggedrobotics/pace-sim2real/issues)

Include:

- PACE version / commit hash
- Isaac Sim / Isaac Lab version
- OS, CUDA, GPU
- exact command(s) used
- logs or error messages

Feature requests are welcome—please describe your use case (robot type, task, environment).

---

## 6. License

By contributing, you agree that your contributions are licensed under Apache-2.0, the same license as the project.

We aim to make PACE a reliable foundation for both research and industry.\
If your contribution becomes part of a project, paper, or cool demo, feel free to mention it in your PR—we love seeing what people build on top of this!
