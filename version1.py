import subprocess
import whisper
from transformers import pipeline
from gtts import gTTS
import os
import datetime
import srt

def generate_unique_filename(base_name, extension):
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{base_name}_{timestamp}{extension}"

def extract_audio(video_path, audio_path):
    """Extract audio from video using FFmpeg."""
    cmd = [
        "ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", audio_path, "-y"
    ]
    subprocess.run(cmd, check=True)

def transcribe_audio(audio_path, model_name="base"):
    """Transcribe audio using Whisper."""
    model = whisper.load_model(model_name)
    result = model.transcribe(audio_path)
    return result['text'], result['segments']

def translate_text(text, target_language):
    """Translate text to target language using Hugging Face."""
    translator = pipeline("translation", model=f"Helsinki-NLP/opus-mt-ru-{target_language}")
    translations = translator(text, max_length=512)
    return translations[0]['translation_text']

def generate_voice(text, output_path):
    """Generate AI voice from text using gTTS."""
    tts = gTTS(text=text, lang='en')  # Change 'en' to the target language code if needed
    tts.save(output_path)

def generate_subtitles(segments, translated_text, subtitle_path):
    """Generate subtitles (SRT format) dynamically."""
    translated_words = translated_text.split()  # Split translated text into words
    subtitles = []

    word_index = 0
    for segment in segments:
        start_time = datetime.timedelta(seconds=segment["start"])
        end_time = datetime.timedelta(seconds=segment["end"])
        words = segment["text"].strip().split()  # Words in this segment
        
        # Map translated words to original segments
        subtitle_content = " ".join(translated_words[word_index:word_index + len(words)])
        word_index += len(words)
        
        subtitle = srt.Subtitle(index=len(subtitles) + 1, start=start_time, end=end_time, content=subtitle_content)
        subtitles.append(subtitle)

    with open(subtitle_path, "w") as f:
        f.write(srt.compose(subtitles))

def overlay_audio_and_subtitles(video_path, audio_path, subtitle_path, output_path):
    """Overlay audio and subtitles on video using FFmpeg."""
    cmd = [
        "ffmpeg",
        "-i", video_path,               # Input video
        "-i", audio_path,               # Input audio
        "-vf", f"subtitles={subtitle_path}:force_style='FontSize=24,PrimaryColour=&H00FFFF&'",  # Add styled subtitles
        "-c:v", "libx264",              # Video codec
        "-c:a", "aac",                  # Audio codec
        "-map", "0:v:0", "-map", "1:a:0",  # Map video and audio streams
        "-shortest",                    # Shorten to the shortest input
        output_path, "-y"
    ]
    subprocess.run(cmd, check=True)

def main():
    video_path = "input_video.mp4"  # Input video path
    audio_path = generate_unique_filename("extracted_audio", ".mp3")  # Extracted audio path
    transcription_language = "ru"  # Original language of the video
    target_language = "en"  # Target language for captions and voice
    translated_audio_path = generate_unique_filename("translated_audio", ".mp3")  # AI-generated audio path
    subtitle_path = generate_unique_filename("subtitles", ".srt")  # Subtitle file path
    output_video_path = generate_unique_filename("output_video", ".mp4")  # Final video path

    # Step 1: Extract audio from video
    print("Extracting audio from video...")
    extract_audio(video_path, audio_path)

    # Step 2: Transcribe the audio
    print("Transcribing audio...")
    original_text, segments = transcribe_audio(audio_path)
    print(f"Original Transcription: {original_text}")

    # Step 3: Translate captions
    print("Translating captions...")
    translated_text = translate_text(original_text, target_language)
    print(f"Translated Text: {translated_text}")

    # Step 4: Generate subtitles
    print("Generating subtitles...")
    generate_subtitles(segments, translated_text, subtitle_path)

    # Step 5: Generate AI voice if needed
    if target_language != transcription_language:
        print("Generating AI voice...")
        generate_voice(translated_text, translated_audio_path)

        # Step 6: Overlay AI voice and subtitles on video
        print("Overlaying AI voice and subtitles on video...")
        overlay_audio_and_subtitles(video_path, translated_audio_path, subtitle_path, output_video_path)
    else:
        print("No AI voice generation needed for the same language.")
        overlay_audio_and_subtitles(video_path, audio_path, subtitle_path, output_video_path)

    print("Process completed. Output video saved at:", output_video_path)

if __name__ == "__main__":
    main()
