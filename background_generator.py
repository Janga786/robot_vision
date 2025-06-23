import os, requests

urls = [
    "https://upload.wikimedia.org/wikipedia/commons/0/08/Kitchen_Background_1.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/9/94/Kitchen_Background_2.jpg",
    # …add more links if you like
]

headers = {"User-Agent": "Mozilla/5.0 (DataGenBot/1.0)"}
os.makedirs("backgrounds", exist_ok=True)

for i, url in enumerate(urls):
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        with open(f"backgrounds/bg_{i}.jpg", "wb") as f:
            f.write(r.content)
        print(f"✅ bg_{i}.jpg")
    except Exception as e:
        print(f"❌ {url.split('/')[-1]} — {e}")

