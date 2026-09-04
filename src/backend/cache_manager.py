from pathlib import Path
from urllib.parse import urlparse
import requests
import json
from . import library


# Default Values
CACHE_FILE_TEMPLATE = { "animes": {} }


# Checks if a string is an URL or a path
def is_url(value):
    parsed_value = urlparse(str(value))
    return parsed_value.scheme in ("http", "https") and bool(parsed_value.netloc)


# Download and Cache an Image according to ID and path
def download_image(url, save_folder, id):
    try:
        # Call center
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()

        # If the folder is gone for whatever reason re-create it
        save_folder.mkdir(parents=True, exist_ok=True)

        # Get the file extension of the image
        image_extension = Path(urlparse(url).path).suffix.lower()

        # Set the save path
        save_path = save_folder.joinpath(id+image_extension)

        # If the image already exist, skip it
        if save_path.exists(): return str(save_path)

        # Save the image
        with save_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return str(save_path)
    
    except requests.exceptions.RequestException as e:
        print(f"Cache Manager Debug: Failed to download image {url}: {e}")
    
    return None



# Manages all the cache from Anime Metadata
class CacheManager:
    def __init__(self, appdata_path):
        # Set Paths
        self.APPDATA_PATH = Path(appdata_path).expanduser()
        self.CACHE_PATH = self.APPDATA_PATH.joinpath("cache")
        self.CACHE_FILE = self.CACHE_PATH.joinpath("cache.json")
        self.CACHE_COVERS = self.CACHE_PATH.joinpath("covers")

        print("Cache Manager Debug - Cache Path:", self.CACHE_PATH)
        print("Cache Manager Debug - Cache File:", self.CACHE_FILE, "/ Exists:", self.CACHE_FILE.exists())
        print("Cache Manager Debug - Cache Covers:", self.CACHE_COVERS)

        # Create the folders if they don't exist
        self.CACHE_PATH.mkdir(parents=True, exist_ok=True)
        self.CACHE_COVERS.mkdir(parents=True, exist_ok=True)

        # If cache.json doesn't exist in CACHE_PATH, create it
        if not self.CACHE_FILE.exists():
            print("Cache Manager Debug: Cache file not detected, creating one automatically!")
            template = CACHE_FILE_TEMPLATE.copy()
            with self.CACHE_FILE.open("w") as f:
                json.dump(template, f, indent=4)
        
        # Load the file
        with self.CACHE_FILE.open("r", encoding="utf-8") as f:
            try:
                self.cache: dict = json.load(f)
            except (json.JSONDecodeError, ValueError):
                print("Cache Manager Debug - Cache file was empty or corrupted. Using default values")
                self.cache = CACHE_FILE_TEMPLATE.copy()

    # Get the metadata from ID
    def get_anime_from_id(self, id):
        if id in self.cache["animes"].keys():
            return self.cache["animes"][id]

        print(f"Cache Manager Debug - Get anime from ID: Could not find ID {id}!")
        return None
    
    # Get the metadata from Path
    def get_anime_from_path(self, path):
        for id in self.cache["animes"].keys():
            if path == self.cache["animes"][id]["path"]:
                return id
        
        print(f"Cache Manager Debug - Get anime from Path: Could not find Anime with Path {path}!")
        return None

    # Add anime metadata to cache (Get from Library get_anime_metadata)
    def set_anime(self, data):
        # If it's a string, it means the anime was not found on AniList.
        if isinstance(data, str):
            anime_name = Path(data).name

            # If anime name already in cache, skip it
            for id in self.cache["animes"].keys():
                if anime_name == self.cache["animes"][id]["title"]["english"]:
                    print(f"Cache Manager Debug - ID {id} already exists in cache. Skipping")
                    return
            
            # If not found, set default values
            data = library.get_fallback_template(data, self.cache["animes"].keys())

            print(f"Cache Manager Debug - Setting default template for {anime_name}")
        
        # If it's None, then give them nothing
        if data is None:
            print(f"Cache Manager Debug - Unable to cache value None to cache.")
            return
        
        # A Dict was provided
        # make sure there's actually an ID in the provided data
        if "id" in data.keys():
            # Create a copy of data
            data = data.copy()

            # Set ID and remove from original data
            id = str(data["id"]); data.pop("id")

            # Skip if it already exists in cache
            if id in self.cache["animes"].keys(): 
                print(f"Cache Manager Debug - ID {id} already exists in cache. Skipping")
                return

            # Download the images and replace the Image links with cached local paths unless it's already local
            cover_link = data["coverImage"]["extraLarge"]
            
            if is_url(cover_link):
                img_path = download_image(cover_link, self.CACHE_COVERS, id)
                data["image"] = img_path
            else:
                data["image"] = data["coverImage"]["extraLarge"]

            # Add data to cache
            self.cache["animes"][id] = data
        else:
            print(f"Cache Manager Debug - Unable to set a cache item because of an empty json provided! Json Provided: {data}")
    
    # Save the current cache to file
    def save(self):
        with self.CACHE_FILE.open("w") as f:
            json.dump(self.cache, f, indent=4)


if __name__ == "__main__":
    # Testing purposes
    cache_manager = CacheManager("~/.local/share/PolarTea Studios/PTBAnime")

    animes = library.scan_anime_folder("/run/media/polar/Skibidi Riz/ani-cli/anime")

    anime_metadatas = []
    for anime in animes:
        # If anime already in cache, don't add it to get processed
        if cache_manager.get_anime_from_path(anime): 
            print(f"Cache Manager Debug: Anime {Path(anime).name} already in Cache, skipping.")
            continue

        anime_metadatas.append(library.get_anime_metadata(Path(anime)))
    
    # Set Cache
    for anime_metadata in anime_metadatas:
        cache_manager.set_anime(anime_metadata)
    
    cache_manager.save()
