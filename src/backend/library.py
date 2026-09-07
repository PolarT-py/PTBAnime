from pathlib import Path
from urllib.parse import urlparse
from random import randint
from copy import deepcopy
import json, requests, time


# The library backend will search your provided Anime folder.
# It will take each subfolder's title and search it on AniList.
# It fetches the Native, Romanized and English title versions, the cover, and the description of the Anime.
# After that, it will cache the data in it's own folder called .PTBAnime
# If it cannot fetch any data, it will use the placeholder cover, and folder name for it's name.


# Add in future:
# - Switch from AniList to Jikan for a higher rate limit of 60r/m
# - Make it so animes that are found but don't have fetched metadata use a blank image and sit there until they receive their cover and stuff


# Set Paths
BASE_DIR = Path(__file__).parent.parent.parent.resolve()
FALLBACK_THUMBNAIL = str(BASE_DIR.joinpath(Path("assets/images/anime_card_thumbnail.png")))


# Requests timing stuff
last_request_time = 0.0
MIN_REQUEST_INTERVAL = 60 / 28  # Limit to 28 requests per minute so it doesn't hit AniList's current 30 requests rate limit


# Fallback Template. Do not copy directly!
FALLBACK_TEMPLATE = {
    "id": 0,  # Randomized in a function
    "title": {
        "romaji": "Idk",
        "english": "Idk",
        "native": "Idk"
    },
    "coverImage": {
        "extraLarge": FALLBACK_THUMBNAIL,
        "color": "#000000"
    },
    "type": "ANIME",
    "status": "Unknown",
    "episodes": 0,
    "seasonYear": 2000,
    "genres": [],
    "averageScore": 50,
    "description": "This Anime was not found on AniList, so now it's using a fallback template. Make sure to the folder name correctly spelled (English, romaji, or native) and fetch again. You can also manually set these values.",
    "path": "?",
    "is_fallback": True,
    "visible": True  # Decides if it shows up in the Library
}


# Get the list of visible animes sorted by name for Home Page Grid from cache
# Filtered by search too
def get_home_page_grid(cache, search_filter):
    l = []

    for anime_id, anime in cache["animes"].items():
        if anime.get("visible", True):
            # Filter out ones that don't fit the search
            qualified = False
            search_filter = search_filter.lower()

            if search_filter in anime["title"]["english"].lower() or search_filter in anime["title"]["romaji"].lower() or search_filter in anime["title"]["native"].lower():
                qualified = True
            
            if search_filter in anime["description"].lower():
                qualified = True
            
            for word in search_filter:
                if word in anime["genres"]:
                    qualified = True; break
            
            if not qualified: continue

            # Fix null colors by setting them to black
            if anime["coverImage"]["color"] is None:
                anime["coverImage"]["color"] = "#000000"
            
            # Add an ID to it just for the library
            anime["id"] = int(anime_id)
            l.append(anime)

    return l


# Get fallback template
def get_fallback_template(anime_path, existing_ids):
    # Make a copy of the template
    template = deepcopy(FALLBACK_TEMPLATE)

    # Set anime name
    if isinstance(anime_path, str):
        anime_name = Path(anime_path).name
    else:
        anime_name = anime_path.name

    # Set it's names to the folder name
    title = template["title"]
    title["english"] = anime_name; title["romaji"] = anime_name; title["native"] = anime_name

    # Set the path
    template["path"] = str(anime_path)

    # Give it a random ID from 2,000,000 to 2,100,000 that's not already taken
    while True:
        random_id = randint(1_000_001, 1_100_000)
        if random_id not in existing_ids: break
    
    template["id"] = str(random_id)

    return template


# Scan the entire Anime folder
# Get all detected Anime paths back
def scan_anime_folder(provided_path):
    if not isinstance(provided_path, str):
        print("The provided path to Anime Folder is invalid:", provided_path)
        return None

    # Parse it from a URL to Path
    anime_folder = Path(urlparse(provided_path).path)

    # print("Library Debug - Provided Path:", provided_path)
    print("Library Debug - Clean Path:", anime_folder)

    # Check for all subfolders
    found_subfolders = [p for p in anime_folder.rglob("*/") if p.is_dir()]

    # print("Library Debug - All Subfolders:", found_subfolders)

    # Filter out non-anime folders by checking if they have mp4/mkv/mov/webm files in them
    animes = []

    for subfolder in found_subfolders:
        for file in subfolder.iterdir():
            if file.suffix.lower() in (".mp4", ".mkv", ".mov", ".webm"):
                animes.append(str(subfolder))
                break
    
    print("Library Debug - Found Animes:", animes)

    return animes


# Fetch anime metadata by anime name on AniList
# Return available metadata. If can't find any, return default values
def get_anime_metadata(anime_path):
    global last_request_time

    # Make sure it throttles for the rate limit
    elapsed = time.time() - last_request_time
    if elapsed < MIN_REQUEST_INTERVAL:
        time.sleep(MIN_REQUEST_INTERVAL - elapsed)

    if isinstance(anime_path, str):
        anime_name = Path(anime_path).name
    else:
        anime_name = anime_path.name
    
    # Create query and headers
    query = """
query ($search: String) {
  Media (search: $search, type: ANIME) {
    id
    title {
      romaji
      english
      native
    }
    coverImage {
        extraLarge
        color
    }
    type
    status
    episodes
    seasonYear
    genres
    averageScore
    description
  }
}
"""
    try:
        # Attempt to send a request
        response = requests.post("https://graphql.anilist.co", json={"query": query, "variables": {"search": anime_name}})

        # Store last request time
        last_request_time = time.time()

        # Extract metadata
        anime_metadata = response.json()

        # If there are errors, it probably means it just can't find it
        # Not sure how, but might add a looser way of searching in the future
        if "errors" in anime_metadata:
            print(f"Library Debug: ! Could not find the Anime you were looking for on AniList. Please make sure the folder name is correct. Hint: You might be sending too many requests too quickly, try again in a minute. Provided name: {anime_name}")
            print(f"Library Debug: ! ^ The error: {anime_metadata}")
            return str(anime_path)

        print(f"Library Debug: Found Anime on AniList: {anime_name}")

        # If there's no English name, use the romanized name as fallback
        title = anime_metadata["data"]["Media"]["title"]
        if title["english"] is None: title["english"] = title["romaji"]

        # Add the path to where the Anime was found
        anime_metadata["data"]["Media"]["path"] = str(anime_path)

        # Set it as not a fallback
        anime_metadata["data"]["Media"]["is_fallback"] = False

        return anime_metadata["data"]["Media"]
    
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while trying to fetch Anime metadata: {e}")
    
    return str(anime_path)


if __name__ == "__main__":
    print("Debugging for Library")

    # Test fetch data
    test = get_anime_metadata("/run/media/polar/Skibidi Riz/ani-cli/anime/Mission Yozakura Family/")
    if isinstance(test, dict):
        print("Library Debug - Anime Metadata:", json.dumps(test, indent=4))
        # print("Library Debug - Description:", test["description"])
    else:
        print("Library Debug - Anime Metadata: Anime not found!")
