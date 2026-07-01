"""
background_generator.py — Download background images for scene compositing.

Populates the backgrounds/ directory with real-world photos that the
synthetic data generator composites rendered objects onto. Add or replace
URLs below to change the background set.
"""

import os
import requests

urls = [
    "https://upload.wikimedia.org/wikipedia/commons/0/08/Kitchen_Background_1.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/9/94/Kitchen_Background_2.jpg",
    # Add more image URLs here to expand the background set.
]

headers = {"User-Agent": "Mozilla/5.0 (DataGenBot/1.0)"}
os.makedirs("backgrounds", exist_ok=True)

for i, url in enumerate(urls):
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        with open(f"backgrounds/bg_{i}.jpg", "wb") as f:
            f.write(r.content)
        print(f"Saved backgrounds/bg_{i}.jpg")
    except Exception as e:
        print(f"Failed: {url.split('/')[-1]} — {e}")
