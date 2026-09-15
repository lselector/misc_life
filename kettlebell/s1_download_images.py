#!/usr/bin/env python3
"""
Download the images used by KETTLEBELL_GUIDE.md.

Two sources are used. Technique photographs come from
Wikimedia Commons and are freely licensed, mostly CC BY-SA
4.0 by Taco Fleur of Cavemantraining. Video thumbnails come
from YouTube and are shown as clickable links to the videos
they belong to.

Files that are already present are skipped, so the script is
safe to re-run. Use --force to re-download everything.

Run s2_clean_images.py afterwards to bring the downloaded
files to one standard size.

Usage:
    python3 s1_download_images.py
    python3 s1_download_images.py --force

Created: 2026-09-08
Last updated: 2026-09-08
"""

import glob
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

IMAGES_DIR = "images"
TIMEOUT = 30
USER_AGENT = (
    "kettlebell-guide-builder/1.0 "
    "(personal reference document)"
)

# Wikimedia throttles bursts, so photos are fetched slowly
# and a 429 is retried with a longer wait each time.
POLITE_DELAY = 2.0
MAX_TRIES = 4

WM = "https://upload.wikimedia.org/wikipedia/commons"

# Technique photos: (local name, full source URL)
PHOTOS = [
    ("kb-anatomy",
     f"{WM}/3/38/"
     "Anatomy_of_the_Kettlebell_%28cropped%29.jpg"),
    ("competition-bells",
     f"{WM}/thumb/2/2d/Competition_kettlebells_8-24_kilos"
     ".jpg/960px-Competition_kettlebells_8-24_kilos.jpg"),
    ("grip-flat-hand",
     f"{WM}/b/b6/Grip_Flat_Hand_Grip.jpg"),
    ("grip-tight",
     f"{WM}/thumb/f/ff/Loose_Grip_vs_Tight_Grip_-_Tight"
     ".jpg/960px-Loose_Grip_vs_Tight_Grip_-_Tight.jpg"),
    ("rack-position",
     f"{WM}/thumb/3/38/Kettlebell_Clean_and_Jerk_13_Rack"
     ".jpg/960px-Kettlebell_Clean_and_Jerk_13_Rack.jpg"),
    ("hip-hinge",
     f"{WM}/thumb/f/f0/Kettlebell_Clean_and_Jerk_5_HIp_"
     "Hinge.jpg/960px-Kettlebell_Clean_and_Jerk_5_HIp_"
     "Hinge.jpg"),
    ("rack-transition",
     f"{WM}/thumb/c/c5/Kettlebell_Clean_and_Jerk_12_Rack_"
     "Transition.jpg/960px-Kettlebell_Clean_and_Jerk_12_"
     "Rack_Transition.jpg"),
    ("jerk-drive",
     f"{WM}/thumb/a/af/Kettlebell_Clean_and_Jerk_17_Knee_"
     "Jerk_%28Push%29.jpg/960px-Kettlebell_Clean_and_Jerk_"
     "17_Knee_Jerk_%28Push%29.jpg"),
    ("jerk-lockout",
     f"{WM}/thumb/1/15/Kettlebell_Clean_and_Jerk19_Full-"
     "body_Lockout.jpg/960px-Kettlebell_Clean_and_Jerk19_"
     "Full-body_Lockout.jpg"),
    ("swing-top",
     f"{WM}/thumb/3/3b/Kettlebell_swing_with_arms_fully_"
     "extended.jpg/960px-Kettlebell_swing_with_arms_fully_"
     "extended.jpg"),
    ("swing-backswing",
     f"{WM}/thumb/8/80/Kettlebell_swing_with_arms_extended_"
     "upon_back_swing.jpg/960px-Kettlebell_swing_with_arms_"
     "extended_upon_back_swing.jpg"),
    ("clean-incorrect",
     f"{WM}/thumb/d/db/Incorrect_Kettlebell_Clean.jpg/"
     "960px-Incorrect_Kettlebell_Clean.jpg"),
    ("front-squat-bottom",
     f"{WM}/thumb/1/16/Kettlebell_Front_Squat_4_Full.jpg/"
     "960px-Kettlebell_Front_Squat_4_Full.jpg"),
    ("half-snatch-pull",
     f"{WM}/thumb/6/66/Kettlebell_Half_Snatch_7_Pull.jpg/"
     "960px-Kettlebell_Half_Snatch_7_Pull.jpg"),
    ("half-snatch-lockout",
     f"{WM}/thumb/6/67/Kettlebell_Half_Snatch_11_Lockout_-"
     "_Fixation.jpg/960px-Kettlebell_Half_Snatch_11_"
     "Lockout_-_Fixation.jpg"),
    ("turkish-get-up",
     f"{WM}/thumb/a/a2/Turkish_Get_Up.jpg/"
     "960px-Turkish_Get_Up.jpg"),
    ("snatch-physics",
     f"{WM}/thumb/1/1a/Snatch_Physics_by_Cavemantraining"
     ".jpg/960px-Snatch_Physics_by_Cavemantraining.jpg"),
    ("pavel-portrait",
     f"{WM}/a/a4/Pavel-tsatsouline.png"),
]

