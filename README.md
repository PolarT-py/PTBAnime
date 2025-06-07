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
- GTK 4
- GObject
- PyGObject
- ffmpeg-python

Make sure you have python 3 installed on your computer, and install `GObject`, `PyGobject` and `ffmpeg-python` via `pip`. Then you have to install GTK onto your system, if you are a Windows user you do not have to worry, but for Linux and Mac users you have to install it manually. For Linux users, install it via your favorite package manager or build it yourself https://www.gtk.org/docs/installations/linux/, and for Mac users check out how to install here: https://www.gtk.org/docs/installations/macos/

### Setup
You will need to do a lot of manual work to make everything look pretty, you need to select the folder all your anime videos is in, which is the easy part. You also then have to edit PTBAnime-info files to add a Title and Description, and also a cover image, in the form of a png/jpg. 
<pre>
your-anime-folder/            # Root anime folder (set in settings)
├── Dragon Ball A/            # Each folder = one anime
│   ├── cover.png             # Cover image, you need to add your own cover.png
│   ├── PTBAnime-data.json    # Metadata (Auto-generated), but change the values yourself
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

PTBAnime is for personal use only. It does not stream or download anime from the internet. You must provide your own files. PTBAnime is developed **just** for fun, we will still look at bugs/feature requests, but it's not guaranteed we will implement them. 
