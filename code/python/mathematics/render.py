"""Render distributable H.264 animations and their informative still frames."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
SCENES = ["LinearMap", "Stability", "Taylor", "Jacobian", "KKT",
          "Sampling", "NormalArea", "Fourier"]
POSTER_TIMES = dict(LinearMap=9, Stability=8, Taylor=15, Jacobian=6,
                    KKT=10, Sampling=13, NormalArea=9, Fourier=10)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("scenes", nargs="*", choices=SCENES)
    args = parser.parse_args()
    dest = ROOT / "figures/mathematics/animations"
    dest.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).parent), OPENBLAS_NUM_THREADS="1")
    with tempfile.TemporaryDirectory(prefix="math-manim-") as temporary:
        for name in args.scenes or SCENES:
            subprocess.run([sys.executable, "-m", "manim", "--disable_caching",
                            "--format=mp4", "--resolution=1280,720", "--fps=30",
                            "--media_dir", temporary, str(Path(__file__).with_name("scenes.py")), name],
                           env=env, check=True)
            raw = next(Path(temporary).glob(f"videos/scenes/*/{name}.mp4"))
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw),
                            "-c:v", "libx264", "-crf", "23", "-pix_fmt", "yuv420p",
                            "-movflags", "+faststart", "-an", str(dest/f"{name}.mp4")], check=True)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(POSTER_TIMES[name]),
                            "-i", str(dest/f"{name}.mp4"), "-frames:v", "1",
                            str(dest/f"{name}.png")], check=True)
            print(f"Published assets: {name}", flush=True)


if __name__ == "__main__":
    main()
