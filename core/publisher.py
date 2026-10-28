"""
core/publisher.py
Automates Git and GitHub repository synchronization.
Automatically commits and pushes updated M3U playlists to GitHub,
providing permanent raw URLs for Android IPTV Pro / TiviMate.
"""

import os
import shutil
import subprocess
import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Publisher")

class GitHubPublisher:
    def __init__(
        self,
        repo_name: str = "live-tv-playlist",
        branch: str = "main",
        is_private: bool = False,
        username: str = "iu-parvej"
    ):
        self.repo_name = repo_name
        self.branch = branch
        self.is_private = is_private
        self.username = username
        self.full_repo = f"{username}/{repo_name}"

    def run_cmd(self, cmd: list) -> subprocess.CompletedProcess:
        return subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

    def sync_output_to_root(self):
        """Copies generated files to root directory for ultra-clean raw GitHub links."""
        files_to_copy = [
            "playlist.m3u",
            "playlist_multiserver.m3u",
            "playlist_bdix.m3u",
            "playlist_sports.m3u",
            "status.json"
        ]
        for fname in files_to_copy:
            src = os.path.join("output", fname)
            if os.path.exists(src):
                shutil.copy2(src, fname)

    def ensure_repo(self) -> bool:
        # Check if git is initialized
        if not os.path.exists(".git"):
            logger.info("Initializing local git repository...")
            self.run_cmd(["git", "init"])
            self.run_cmd(["git", "branch", "-M", self.branch])

        # Check if remote origin exists
        res = self.run_cmd(["git", "remote", "get-url", "origin"])
        if res.returncode != 0:
            logger.info(f"Checking if remote GitHub repository '{self.full_repo}' exists...")
            check_gh = self.run_cmd(["gh", "repo", "view", self.full_repo])
            
            if check_gh.returncode != 0:
                logger.info(f"Creating new GitHub repository '{self.full_repo}' via gh CLI...")
                vis_flag = "--private" if self.is_private else "--public"
                create_res = self.run_cmd([
                    "gh", "repo", "create", self.full_repo,
                    vis_flag,
                    "--source=.",
                    "--remote=origin"
                ])
                if create_res.returncode != 0:
                    logger.warning(f"Could not create repo automatically: {create_res.stderr}")
                    # Fallback to manual remote set
                    self.run_cmd(["git", "remote", "add", "origin", f"https://github.com/{self.full_repo}.git"])
            else:
                self.run_cmd(["git", "remote", "add", "origin", f"https://github.com/{self.full_repo}.git"])

        return True

    def commit_and_push(self, stats: Dict[str, Any]) -> Optional[Dict[str, str]]:
        self.sync_output_to_root()
        self.ensure_repo()

        # Stage files
        self.run_cmd(["git", "add", "."])

        # Commit message
        total_ch = stats.get("channels_count", 0)
        bdix_ch = stats.get("bdix_channels_count", 0)
        commit_msg = f"Auto-refresh Live TV Playlists: {total_ch} channels active ({bdix_ch} BDIX fast)"

        commit_res = self.run_cmd(["git", "commit", "-m", commit_msg])
        if "nothing to commit" in commit_res.stdout.lower() or "nothing to commit" in commit_res.stderr.lower():
            logger.info("No playlist changes detected; already up-to-date.")
        else:
            logger.info(f"Git commit created: {commit_msg}")

        # Push to remote
        logger.info(f"Pushing to GitHub ({self.full_repo} [{self.branch}])...")
        push_res = self.run_cmd(["git", "push", "-u", "origin", self.branch])
        if push_res.returncode != 0:
            logger.warning(f"Push warning: {push_res.stderr}")
        else:
            logger.info("Successfully pushed to GitHub!")

        # Generate URLs
        raw_base = f"https://raw.githubusercontent.com/{self.full_repo}/{self.branch}"
        urls = {
            "primary": f"{raw_base}/playlist.m3u",
            "multiserver": f"{raw_base}/playlist_multiserver.m3u",
            "bdix": f"{raw_base}/playlist_bdix.m3u",
            "sports": f"{raw_base}/playlist_sports.m3u",
            "github_repo": f"https://github.com/{self.full_repo}"
        }
        return urls
