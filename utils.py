#### UTILITY FUNCTIONS
import os
from dotenv import load_dotenv
from openai import OpenAI
# import configparser
from google.cloud import texttospeech
from google.oauth2 import service_account
from google.cloud import translate_v2 as translate

# load environment variables
load_dotenv()

### google application credentials ###
credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
credentials = service_account.Credentials.from_service_account_file(credentials_path)

####################################################################
####### GOOGLE TEXT-TO-SPEECH > WORKING ######################
# function for text to speech for the talking bot 
def text_to_speech(text, language_code='it-IT', return_audio=True):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        #ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        #alternative_language_codes=['en-US']  # Use if you want to support multiple languages
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
    ### D E B U G G I N G ###
    print(f"Text-to-Speech response: Google has responded from the TTS API.")  # Log the response from Google TTS

    if return_audio:
        return response.audio_content
    else:
        # Optionally upload to Cloudinary and return the URL instead
        pass


################################################################ 
# translate now function 
def translate_text_italian(text, source_language='en', target_language='it'):
    translate_client = translate.Client()
    result = translate_client.translate(text, source_language=source_language, target_language=target_language)
    return result['translatedText']

#################################################################
# get phonetics from OpenAI
def get_italian_phonetics(text):
    """Get phonetic pronunciation for Italian text using OpenAI."""
    
    # Input validation
    if not text or len(text.strip()) == 0:
        return None
        
    # Enforce character limit
    MAX_CHARS = 50  # Match frontend limit
    text = text[:MAX_CHARS]
    
    # OpenAI stuff
    client_oai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))   
  
    prompt = f"""Convert this Italian text into simplified phonetic pronunciation: "{text}"
    Format: Return only the pronunciation with syllables separated by hyphens, stressed syllable in CAPS.
    Example format: "conoscerti" should return "ko-no-SHER-tee" without quotes or parenthesis.
    Only return the pronunciation, no other text, quotes, or parenthesis."""
    
    try:
        response = client_oai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error getting phonetics: {e}")
        return None