import os
import re
import json
import subprocess
import sys

VIDEO_EXTENSIONS = ('.mp4', '.mkv', '.avi', '.webm', '.flv', '.mov', '.wmv', '.mpg', '.mpeg', '.ts')
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg')
EPISODE_REGEX = r'[Ee][Pp]\.?(\d+)|-(\d+)(?=\.(?:mp4|mkv|avi|webm|flv|mov|wmv|mpg|mpeg|ts)$)'
SEASON_REGEX = r'[Ss]eason\s*(\d+)|[Ss](\d+)'
ANIME_JSON_FILE = "anime.json"
MIN_EPISODES_THRESHOLD = 1  # Keep at 1 for testing, adjust for production


def get_video_duration(filepath):
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            filepath
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        duration_str = result.stdout.strip()
        return float(duration_str) if duration_str else 0.0
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        sys.stderr.write(f"Warning: Could not get duration or file corrupted for: {filepath}\n")
        return 0.0


def extract_episode_number(filename):
    match = re.search(EPISODE_REGEX, filename, re.IGNORECASE)
    if match:
        if match.group(1):
            return int(match.group(1))
        elif match.group(2):
            return int(match.group(2))
    return None


def extract_season_number(foldername):
    match = re.search(SEASON_REGEX, foldername, re.IGNORECASE)
    if match:
        if match.group(1):
            return int(match.group(1))
        elif match.group(2):
            return int(match.group(2))
    return None


def find_banner_picture(folder_path, filename_prefix="banner"):
    for ext in IMAGE_EXTENSIONS:
        banner_path = os.path.join(folder_path, f"{filename_prefix}{ext}")
        if os.path.exists(banner_path):
            return banner_path
    return None


def _process_single_anime_directory(anime_series_path):
    series_seasons = []
    series_banner = find_banner_picture(anime_series_path)

    potential_season_folders = []
    for item_name in os.listdir(anime_series_path):
        item_path = os.path.join(anime_series_path, item_name)
        if os.path.isdir(item_path):
            season_number = extract_season_number(item_name)
            if season_number is not None:
                potential_season_folders.append((season_number, item_name, item_path))


    potential_season_folders.sort(key=lambda x: x[0])

    if potential_season_folders:

        for season_num, season_name, season_path in potential_season_folders:
            season_banner = find_banner_picture(season_path)
            episodes_in_season = []
            for filename in os.listdir(season_path):
                if filename.lower().endswith(VIDEO_EXTENSIONS):
                    filepath = os.path.join(season_path, filename)
                    episode_number = extract_episode_number(filename)
                    if episode_number is not None:
                        duration = get_video_duration(filepath)
                        if duration > 0:  # Only add if duration is positive (valid video)
                            episodes_in_season.append({
                                "episode_number": episode_number,
                                "file_name": filename,
                                "file_path": filepath,
                                "duration_seconds": duration
                            })

            if len(episodes_in_season) >= MIN_EPISODES_THRESHOLD:
                series_seasons.append({
                    "season_number": season_num,
                    "season_folder_name": season_name,
                    "season_folder_path": season_path,
                    "banner_picture": season_banner,
                    "episodes": sorted(episodes_in_season, key=lambda x: x["episode_number"])
                })
    else:

        episodes_in_root = []
        for filename in os.listdir(anime_series_path):
            if filename.lower().endswith(VIDEO_EXTENSIONS):
                filepath = os.path.join(anime_series_path, filename)
                episode_number = extract_episode_number(filename)
                if episode_number is not None:
                    duration = get_video_duration(filepath)
                    if duration > 0:  # Only add if duration is positive (valid video)
                        episodes_in_root.append({
                            "episode_number": episode_number,
                            "file_name": filename,
                            "file_path": filepath,
                            "duration_seconds": duration
                        })

        if len(episodes_in_root) >= MIN_EPISODES_THRESHOLD:

            series_seasons.append({
                "season_number": 1,
                "season_folder_name": os.path.basename(anime_series_path),  # Use series folder name for implicit season
                "season_folder_path": anime_series_path,
                "banner_picture": series_banner,  # Use series banner for implicit season
                "episodes": sorted(episodes_in_root, key=lambda x: x["episode_number"])
            })

    return series_seasons, series_banner


def index_anime_folders(base_folder):
    indexed_animes = []

    if not os.path.isdir(base_folder):
        sys.stderr.write(f"Error: Base folder '{base_folder}' does not exist or is not a directory.\n")
        return 0





    contains_season_subfolders = any(
        os.path.isdir(os.path.join(base_folder, item)) and extract_season_number(item) is not None
        for item in os.listdir(base_folder)
    )


    contains_direct_episodes = any(
        os.path.isfile(os.path.join(base_folder, item)) and item.lower().endswith(
            VIDEO_EXTENSIONS) and extract_episode_number(item) is not None
        for item in os.listdir(base_folder)
    )

    if contains_season_subfolders or contains_direct_episodes:


        series_seasons, series_banner = _process_single_anime_directory(base_folder)
        if series_seasons:  # Only add if actual seasons/episodes were found
            indexed_animes.append({
                "name": os.path.basename(base_folder),  # Name derived from the base_folder's name
                "folder_path": base_folder,
                "banner_picture": series_banner,
                "seasons": series_seasons
            })
    else:
        # Case 2: The base_folder is a higher-level folder, iterate its subdirectories for anime series
        for anime_series_name in os.listdir(base_folder):
            anime_series_path = os.path.join(base_folder, anime_series_name)

            if not os.path.isdir(anime_series_path):
                continue  # Skip files directly in the base_folder; we only care about sub-folders as potential series

            # Process each subdirectory as a potential anime series
            series_seasons, series_banner = _process_single_anime_directory(anime_series_path)

            if series_seasons:  # Only add if actual seasons/episodes were found in this subdirectory
                indexed_animes.append({
                    "name": anime_series_name,
                    "folder_path": anime_series_path,
                    "banner_picture": series_banner,
                    "seasons": series_seasons
                })

    # --- Merge with existing anime.json data ---
    current_anime_data = {"animes": []}
    if os.path.exists(ANIME_JSON_FILE):
        try:
            with open(ANIME_JSON_FILE, "r") as f:
                current_anime_data = json.load(f)
        except json.JSONDecodeError:
            sys.stderr.write(f"Warning: {ANIME_JSON_FILE} is corrupted or empty. Starting fresh.\n")

    # Create a map of existing anime by folder_path for efficient updates
    existing_anime_map = {anime["folder_path"]: anime for anime in current_anime_data["animes"]}

    for new_anime in indexed_animes:
        if new_anime["folder_path"] in existing_anime_map:
            # Update existing entry with new details (e.g., if episodes/seasons changed)
            existing_entry = existing_anime_map[new_anime["folder_path"]]
            existing_entry["seasons"] = new_anime["seasons"]
            existing_entry["name"] = new_anime["name"]
            existing_entry["banner_picture"] = new_anime["banner_picture"]
        else:
            # Add new anime entry
            current_anime_data["animes"].append(new_anime)

    # Sort the final list of anime by name
    current_anime_data["animes"].sort(key=lambda x: x.get("name", "").lower())

    # Save the updated anime data to JSON file
    with open(ANIME_JSON_FILE, "w") as f:
        json.dump(current_anime_data, f, indent=4)

    sys.stdout.write(f"Indexed {len(indexed_animes)} anime series.\n")
    return len(indexed_animes)