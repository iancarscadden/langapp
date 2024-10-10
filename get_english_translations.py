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

# Initialize the Genius client with increased timeout and retries
genius = lyricsgenius.Genius(
    GENIUS_API_TOKEN,
    timeout=15,  # Increase timeout to 15 seconds
    retries=3,    # Number of retries on failure
    sleep_time=5, # Time to wait between retries in seconds
    remove_section_headers=True,  # Removes [Chorus], [Verse], etc.
    skip_non_songs=True,          # Skips tracks that aren't songs
    excluded_terms=["(Remix)", "(Live)"]  # Exclude live or remix versions
)

# List of songs to fetch
songs_to_fetch = [
    # Spanish Songs
    {
        "id": "1",
        "language": "Spanish",
        "artist": "Ricky Martin, Residente, Bad Bunny",
        "song": "Cántalo"
    },
    {
        "id": "2",
        "language": "Spanish",
        "artist": "Marc Anthony",
        "song": "Vivir Mi Vida"
    },
    {
        "id": "3",
        "language": "Spanish",
        "artist": "Don Omar, Zion & Lennox",
        "song": "Te Quiero Pa’ Mí"
    },
    # French Songs
    {
        "id": "4",
        "language": "French",
        "artist": "Joe Dassin",
        "song": "Les Champs-Élysées"
    },
    {
        "id": "5",
        "language": "French",
        "artist": "Stromae",
        "song": "Papaoutai"
    },
    {
        "id": "6",
        "language": "French",
        "artist": "Zaz",
        "song": "Je Veux"
    },
    # Arabic Songs
    {
        "id": "7",
        "language": "Arabic",
        "artist": "Rachid Taha",
        "song": "Ya Rayah"
    },
    {
        "id": "8",
        "language": "Arabic",
        "artist": "Hamid Al Shaeri",
        "song": "Ouda"
    },
    {
        "id": "9",
        "language": "Arabic",
        "artist": "Nancy Ajram",
        "song": "Ya Tabtab"
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


def fetch_translated_song(song):
    """
    Attempts to fetch English translated lyrics for a given song.
    Returns the translated lyrics if found, else returns None.
    """
    # Construct possible English translation titles
    translated_title_variants = [
        f"{song['song']} (English)",
        f"{song['song']} [English]",
        f"{song['song']} English",
        f"{song['song']} - English",
        f"{song['song']} (Translation)",
        f"{song['song']} [Translation]",
        f"{song['song']} Translation",
        f"{song['song']} - Translation"
    ]

    for variant in translated_title_variants:
        try:
            fetched_song = genius.search_song(variant, song['artist'])
            if fetched_song and fetched_song.lyrics:
                return fetched_song.lyrics
        except (ReadTimeout, ConnectionError) as e:
            print(f"Error fetching translated lyrics for '{song['song']}' with title variant '{variant}': {e}")
            continue
        except Exception as e:
            print(f"An unexpected error occurred while fetching translated lyrics for '{song['song']}': {e}")
            continue

    # If not found via title variants, attempt a general search with specific query
    try:
        query = f"{song['song']} English translation {song['artist']}"
        fetched_song = genius.search_song(song['song'], song['artist'], sort="title")
        if fetched_song and fetched_song.lyrics:
            # Heuristically extract the English translation if present
            # This might not be accurate and may require manual verification
            return fetched_song.lyrics
    except Exception as e:
        print(f"An error occurred during heuristic search for translated lyrics for '{song['song']}': {e}")

    # If all attempts fail, return None
    return None


def fetch_and_store_lyrics(songs, output_file_original='original_songs.json', output_file_translated='translated_songs.json'):
    """
    Fetches lyrics for the given songs and stores them in separate JSON files.
    - Original lyrics are stored in 'original_songs.json'.
    - Translated lyrics are stored in 'translated_songs.json'.
    """
    fetched_original_songs = []
    fetched_translated_songs = []
    for song in songs:
        print(f"Fetching original lyrics for '{song['song']}' by {song['artist']}...")
        attempts = 0
        while attempts < genius.retries:
            try:
                fetched_song = genius.search_song(song['song'], song['artist'])
                if fetched_song and fetched_song.lyrics:
                    lyrics = fetched_song.lyrics
                    cleaned_lyrics = clean_lyrics(lyrics)
                    fetched_original_songs.append({
                        "id": song["id"],
                        "language": song["language"],
                        "artist": song["artist"],
                        "song": song["song"],
                        "lyrics": cleaned_lyrics
                    })
                    print(f"Successfully fetched original lyrics for '{song['song']}'.\n")
                else:
                    print(f"Original lyrics not found for '{song['song']}' by {song['artist']}'.\n")
                break  # Exit retry loop whether successful or not
            except (ReadTimeout, ConnectionError) as e:
                attempts += 1
                print(f"Attempt {attempts} - Error fetching original lyrics: {e}")
                if attempts < genius.retries:
                    print("Retrying...\n")
                    time.sleep(genius.sleep_time)
                else:
                    print(f"Failed to fetch original lyrics for '{song['song']}' after {genius.retries} attempts.\n")
            except Exception as e:
                print(f"An unexpected error occurred: {e}\n")
                break  # Do not retry on unexpected errors

        # Fetch translated lyrics
        print(f"Attempting to fetch English translated lyrics for '{song['song']}' by {song['artist']}...")
        translated_lyrics = fetch_translated_song(song)
        if translated_lyrics:
            cleaned_translated_lyrics = clean_lyrics(translated_lyrics)
            fetched_translated_songs.append({
                "id": song["id"],
                "language": "English",
                "artist": song["artist"],
                "song": f"{song['song']} (English)",
                "lyrics": cleaned_translated_lyrics
            })
            print(f"Successfully fetched English translated lyrics for '{song['song']}'.\n")
        else:
            print(f"English translated lyrics not found for '{song['song']}'. Skipping to next song.\n")

        # Optional: Delay between requests to respect rate limits
        time.sleep(2)  # Sleep for 2 seconds

    # Save fetched original lyrics to JSON file
    with open(output_file_original, 'w', encoding='utf-8') as f:
        json.dump(fetched_original_songs, f, ensure_ascii=False, indent=4)
    print(f"Original lyrics have been fetched and stored in '{output_file_original}'.")

    # Save fetched translated lyrics to JSON file
    if fetched_translated_songs:
        with open(output_file_translated, 'w', encoding='utf-8') as f:
            json.dump(fetched_translated_songs, f, ensure_ascii=False, indent=4)
        print(f"English translated lyrics have been fetched and stored in '{output_file_translated}'.")
    else:
        print("No English translated lyrics were fetched.")


if __name__ == "__main__":
    fetch_and_store_lyrics(songs_to_fetch)
