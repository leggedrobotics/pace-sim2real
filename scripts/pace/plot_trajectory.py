import torch
import matplotlib.pyplot as plt
import re
from pathlib import Path

import argparse

# add argparse arguments
parser = argparse.ArgumentParser(description="Pace agent for Isaac Lab environments.")
parser.add_argument("--folder_name", type=str, default=None, help="Name of the folder to use.")
parser.add_argument("--params_name", type=str, default=None, help="Name of the parameters file to use.")
parser.add_argument("--robot_name", type=str, default="anymal_d", help="Name of the robot.")
parser.add_argument("--plot_trajectory", action="store_true", help="Whether to plot the trajectory.")
parser.add_argument("--plot_score", action="store_true", help="Whether to plot the score over iterations.")

args = parser.parse_args()
folder_name = args.folder_name
params_name = args.params_name
robot_name = args.robot_name
plot_trajectory = args.plot_trajectory
plot_score = args.plot_score

current_dir = Path(__file__).parent.resolve()
project_root = current_dir.parent.parent

# folder_name = "25_10_24_12-05-07"
log_dir = project_root / "logs" / "pace" / robot_name

if not log_dir.exists():
    raise FileNotFoundError(f"No logs for robot {robot_name} under {log_dir}")

_pattern = re.compile(r"^params_(\d+)\.pt$")


def find_latest_params(root: Path):
    best = None  # tuple (int, Path)
    for p in root.rglob("params_*.pt"):
        m = _pattern.match(p.name)
        if not m:
            continue
        num = int(m.group(1))
        if best is None or num > best[0]:
            best = (num, p)
    return None if best is None else best[1], best[0]


# if no folder_name given, pick the most recent run folder for the robot
if not folder_name:
    robot_dir = log_dir
    candidates = [p for p in robot_dir.iterdir() if p.is_dir()]
    if not candidates:
        raise FileNotFoundError(f"No run folders found under {robot_dir}")
    latest_folder = max(candidates, key=lambda p: p.stat().st_mtime)
    folder_name = latest_folder.name

# now point log_dir at the chosen robot/run folder
log_dir = log_dir / folder_name

if params_name is None:
    params_path, params_num = find_latest_params(log_dir)
else:
    params_path = log_dir / params_name
    params_num = int(_pattern.match(params_name).group(1))
    if not params_path.exists():
        raise FileNotFoundError(f"Given params file {params_path} does not exist")
if params_path is None:
    raise FileNotFoundError(f"No params_*.pt files found under {log_dir}")
print(f"Latest params file: {params_path}")

params = torch.load(params_path)
config = torch.load(log_dir / "config.pt")

joint_names = config["joint_names"]
trajectories = params["best_trajectory"]  # time x joints
real_trajectories = config["dof_pos"]  # time x joints
target_trajectories = config["des_dof_pos"]  # time x joints

print(f"Best parameter set: {params['mean']}")
encoder_bias = params['mean'][36:48]

if plot_score:
    plt.figure()
    plt.title("CMA-ES Score over Iterations")
    plt.xlabel("Iteration")
    plt.ylabel("Score")
    data = torch.min(params["scores_buffer"][:params_num + 1], dim=1).values.cpu().numpy()
    plt.semilogy(data)
    plt.xlim(0, params_num)
    # plt.ylim(0, None)
    plt.grid()
    plt.show()

if plot_trajectory:
    for i in range(trajectories.shape[1]):
        plt.figure()
        plt.plot(trajectories[:, i].cpu().numpy(), label="Sim")
        plt.plot(real_trajectories[:, i].cpu().numpy() + encoder_bias[i].item(), label="Real")
        plt.plot(target_trajectories[:, i].cpu().numpy(), c="grey", label="Target", linestyle="--")
        plt.title(f"Joint {joint_names[i]}")  # Use joint names from config
        plt.xlabel("Time step")
        plt.ylabel("Position (rad)")
        plt.legend()
        plt.grid()
        plt.show()

print("Plotting complete.")
