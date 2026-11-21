#!/usr/bin/env python3
"""Generate a warm, self-hosted GitHub profile statistics SVG."""

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
    cards = []
    x_positions = [24, 292, 560, 828]
    accents = ["#C97952", "#E6AC59", "#89947B", "#D99A70"]
    label_colors = ["#A66A4D", "#A8843F", "#78866B", "#A66A4D"]

    for index, (label, value, caption) in enumerate(metrics):
        x = x_positions[index]
        accent = accents[index]
        label_color = label_colors[index]
        cards.append(f"""
    <g transform="translate({x} 55)">
      <rect width="250" height="145" rx="17" fill="#FFFCF7" stroke="#EADBCB"/>
      <circle cx="218" cy="28" r="7" fill="{accent}" opacity=".25"/>
      <text x="22" y="35" font-size="11" font-weight="700" letter-spacing="1.1" fill="{label_color}">{escape(label)}</text>
      <text x="22" y="91" font-size="38" font-weight="750" fill="#453B34">{escape(value)}</text>
      <rect x="22" y="112" width="44" height="4" rx="2" fill="{accent}"/>
      <text x="22" y="133" font-size="12" fill="#8A7868">{escape(caption)}</text>
    </g>""")

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="230" viewBox="0 0 1100 230" role="img" aria-labelledby="title desc">
  <title id="title">TriIgnis GitHub 数据统计</title>
  <desc id="desc">暖色风格的 GitHub 数据卡片，展示公开仓库、累计 Stars、累计 Forks 和关注者数量，每日自动更新。</desc>
  <rect x="4" y="4" width="1092" height="222" rx="24" fill="#FFF9F2" stroke="#E8D7C6" stroke-width="2"/>
  <g font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
    <text x="34" y="38" font-size="12" font-weight="700" letter-spacing="2.4" fill="#A66A4D">GITHUB SNAPSHOT</text>
    <text x="1064" y="38" font-size="11" text-anchor="end" letter-spacing="1.2" fill="#A28E7C">UPDATED {escape(updated)}</text>
    {''.join(cards)}
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
