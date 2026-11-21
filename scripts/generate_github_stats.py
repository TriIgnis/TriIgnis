#!/usr/bin/env python3
"""Generate a warm, minimal GitHub profile statistics SVG."""

from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

USERNAME = "TriIgnis"
API = "https://api.github.com"
OUTPUT = Path("assets/github-stats.svg")


def github_get(path: str):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "TriIgnis-profile-stats",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"{API}{path}", headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"GitHub API request failed for {path}: {exc}") from exc


def compact(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}k"
    return str(value)


def build_svg(metrics, updated):
    centers = [145, 415, 685, 955]
    accents = ["#C97952", "#D6A45F", "#89947B", "#C58C70"]
    groups = []

    for index, (label, value, caption) in enumerate(metrics):
        groups.append(f"""
    <g transform="translate({centers[index]} 0)">
      <circle cx="-78" cy="76" r="4" fill="{accents[index]}" opacity=".9"/>
      <text x="0" y="81" text-anchor="middle" font-size="11" font-weight="700" letter-spacing="1.25" fill="#927B68">{escape(label)}</text>
      <text x="0" y="132" text-anchor="middle" font-size="38" font-weight="750" fill="#453B34">{escape(value)}</text>
      <rect x="-16" y="151" width="32" height="3" rx="1.5" fill="{accents[index]}" opacity=".75"/>
      <text x="0" y="180" text-anchor="middle" font-size="12" fill="#8A7868">{escape(caption)}</text>
    </g>""")

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="205" viewBox="0 0 1100 205" role="img" aria-labelledby="title desc">
  <title id="title">TriIgnis GitHub 数据统计</title>
  <desc id="desc">暖色风格的 GitHub 数据统计，展示公开仓库、累计 Stars、累计 Forks 和关注者数量，每日自动更新。</desc>
  <rect x="4" y="4" width="1092" height="197" rx="26" fill="#FFF9F2" stroke="#EFE2D4" stroke-width="1.4"/>
  <g font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
    <text x="34" y="36" font-size="11" font-weight="700" letter-spacing="2.1" fill="#A66A4D">GITHUB SNAPSHOT</text>
    <text x="1064" y="36" font-size="10.5" text-anchor="end" letter-spacing="1" fill="#A28E7C">UPDATED {escape(updated)}</text>
    <path d="M280 58 V184 M550 58 V184 M820 58 V184" stroke="#EDE2D7" stroke-width="1"/>
    {''.join(groups)}
  </g>
</svg>
'''


def main():
    user = github_get(f"/users/{USERNAME}")
    repositories = []
    page = 1
    while True:
        batch = github_get(
            f"/users/{USERNAME}/repos?type=owner&per_page=100&page={page}"
        )
        repositories.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    original_repositories = [repo for repo in repositories if not repo.get("fork", False)]
    total_stars = sum(int(repo.get("stargazers_count", 0)) for repo in original_repositories)
    total_forks = sum(int(repo.get("forks_count", 0)) for repo in original_repositories)

    metrics = [
        ("PUBLIC REPOSITORIES", compact(int(user.get("public_repos", 0))), "公开仓库"),
        ("TOTAL STARS", compact(total_stars), "累计 Stars"),
        ("TOTAL FORKS", compact(total_forks), "累计 Forks"),
        ("FOLLOWERS", compact(int(user.get("followers", 0))), "关注者"),
    ]
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d UTC")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build_svg(metrics, updated), encoding="utf-8")
    print(f"Updated {OUTPUT}: {metrics}")


if __name__ == "__main__":
    main()
