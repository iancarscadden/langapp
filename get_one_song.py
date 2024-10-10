
# THIS SCRIPT CAN BE USED / REPLACED WITH THINGS TO GET JUST ONE SONG WITH THIS LYRICS VIA LYRICSGENUIS

import os
import json
import time
import re
import lyricsgenius
from dotenv import load_dotenv
from requests.exceptions import ReadTimeout, ConnectionError

# Load environment variables from .env
load_dotenv()
GENIUS_API_TOKEN = os.getenv("GENIUS_API_TOKEN")

if not GENIUS_API_TOKEN:
    raise ValueError("Please set the GENIUS_API_TOKEN in your .env file.")

# Initialize the Genius client with increased timeout
genius = lyricsgenius.Genius(
    GENIUS_API_TOKEN,
    timeout=15,  # Increase timeout to 15 seconds
    retries=3,    # Number of retries on failure
    sleep_time=5, # Time to wait between retries in seconds
    remove_section_headers=True,  # Removes [Chorus], [Verse], etc.
    skip_non_songs=True,          # Skips tracks that aren't songs
    excluded_terms=["(Remix)", "(Live)"]  # Exclude live or remix versions
)

# List of songs to fetch (only the new song)
songs_to_fetch = [
    {
        "id": "3",  # Assuming you're replacing the existing song with id "3"
        "language": "Spanish",
        "artist": "Don Omar, Zion & Lennox",
        "song": "Te Quiero Pa’ Mí"
    }
]

def clean_lyrics(lyrics):
    """
    Cleans the lyrics by removing unwanted sections and annotations.
    """
    # Remove bracketed text (e.g., [Chorus], (Verse))
    lyrics = re.sub(r'[\[\(].*?[\]\)]', '', lyrics)

    # Remove unwanted lines
    unwanted_phrases = [
        'Contributors',
        'Translations',
        'You might also like',
        'Embed',
        'See ',
        'Get tickets',
        'English',
        'Deutsch',
        '1 Contributor',
        '1 Translation'
    ]
    lines = lyrics.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if any(phrase in line for phrase in unwanted_phrases):
            continue
        cleaned_lines.append(line)

    # Remove extra whitespace and empty lines
    cleaned_lyrics = '\n'.join(cleaned_lines).strip()
    return cleaned_lyrics


def fetch_and_store_lyrics(songs, output_file='te_quiero_pa_mi.json'):
    """
    Fetches lyrics for the given songs and stores them in a JSON file.
    """
    fetched_songs = []
    for song in songs:
        print(f"Fetching lyrics for '{song['song']}' by {song['artist']}...")
        attempts = 0
        while attempts < genius.retries:
            try:
                # To handle multiple artists, concatenate them with ' & ' or ' and '
                # Alternatively, you can try searching with just the main artist first
                fetched_song = genius.search_song(song['song'], song['artist'])
                if fetched_song and fetched_song.lyrics:
                    lyrics = fetched_song.lyrics
                    cleaned_lyrics = clean_lyrics(lyrics)
                    fetched_songs.append({
                        "id": song["id"],
                        "language": song["language"],
                        "artist": song["artist"],
                        "song": song["song"],
                        "lyrics": cleaned_lyrics
                    })
                    print(f"Successfully fetched lyrics for '{song['song']}'.\n")
                else:
                    print(f"Lyrics not found for '{song['song']}' by {song['artist']}'.\n")
                break  # Exit retry loop whether successful or not
            except (ReadTimeout, ConnectionError) as e:
                attempts += 1
                print(f"Attempt {attempts} - Error fetching lyrics: {e}")
                if attempts < genius.retries:
                    print("Retrying...\n")
                    time.sleep(genius.sleep_time)
                else:
                    print(f"Failed to fetch lyrics for '{song['song']}' after {genius.retries} attempts.\n")
            except Exception as e:
                print(f"An unexpected error occurred: {e}\n")
                break  # Do not retry on unexpected errors

        # Optional: Delay between requests to respect rate limits
        time.sleep(2)  # Sleep for 2 seconds

    # Save fetched lyrics to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(fetched_songs, f, ensure_ascii=False, indent=4)
    print(f"All lyrics have been fetched and stored in '{output_file}'.")


if __name__ == "__main__":
    fetch_and_store_lyrics(songs_to_fetch)
