from google.cloud import texttospeech
from google.cloud import translate
import os
import babel
import numpy as np
from moviepy.editor import *
from moviepy.video.tools.segmenting import findObjects
import youtube_upload
import argparse

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.abspath("vocabria.json")

def speak_in_many_languages(text, privacy_status=youtube_upload.PrivacyStatus.PUBLIC):
    text = text.title()
    directory = os.path.join('videos', text)
    if not os.path.exists(directory):
        os.mkdir(directory)
    video_snippets = []
    languages = ['en'] + spoken_languages()
    languages = languages[:5]
    for index, language in enumerate(languages):
        translation, audio_output_path = translate_and_speak(text, language, directory)
        video_snippets.append(language_video_snippet(text, translation, language, audio_output_path, index==len(languages)))
    video_snippets.append(closing_message())
    full_video = concatenate_videoclips(video_snippets)
    background_image_clip = ImageClip("background-image.png")
    full_video = CompositeVideoClip([
        background_image_clip,
        full_video
    ]).subclip(0, full_video.duration)
    video_path = os.path.join(directory, f'{text}.mp4')
    full_video.write_videofile(video_path,fps=24,codec='mpeg4')
    language_names = [language_name(language, native=False) for language in languages]
    youtube_upload.upload_to_youtube(video_path, f'"{text}" spoken in many languages', f'Hear the word "{text}" spoken in many different languages.\n\n{", ".join(language_names)}', category=27, keywords=['language', 'translation', 'pronunciation', text], privacy_status=privacy_status)

def language_name(language, native=True):
    if native:
        return babel.Locale.parse(language).get_display_name(language)
    else:
        return babel.Locale.parse(language).get_display_name('en')

project_id = 'vocabria'
translate_client = translate.TranslationServiceClient()
client_parent = translate_client.location_path(project_id, 'global')
def translate(text, language_code):
    if language_code == 'en':
        return text
    response = translate_client.translate_text(
        parent=client_parent,
        contents=[text],
        source_language_code="en-US",
        target_language_code=language_code
    )
    return response.translations[0].translated_text

texttospeech_client = texttospeech.TextToSpeechClient()
def speak(text, language, filename):
    synthesis_input = texttospeech.types.SynthesisInput(text=text)
    voice_selection = texttospeech.types.VoiceSelectionParams(
        language_code=language
    )
    audio_config = texttospeech.types.AudioConfig(
        audio_encoding=texttospeech.enums.AudioEncoding.MP3)
    response = texttospeech_client.synthesize_speech(synthesis_input, voice_selection, audio_config)
    with open(filename, 'wb') as out:
        out.write(response.audio_content)
        print(f'Audio content written to file "{filename}"')

def translate_and_speak(text, language, out_dir):
    translation = translate(text, language)
    audio_filename = f'{text}_{language}.mp3'
    path = os.path.join(out_dir, audio_filename)
    speak(translation, language, path)
    return translation, path

def spoken_languages():
    voices = texttospeech_client.list_voices().voices
    unique_languages = []
    for voice in voices:
        language_code = voice.language_codes[0].split('-')[0]
        if language_code not in unique_languages and not language_code == 'en':
            unique_languages.append(language_code)
    return unique_languages

screensize = (720,460)
def language_video_snippet(en_text, translated_text, language, audio_path, fade_en_text=False):
    language_native = language_name(language, native=True)
    language_english = language_name(language, native=False)

    audio_clip = AudioFileClip(audio_path)

    animation_duration = 0.7
    wait_duration = 0.5

    translated_text_clip = TextClip(translated_text, color='black', font="ArialUnicode", fontsize=200).set_position(('center', 0.47), relative=True)
    en_text_clip = TextClip(en_text, color='black', font='ArialUnicode', fontsize=200).set_position(('center', 0.2), relative=True)
    language_text_clip = TextClip(f'{language_native} ({language_english})', color='black', font='ArialUnicode', fontsize=100).set_position(('center', 0.6), relative=True)

    before_audio_video_clip = CompositeVideoClip([
        en_text_clip.subclip(0, animation_duration+wait_duration),
        translated_text_clip.subclip(0, animation_duration).crossfadein(animation_duration),
        translated_text_clip.subclip(0, wait_duration).set_start(animation_duration),
        language_text_clip.subclip(0, animation_duration).crossfadein(animation_duration),
        language_text_clip.subclip(0, wait_duration).set_start(animation_duration)
        ])
    audio_video_clip = CompositeVideoClip([
        en_text_clip.subclip(0, audio_clip.duration),
        translated_text_clip.subclip(0, audio_clip.duration),
        language_text_clip.subclip(0, audio_clip.duration)
        ]).set_audio(audio_clip)
    after_audio_video_clip = CompositeVideoClip([
        *([en_text_clip.subclip(0, animation_duration+wait_duration)] if not fade_en_text else [
            en_text_clip.subclip(0, wait_duration),
            en_text_clip.subclip(0, animation_duration).crossfadeout(animation_duration).set_start(wait_duration),
        ]),
        translated_text_clip.subclip(0, wait_duration),
        translated_text_clip.subclip(0, animation_duration).crossfadeout(animation_duration).set_start(wait_duration),
        language_text_clip.subclip(0, wait_duration),
        language_text_clip.subclip(0, animation_duration).crossfadeout(animation_duration).set_start(wait_duration)
        ])

    text_clips = concatenate_videoclips([
        before_audio_video_clip,
        audio_video_clip,
        after_audio_video_clip
        ])
    return text_clips
    
    
def closing_message():
    duration = 4
    message_clip = TextClip("""Leave a comment with words\nyou would like to hear translated!""", color='black', font="ArialUnicode", fontsize=150).set_position(('center', 0.35), relative=True)
    return CompositeVideoClip([
        message_clip.subclip(0,duration).crossfadein(0.7)
    ])