# Video thumbnails: (local name, YouTube video id)
THUMBNAILS = [
    ("video-goblet-squat", "FcTOmJW0G6U"),
    ("video-press", "78-gZ-y3vgA"),
    ("video-snatch", "fbm_zISdSbw"),
    ("video-long-cycle", "KyQsweWeofc"),
    ("video-jerk", "2EWDneXMCgI"),
    ("video-pendulum-swing", "-R7oJ2XUvcs"),
    ("video-clean", "rndZDA3vUnU"),
    ("video-hardstyle-swing", "ZYgRuQoh6Qc"),
    ("video-half-snatch", "UQb2A6qcTW8"),
    ("video-deadlift", "-N4NjwW7bGA"),
    ("video-lunge", "gWN9epxFqX8"),
    ("video-row", "8gg400ddt-g"),
    ("video-suitcase-carry", "m7iiTYfRy9A"),
    ("video-thruster", "n7jEYoIU9Zs"),
    ("video-windmill", "ITSmgn_BQgY"),
    ("video-bench-press", "4ULa6AJcjr8"),
    ("video-around-the-world", "N4mMVG8S5Kg"),
    ("video-atlas-swing", "ZXq_vq-F66c"),
    ("video-turkish-get-up", "5kb9Blkrj2w"),
    ("video-pavel-big-three", "6EX7nlyX4nY"),
    ("video-pavel-20-minute", "E0IOzN4AV7w"),
]

# Best first: YouTube serves 404 for sizes it does not have
THUMB_SIZES = ["maxresdefault", "sddefault", "hqdefault"]


# --------------------------------------------------------------
def log_message(message):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


# --------------------------------------------------------------
def existing_file(name):
    """Return existing image path for name, or None."""
    matches = glob.glob(os.path.join(IMAGES_DIR, f"{name}.*"))
    return matches[0] if matches else None


# --------------------------------------------------------------
def target_path(name, url):
    """Build local path for name using the URL extension."""
    ext = os.path.splitext(url)[1].lower()
    if ext not in ('.jpg', '.jpeg', '.png', '.webp'):
        ext = '.jpg'
    return os.path.join(IMAGES_DIR, f"{name}{ext}")


# --------------------------------------------------------------
def fetch_once(url):
    """Download URL once, returning bytes or an error."""
    request = urllib.request.Request(
        url,
        headers={'User-Agent': USER_AGENT}
    )
    try:
        with urllib.request.urlopen(request,
                                    timeout=TIMEOUT) as resp:
            return resp.read(), None
    except (urllib.error.URLError, OSError) as exc:
        return None, exc


# --------------------------------------------------------------
def fetch_bytes(url):
    """Download URL, backing off when the host throttles."""
    for attempt in range(1, MAX_TRIES + 1):
        data, exc = fetch_once(url)
        if data:
            return data
        code = getattr(exc, 'code', None)
        if code not in (429, 503) or attempt == MAX_TRIES:
            log_message(f"  failed: {exc}")
            return None
        wait = POLITE_DELAY * 2 ** attempt
        log_message(f"  throttled, waiting {wait:.0f}s")
        time.sleep(wait)
    return None


# --------------------------------------------------------------
def save_image(name, url, force):
    """Download one image unless it is already present."""
    present = existing_file(name)
    if present and not force:
        log_message(f"Skipping {name} - already have "
                    f"{os.path.basename(present)}")
        return False

    log_message(f"Downloading {name}")
    data = fetch_bytes(url)
    if not data:
        return False

    if present and force:
        os.remove(present)

    path = target_path(name, url)
    with open(path, 'wb') as handle:
        handle.write(data)

    size_kb = len(data) // 1024
    log_message(f"  saved {path} ({size_kb} KB)")
    return True


# --------------------------------------------------------------
def thumbnail_url(video_id):
    """Return the best available thumbnail URL, or None."""
    base = "https://img.youtube.com/vi"
    for size in THUMB_SIZES:
        url = f"{base}/{video_id}/{size}.jpg"
        request = urllib.request.Request(
            url,
            method='HEAD',
            headers={'User-Agent': USER_AGENT}
        )
        try:
            with urllib.request.urlopen(request,
                                        timeout=TIMEOUT):
                return url
        except (urllib.error.URLError, OSError):
            continue
    log_message(f"  no thumbnail found for {video_id}")
    return None


# --------------------------------------------------------------
def download_photos(force):
    """Download all technique photos."""
    count = 0
    for name, url in PHOTOS:
        if save_image(name, url, force):
            count += 1
            time.sleep(POLITE_DELAY)
    return count


# --------------------------------------------------------------
def download_thumbnails(force):
    """Download all video thumbnails."""
    count = 0
    for name, video_id in THUMBNAILS:
        if existing_file(name) and not force:
            log_message(f"Skipping {name} - already present")
            continue
        url = thumbnail_url(video_id)
        if url and save_image(name, url, force):
            count += 1
    return count


# --------------------------------------------------------------
def main():
    """Download every image needed by the guide."""
    force = '--force' in sys.argv

    log_message("Starting image download")
    os.makedirs(IMAGES_DIR, exist_ok=True)

    photos = download_photos(force)
    thumbs = download_thumbnails(force)

    log_message("=" * 50)
    log_message(f"Technique photos downloaded: {photos}")
    log_message(f"Video thumbnails downloaded: {thumbs}")
    log_message(f"Files now in {IMAGES_DIR}: "
                f"{len(os.listdir(IMAGES_DIR))}")
    log_message("Next: python3 s2_clean_images.py")


# --------------------------------------------------------------
if __name__ == "__main__":
    main()
