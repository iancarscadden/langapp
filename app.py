import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import openai
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# Load API keys from environment variables
GENIUS_API_TOKEN = os.environ.get("GENIUS_API_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Initialize the OpenAI API key
openai.api_key = OPENAI_API_KEY


# Load songs data from JSON and organize by language
def load_songs():
    with open('songs.json', 'r', encoding='utf-8') as f:
        songs_list = json.load(f)
    # Organize songs by language
    songs_by_language = {}
    for song in songs_list:
        language = song['language'].lower()  # Normalize language to lowercase
        if language not in songs_by_language:
            songs_by_language[language] = []
        songs_by_language[language].append({
            'id': song['id'],
            'artist': song['artist'],
            'song': song['song'],
            'lyrics': song['lyrics']
        })
    return songs_by_language


songs_data = load_songs()


# Route for Welcome Page
@app.route('/')
def welcome():
    return render_template('welcome.html')


# Route for Choose Language Page
@app.route('/choose-language', methods=['GET', 'POST'])
def choose_language():
    if request.method == 'POST':
        selected_language = request.form.get('language').lower()
        if selected_language in songs_data:
            return redirect(url_for('choose_song', language=selected_language))
        else:
            error = "Selected language is not available."
            available_languages = [lang.capitalize() for lang in songs_data.keys()]
            return render_template('choose_language.html', languages=available_languages, error=error)
    # Capitalize language names for display
    available_languages = [lang.capitalize() for lang in songs_data.keys()]
    return render_template('choose_language.html', languages=available_languages)


# Route for Choose Song Page
@app.route('/choose-song/<language>', methods=['GET', 'POST'])
def choose_song(language):
    language = language.lower()
    if language not in songs_data:
        return redirect(url_for('choose_language'))

    if request.method == 'POST':
        selected_song_id = request.form.get('song_id')
        # Find the song by ID
        selected_song = next((song for song in songs_data[language] if song['id'] == selected_song_id), None)
        if selected_song:
            return render_template('lyrics.html', language=language.capitalize(), song=selected_song['song'],
                                   lyrics=selected_song['lyrics'], artist=selected_song['artist'])
        else:
            error = "Selected song not found."
            song_titles = [song['song'] for song in songs_data[language]]
            return render_template('choose_song.html', language=language.capitalize(), songs=songs_data[language],
                                   error=error)

    # Pass the list of song dictionaries to the template
    return render_template('choose_song.html', language=language.capitalize(), songs=songs_data[language])


# Route to handle OpenAI API call (Explanation Feature)
@app.route("/explain", methods=["POST"])
def explain():
    selected_text = request.json.get("text", "")
    if selected_text:
        explanation = get_explanation(selected_text)
        return jsonify({"explanation": explanation})
    else:
        return jsonify({"error": "No text selected."}), 400


# Function to get explanation from OpenAI API
def get_explanation(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Ensure you have access to GPT-4
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user",
                 "content": f"Explain how the following phrase is used in normal conversations, keep it short:\n\n'{text}'"}
            ],
            max_tokens=100,
            temperature=0.7,
        )
        explanation = response['choices'][0]['message']['content'].strip()
        return explanation
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return "An error occurred while fetching the explanation."


if __name__ == "__main__":
    app.run(debug=True)
