# 📹 PTBAnime

PTBAnime is a cool personal anime library manager and player built in Python using **GTK4**. Developed by two friends, [PolarT-py](https://github.com/PolarT-py) and [TBG09](https://github.com/TBG09), it's a modern (not really) and minimalist (not really) desktop app for watching and tracking your local anime collection.

---

## 🧩 Features

- 🎞️ Oogly grid layout for browsing your collection
- 🖼️ Cover thumbnails (Yes)
- 🔍 Built-in search functionality
- 🧠 Memory-efficient GTK4 design (Just kidding about this part)
- 🛠️ Hardly extensible with Python (Just fork the project 😭)
- 💾 Worst code you've ever seen

---

## 📸 Screenshot

> *Coming later*  
> A preview of our unclean and slow UI is on the way :D

---

## 🚀 Getting Started

### Requirements

- Python 3
- GTK 4 (with Python bindings)
- Gobject PyGObject PyGobject-stubs

### Setup
You need to select the folder all your anime videos is in. 
<pre>
your-anime-folder/            # Root anime folder (set in settings)
├── Dragon Ball A/            # Each folder = one anime
│   ├── cover.png             # Cover image, you need to add your own cover.png
│   ├── PTBAnime-data.json    # Metadata (Auto-generated)
│   ├── Episode 01.mp4        # Episodes, every video file will be interpreted as a episode
│   ├── Episode 02.mp4        #
│   └── ...
├── Two Piece/
│   ├── cover.png
│   ├── PTBAnime-data.json
│   ├── Two Piece - Ep1.mp4
│   └── ...
└── Defend on little people/
    ├── cover.png
    ├── PTBAnime-data.json
    ├── 01 - Auto Memories.mp4
    └── ...</pre>

## ❗ Disclaimer

PTBAnime is for personal use only. It does not stream or download anime from the internet. You must provide your own files. PTBAnime is developed **just** for fun. 
