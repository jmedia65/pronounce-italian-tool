from os import environ as env
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, jsonify, g, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from utils import ( 
    text_to_speech,
    translate_text_italian
)
import base64
import html

import azure.cognitiveservices.speech as speechsdk
import json
import os
import tempfile

# load dotenv
load_dotenv()

# Azure Speech keys
speech_key = os.getenv("AZURE_SPEECH_KEY")
service_region = os.getenv("AZURE_SPEECH_REGION")

# init flask
app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

# Create users from environment variables
ADMIN_USERNAME = env.get("ADMIN_USERNAME")
ADMIN_PASSWORD = env.get("ADMIN_PASSWORD")

users = {
    1: User(1, ADMIN_USERNAME, generate_password_hash(ADMIN_PASSWORD))
}

@login_manager.user_loader
def load_user(user_id):
    return users.get(int(user_id))

#### Auth routes ####
@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('translate_now'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = None
        for u in users.values():
            if u.username == username and check_password_hash(u.password, password):
                user = u
                break

        if user:
            login_user(user)
            return redirect(url_for('translate_now'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

#### homepage route ####
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for('translate_now'))
    return redirect(url_for('login'))

# ----------------------------------------------------------
### translate now feature ###
# ----------------------------------------------------------
@app.route("/translate-now", methods=["GET", "POST"])
@login_required
def translate_now():
    
    if request.method == "POST":
        data = request.json
        text = data.get('text')
        source_language = data.get('source_language', 'it')  # Default to English if not provided
        target_language = 'en'  # Always translate to Italian

        translated_text_ita = translate_text_italian(text, source_language, target_language)
        translated_text_ita = html.unescape(translated_text_ita)  # Decode HTML entities
        audio_content = text_to_speech(translated_text_ita)  # Generate audio for the translated text
        audio_data = base64.b64encode(audio_content).decode('utf-8')  # Convert audio content to base64

        return jsonify({"translatedTextItalian": translated_text_ita, "audio": audio_data})
    else:
        return render_template("translate_now.html")

# ----------------------------------------------------------
# grading speech
# ----------------------------------------------------------
@app.route('/grade-pronunciation', methods=['POST'])
def grade_pronunciation():
    if 'audio' not in request.files or 'reference_text' not in request.form:
        return jsonify({"error": "Missing audio file or reference text"}), 400

    audio_file = request.files['audio']
    reference_text = request.form['reference_text']

    # Create a temporary file with a .wav extension
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
        audio_file.save(temp_wav.name)
        temp_wav_path = temp_wav.name

    try:
        # Create AudioConfig from the temporary file
        audio_config = speechsdk.audio.AudioConfig(filename=temp_wav_path)

        # Create speech config with Azure Speech key and region
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)

        # Create pronunciation assessment config
        enable_miscue, enable_prosody = False, False
        config_json = {
            "GradingSystem": "HundredMark",
            "Granularity": "Word",
            "Dimension": "Comprehensive",
            "ScenarioId": "",
            "EnableMiscue": enable_miscue,
            "EnableProsodyAssessment": enable_prosody,
            "NBestPhonemeCount": 0,
        }
        pronunciation_config = speechsdk.PronunciationAssessmentConfig(json_string=json.dumps(config_json))
        pronunciation_config.reference_text = reference_text

        # Create a speech recognizer
        language = 'en-US'
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, language=language, audio_config=audio_config)
        # Apply pronunciation assessment config to speech recognizer
        pronunciation_config.apply_to(speech_recognizer)

        result = speech_recognizer.recognize_once_async().get()

        # Check the result
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            pronunciation_result = json.loads(result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonResult))
            return jsonify(pronunciation_result)
        elif result.reason == speechsdk.ResultReason.NoMatch:
            error_result = {"error": "No speech could be recognized"}
            return jsonify(error_result), 400
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            error_result = {"error": f"Speech Recognition canceled: {cancellation_details.reason}"}
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                error_result["error_details"] = cancellation_details.error_details
            return jsonify(error_result), 500
    finally:
        # Clean up the temporary file
        # os.unlink(temp_wav_path)
        pass
   
# ----------------------------------------------------------
# main
# ----------------------------------------------------------
if __name__ == "__main__" and env.get("IS_PRODUCTION") == "False":
    app.run(debug=True)
# ----------------------------------------------------------    