"""
Trova Native MPV Hardware-Decoded Player Service
Launches streaming trailers and media directly in MPV for Omarchy Linux users.
"""

import subprocess
import shutil
import os

class MpvService:
    def __init__(self):
        self.mpv_bin = shutil.which("mpv")
        self.ytdlp_bin = shutil.which("yt-dlp") or shutil.which("yt-dlp-ejs") or os.path.expanduser("~/.local/bin/yt-dlp")
        self.current_process = None

    def is_available(self):
        return bool(self.mpv_bin)

    def play_url(self, url, title="Trailer"):
        if not self.mpv_bin:
            return {"success": False, "error": "mpv is not installed on this system"}

        # Kill any previously active mpv player launched by Trova
        self.stop()

        cmd = [
            self.mpv_bin,
            url,
            "--force-window=immediate",
            "--hwdec=auto",
            f"--title=Trova: {title}",
            "--geometry=75%x75%+50%+50%",
            "--autofit=1280x720",
            "--keep-open=no"
        ]

        if self.ytdlp_bin and os.path.exists(self.ytdlp_bin):
            cmd.append(f"--script-opts=ytdl_hook-ytdl_path={self.ytdlp_bin}")

        try:
            # Spawn in background detached
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            return {"success": True, "pid": self.current_process.pid}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def stop(self):
        if self.current_process:
            try:
                self.current_process.terminate()
                self.current_process.wait(timeout=1.0)
            except Exception:
                try:
                    self.current_process.kill()
                except Exception:
                    pass
            self.current_process = None
