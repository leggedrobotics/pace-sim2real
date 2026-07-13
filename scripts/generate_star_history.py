#!/usr/bin/env python3
"""Generate aggregate GitHub star-history data and a README-friendly SVG.

The script has two operating modes:

1. GitHub API mode (intended for GitHub Actions):
   reads GITHUB_TOKEN and fetches timestamped stargazers.
2. Local fixture mode:
   reads either a raw GitHub API response or a previously generated JSON file.

Only aggregate counts are written. Stargazer usernames are never persisted.
The implementation uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import os
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

DEFAULT_API_VERSION = "2026-03-10"
DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 600


class StarHistoryError(RuntimeError):
    """Raised for expected, user-facing failures."""


@dataclass(frozen=True)
class StarPoint:
    day: date
    count: int

    def as_json(self) -> dict[str, Any]:
        return {"date": self.day.isoformat(), "count": self.count}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch or load GitHub stargazer timestamps and generate JSON + SVG."
    )
    parser.add_argument(
        "--repository",
        default=os.environ.get("GITHUB_REPOSITORY"),
        help="Repository as OWNER/REPO. Defaults to GITHUB_REPOSITORY.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        help=(
            "Local JSON fixture. Accepts a raw GitHub stargazers response, a list "
            "of timestamps, or this script's normalized output."
        ),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        required=True,
        help="Path for normalized aggregate JSON.",
    )
    parser.add_argument(
        "--output-svg",
        type=Path,
        required=True,
        help="Path for the generated SVG chart.",
    )
    parser.add_argument(
        "--token-env",
        default="GITHUB_TOKEN",
        help="Environment variable containing the GitHub token (default: GITHUB_TOKEN).",
    )
    parser.add_argument(
        "--api-version",
        default=DEFAULT_API_VERSION,
        help=f"GitHub REST API version (default: {DEFAULT_API_VERSION}).",
    )
    parser.add_argument(
        "--as-of",
        type=parse_iso_date,
        default=datetime.now(timezone.utc).date(),
        help="Chart end date as YYYY-MM-DD (default: current UTC date).",
    )
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    return parser.parse_args()


def parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid date {value!r}; expected YYYY-MM-DD."
        ) from exc


def validate_repository(repository: str | None) -> str:
    if not repository:
        raise StarHistoryError(
            "No repository specified. Pass --repository OWNER/REPO or set "
            "GITHUB_REPOSITORY."
        )
    parts = repository.strip().split("/")
    if len(parts) != 2 or not all(parts):
        raise StarHistoryError(
            f"Invalid repository {repository!r}; expected exactly OWNER/REPO."
        )
    return f"{parts[0]}/{parts[1]}"


def parse_github_timestamp(value: str) -> datetime:
    if not isinstance(value, str):
        raise StarHistoryError(f"Expected timestamp string, received {type(value).__name__}.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise StarHistoryError(f"Invalid GitHub timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def github_request_json(url: str, token: str, api_version: str) -> tuple[Any, dict[str, str]]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github.star+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": api_version,
            "User-Agent": "pace-star-history-generator/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body = response.read().decode("utf-8")
            headers = {key.lower(): value for key, value in response.headers.items()}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        try:
            message = json.loads(detail).get("message", detail)
        except json.JSONDecodeError:
            message = detail
        raise StarHistoryError(
            f"GitHub API returned HTTP {exc.code}: {message}. "
            "Confirm that the workflow token can read repository metadata."
        ) from exc
    except urllib.error.URLError as exc:
        raise StarHistoryError(f"Could not reach the GitHub API: {exc.reason}") from exc

    try:
        return json.loads(body), headers
    except json.JSONDecodeError as exc:
        raise StarHistoryError("GitHub returned a non-JSON response.") from exc


def fetch_stargazer_timestamps(
    repository: str, token: str, api_version: str
) -> list[datetime]:
    owner, repo = repository.split("/", 1)
    owner_q = urllib.parse.quote(owner, safe="")
    repo_q = urllib.parse.quote(repo, safe="")

    timestamps: list[datetime] = []
    page = 1

    while True:
        url = (
            f"https://api.github.com/repos/{owner_q}/{repo_q}/stargazers"
            f"?per_page=100&page={page}"
        )
        payload, _headers = github_request_json(url, token, api_version)
        if not isinstance(payload, list):
            raise StarHistoryError(
                "Unexpected GitHub response: expected a list of stargazers."
            )

        for entry in payload:
            if not isinstance(entry, dict) or "starred_at" not in entry:
                raise StarHistoryError(
                    "GitHub did not return star timestamps. Ensure the request uses "
                    "Accept: application/vnd.github.star+json and that the token has "
                    "access to the repository."
                )
            timestamps.append(parse_github_timestamp(entry["starred_at"]))

        if len(payload) < 100:
            break
        page += 1

    timestamps.sort()
    return timestamps


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise StarHistoryError(f"Input file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise StarHistoryError(f"Input file is not valid JSON: {path}: {exc}") from exc


def extract_timestamps(payload: Any) -> list[datetime] | None:
    """Return raw timestamps if payload looks like raw/API fixture data."""
    entries: Any = payload
    if isinstance(payload, dict):
        for key in ("stargazers", "items", "raw"):
            if key in payload:
                entries = payload[key]
                break
        else:
            return None

    if not isinstance(entries, list):
        return None

    timestamps: list[datetime] = []
    for entry in entries:
        if isinstance(entry, str):
            timestamps.append(parse_github_timestamp(entry))
        elif isinstance(entry, dict) and "starred_at" in entry:
            timestamps.append(parse_github_timestamp(entry["starred_at"]))
        else:
            return None

    timestamps.sort()
    return timestamps


def extract_normalized_points(payload: Any) -> list[StarPoint] | None:
    if not isinstance(payload, dict) or not isinstance(payload.get("stars"), list):
        return None

    points: list[StarPoint] = []
    previous_day: date | None = None
    previous_count = -1

    for item in payload["stars"]:
        if not isinstance(item, dict) or "date" not in item or "count" not in item:
            raise StarHistoryError("Malformed normalized input: each star point needs date/count.")
        day = parse_iso_date(str(item["date"]))
        count = int(item["count"])
        if count < 0:
            raise StarHistoryError("Malformed normalized input: counts must be non-negative.")
        if previous_day is not None and day <= previous_day:
            raise StarHistoryError("Malformed normalized input: dates must be strictly increasing.")
        if count < previous_count:
            raise StarHistoryError("Malformed normalized input: counts must be cumulative.")
        points.append(StarPoint(day=day, count=count))
        previous_day = day
        previous_count = count

    return points


def build_points_from_timestamps(
    timestamps: Sequence[datetime], as_of: date
) -> list[StarPoint]:
    if timestamps and timestamps[-1].date() > as_of:
        raise StarHistoryError(
            f"--as-of {as_of.isoformat()} precedes the latest star "
            f"({timestamps[-1].date().isoformat()})."
        )

    if not timestamps:
        return [StarPoint(day=as_of, count=0)]

    stars_per_day = Counter(timestamp.date() for timestamp in timestamps)
    first_day = min(stars_per_day)
    points = [StarPoint(day=first_day - timedelta(days=1), count=0)]

    cumulative = 0
    for day in sorted(stars_per_day):
        cumulative += stars_per_day[day]
        points.append(StarPoint(day=day, count=cumulative))

    if points[-1].day < as_of:
        points.append(StarPoint(day=as_of, count=cumulative))

    return points


def extend_points_to_as_of(points: list[StarPoint], as_of: date) -> list[StarPoint]:
    if not points:
        return [StarPoint(day=as_of, count=0)]
    if points[-1].day > as_of:
        raise StarHistoryError(
            f"--as-of {as_of.isoformat()} precedes the final input point "
            f"({points[-1].day.isoformat()})."
        )
    if points[-1].day < as_of:
        return [*points, StarPoint(day=as_of, count=points[-1].count)]
    return points


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def nice_axis_max(value: int) -> int:
    if value <= 0:
        return 1
    rough = value / 5
    magnitude = 10 ** math.floor(math.log10(rough)) if rough > 0 else 1
    normalized = rough / magnitude
    if normalized <= 1:
        step = 1
    elif normalized <= 2:
        step = 2
    elif normalized <= 5:
        step = 5
    else:
        step = 10
    tick = step * magnitude
    return int(math.ceil(value / tick) * tick)


def format_tick_day(day: date, span_days: int) -> str:
    if span_days > 730:
        return day.strftime("%Y")
    if span_days > 120:
        return day.strftime("%b %Y")
    return day.strftime("%d %b")


def compact_integer(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M".rstrip("0").rstrip(".")
    if value >= 1_000:
        return f"{value / 1_000:.1f}k".rstrip("0").rstrip(".")
    return str(value)


def select_x_ticks(start: date, end: date, count: int = 6) -> list[date]:
    span = max((end - start).days, 1)
    ticks: list[date] = []
    for index in range(count):
        offset = round(span * index / (count - 1))
        candidate = start + timedelta(days=offset)
        if not ticks or candidate != ticks[-1]:
            ticks.append(candidate)
    return ticks


def render_svg(repository: str, points: Sequence[StarPoint], width: int, height: int) -> str:
    if width < 640 or height < 360:
        raise StarHistoryError("SVG dimensions must be at least 640x360.")
    if not points:
        raise StarHistoryError("Cannot render an empty point sequence.")

    margin_left = 88
    margin_right = 42
    margin_top = 112
    margin_bottom = 96
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom

    start_day = points[0].day
    end_day = points[-1].day
    span_days = max((end_day - start_day).days, 1)
    total = points[-1].count
    axis_max = nice_axis_max(total)

    def x_for(day: date) -> float:
        return margin_left + ((day - start_day).days / span_days) * plot_width

    def y_for(count: int) -> float:
        return margin_top + plot_height - (count / axis_max) * plot_height

    polyline = " ".join(f"{x_for(point.day):.2f},{y_for(point.count):.2f}" for point in points)
    area_path = (
        f"M {x_for(points[0].day):.2f} {margin_top + plot_height:.2f} "
        + " ".join(
            f"L {x_for(point.day):.2f} {y_for(point.count):.2f}" for point in points
        )
        + f" L {x_for(points[-1].day):.2f} {margin_top + plot_height:.2f} Z"
    )

    y_grid: list[str] = []
    for index in range(6):
        value = round(axis_max * index / 5)
        y = y_for(value)
        y_grid.append(
            f'<line class="grid" x1="{margin_left}" y1="{y:.2f}" '
            f'x2="{margin_left + plot_width}" y2="{y:.2f}" />'
        )
        y_grid.append(
            f'<text class="tick ytick" x="{margin_left - 18}" y="{y + 5:.2f}">'
            f"{html.escape(compact_integer(value))}</text>"
        )

    x_grid: list[str] = []
    for tick_day in select_x_ticks(start_day, end_day):
        x = x_for(tick_day)
        x_grid.append(
            f'<line class="grid vertical" x1="{x:.2f}" y1="{margin_top}" '
            f'x2="{x:.2f}" y2="{margin_top + plot_height}" />'
        )
        x_grid.append(
            f'<text class="tick xtick" x="{x:.2f}" y="{margin_top + plot_height + 38}">'
            f"{html.escape(format_tick_day(tick_day, span_days))}</text>"
        )

    repo_label = html.escape(repository)
    subtitle = (
        f"{total:,} star" if total == 1 else f"{total:,} stars"
    ) + f" · through {end_day.strftime('%d %b %Y')}"

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">
  <title id="title">{repo_label} star history</title>
  <desc id="description">Cumulative GitHub stars over time. Current total: {total}.</desc>
  <style>
    text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    .background {{ fill: #ffffff; }}
    .title {{ fill: #24292f; font-size: 31px; font-weight: 700; }}
    .subtitle {{ fill: #57606a; font-size: 18px; }}
    .grid {{ stroke: #d8dee4; stroke-width: 1; opacity: .72; }}
    .grid.vertical {{ opacity: .34; }}
    .tick {{ fill: #57606a; font-size: 14px; }}
    .ytick {{ text-anchor: end; }}
    .xtick {{ text-anchor: middle; }}
    .area {{ fill: url(#area-gradient); }}
    .history-line {{ fill: none; stroke: #0969da; stroke-width: 4; stroke-linecap: round; stroke-linejoin: round; }}
    .endpoint {{ fill: #ffffff; stroke: #0969da; stroke-width: 4; }}
    .badge {{ fill: #f6f8fa; stroke: #d0d7de; }}
    .badge-text {{ fill: #24292f; font-size: 18px; font-weight: 650; text-anchor: middle; }}
  </style>
  <defs>
    <linearGradient id="area-gradient" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#54aeff" stop-opacity="0.40" />
      <stop offset="100%" stop-color="#ddf4ff" stop-opacity="0.04" />
    </linearGradient>
  </defs>
  <rect class="background" width="{width}" height="{height}" rx="18" />
  <text class="title" x="{margin_left}" y="49">★ {repo_label}</text>
  <text class="subtitle" x="{margin_left}" y="80">Cumulative GitHub star history</text>
  <rect class="badge" x="{width - 204}" y="31" width="162" height="46" rx="23" />
  <text class="badge-text" x="{width - 123}" y="61">★ {total:,}</text>
  {''.join(y_grid)}
  {''.join(x_grid)}
  <path class="area" d="{area_path}" />
  <polyline class="history-line" points="{polyline}" />
  <circle class="endpoint" cx="{x_for(points[-1].day):.2f}" cy="{y_for(total):.2f}" r="7" />
  <text class="subtitle" x="{margin_left}" y="{height - 22}">{html.escape(subtitle)}</text>
</svg>
'''


def main() -> int:
    args = parse_args()

    try:
        repository = validate_repository(args.repository)

        if args.input is not None:
            payload = load_json(args.input)
            timestamps = extract_timestamps(payload)
            if timestamps is not None:
                points = build_points_from_timestamps(timestamps, args.as_of)
                latest_starred_at = timestamps[-1].isoformat().replace("+00:00", "Z") if timestamps else None
            else:
                normalized = extract_normalized_points(payload)
                if normalized is None:
                    raise StarHistoryError(
                        "Unsupported input JSON. Supply raw stargazers with starred_at "
                        "timestamps or normalized output containing stars[]."
                    )
                points = extend_points_to_as_of(normalized, args.as_of)
                latest_starred_at = payload.get("latest_starred_at")
        else:
            token = os.environ.get(args.token_env)
            if not token:
                raise StarHistoryError(
                    f"Environment variable {args.token_env!r} is not set. "
                    "Use --input for local fixture mode."
                )
            timestamps = fetch_stargazer_timestamps(repository, token, args.api_version)
            points = build_points_from_timestamps(timestamps, args.as_of)
            latest_starred_at = timestamps[-1].isoformat().replace("+00:00", "Z") if timestamps else None

        normalized_output = {
            "repository": repository,
            "as_of": args.as_of.isoformat(),
            "total_stars": points[-1].count,
            "latest_starred_at": latest_starred_at,
            "stars": [point.as_json() for point in points],
        }

        json_text = json.dumps(normalized_output, indent=2, ensure_ascii=False) + "\n"
        svg_text = render_svg(repository, points, args.width, args.height)

        atomic_write_text(args.output_json, json_text)
        atomic_write_text(args.output_svg, svg_text)

        print(
            f"Generated {args.output_json} and {args.output_svg} "
            f"for {repository} ({points[-1].count} stars)."
        )
        return 0

    except StarHistoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
