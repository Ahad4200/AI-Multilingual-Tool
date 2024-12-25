import subprocess
import whisper
from transformers import pipeline
from pyttsx3 import init as pyttsx3_init
import os
import datetime
import srt
import math
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

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
    
    # Split text into chunks of a specified size
    chunk_size = 500  # Adjust this size as needed
    words = text.split()
    chunks = [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    
    # Translate each chunk
    translated_chunks = []
    for chunk in chunks:
        translations = translator(chunk, max_length=1024)  # Set max_length as needed
        translated_chunks.append(translations[0]['translation_text'])
    
    # Combine translated chunks
    return ' '.join(translated_chunks)

def generate_voice(text, output_path):
    """Generate AI voice from text using pyttsx3 for better speed control."""
    engine = pyttsx3_init()
    
    # Adjust voice settings
    engine.setProperty('rate', 185)     # Increased speed of speech to reduce delay
    engine.setProperty('volume', 0.9)   # Volume
    
    # Remove commas for audio generation to prevent delays
    text_for_audio = text.replace(',', '')  # Remove commas
    engine.save_to_file(text_for_audio, output_path)
    engine.runAndWait()

def generate_subtitles(segments, translated_text, subtitle_path):
    """Generate subtitles with improved timing."""
    translated_words = translated_text.split()
    subtitles = []
    
    # Calculate average words per second
    total_duration = segments[-1]["end"] - segments[0]["start"]
    total_words = sum(len(segment["text"].split()) for segment in segments)
    words_per_second = total_words / total_duration if total_duration > 0 else 1
    
    word_index = 0
    for i, segment in enumerate(segments):
        start_time = datetime.timedelta(seconds=segment["start"])
        
        # Calculate end time based on word count
        words_in_segment = len(segment["text"].split())
        segment_duration = words_in_segment / words_per_second
        end_time = datetime.timedelta(seconds=segment["start"] + segment_duration)
        
        # Prevent overlap with next segment
        if i < len(segments) - 1:
            next_start = datetime.timedelta(seconds=segments[i+1]["start"])
            if end_time > next_start:
                end_time = next_start
        
        # Get corresponding translated words
        subtitle_content = " ".join(translated_words[word_index:word_index + words_in_segment])
        word_index += words_in_segment
        
        subtitle = srt.Subtitle(index=len(subtitles) + 1, 
                              start=start_time, 
                              end=end_time, 
                              content=subtitle_content)
        subtitles.append(subtitle)

    with open(subtitle_path, "w", encoding='utf-8') as f:
        f.write(srt.compose(subtitles))

def overlay_audio_and_subtitles(video_path, audio_path, subtitle_path, output_path):
    """Overlay audio and subtitles with improved synchronization."""
    # Get video duration
    probe_cmd = [
        "ffprobe", 
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    video_duration = float(subprocess.check_output(probe_cmd).decode().strip())
    
    # Get audio duration
    probe_cmd = [
        "ffprobe", 
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ]
    audio_duration = float(subprocess.check_output(probe_cmd).decode().strip())
    
    # Calculate speed adjustment
    speed_factor = (audio_duration / video_duration) * 1.2 if video_duration > 0 else 1  # Slightly increase speed
    
    # Create temporary speed-adjusted audio
    temp_audio = "temp_adjusted_audio.mp3"
    speed_cmd = [
        "ffmpeg",
        "-i", audio_path,
        "-filter:a", f"atempo={speed_factor}",
        "-y",
        temp_audio
    ]
    subprocess.run(speed_cmd, check=True)
    
    # Overlay adjusted audio and subtitles
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-i", temp_audio,
        "-vf", f"subtitles={subtitle_path}:force_style='FontSize=24,PrimaryColour=&H00FFFF&'",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path,
        "-y"
    ]
    subprocess.run(cmd, check=True)
    
    # Clean up
    os.remove(temp_audio)

class VideoTranslatorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Translator")
        self.root.geometry("600x500")
        
        # Input video
        tk.Label(root, text="Input Video:").pack(pady=5)
        self.input_frame = tk.Frame(root)
        self.input_frame.pack(fill=tk.X, padx=5)
        
        self.video_path = tk.StringVar()
        tk.Entry(self.input_frame, textvariable=self.video_path).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(self.input_frame, text="Browse", command=self.browse_video).pack(side=tk.RIGHT)

        # Language selection
        tk.Label(root, text="Original Language:").pack(pady=5)
        self.transcription_language = tk.StringVar(value="ru")
        ttk.Combobox(root, textvariable=self.transcription_language, 
                    values=["ru", "en", "fr", "de", "es"]).pack()

        tk.Label(root, text="Target Language:").pack(pady=5)
        self.target_language = tk.StringVar(value="en")
        ttk.Combobox(root, textvariable=self.target_language,
                    values=["en", "ru", "fr", "de", "es"]).pack()

        # Progress
        self.progress = ttk.Progressbar(root, mode='determinate')
        self.progress.pack(fill=tk.X, padx=5, pady=10)
        
        self.status_text = tk.StringVar(value="Ready")
        tk.Label(root, textvariable=self.status_text).pack(pady=5)

        # Start button
        tk.Button(root, text="Start", command=self.start_translation).pack(pady=10)

        # Output log
        self.log_text = tk.Text(root, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def browse_video(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4 *.avi *.mkv"), ("All files", "*.*")])
        if filename:
            self.video_path.set(filename)

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.status_text.set(message)
        self.root.update()

    def start_translation(self):
        if not self.video_path.get():
            messagebox.showerror("Error", "Please select an input video")
            return

        try:
            self.progress['value'] = 0
            video_path = self.video_path.get()
            audio_path = generate_unique_filename("extracted_audio", ".mp3")
            translated_audio_path = generate_unique_filename("translated_audio", ".mp3")
            subtitle_path = generate_unique_filename("subtitles", ".srt")
            output_video_path = generate_unique_filename("output_video", ".mp4")

            # Step 1
            self.log("Extracting audio...")
            extract_audio(video_path, audio_path)
            self.progress['value'] = 20

            # Step 2
            self.log("Transcribing audio...")
            original_text, segments = transcribe_audio(audio_path)
            self.log(f"Original Transcription: {original_text}")
            self.progress['value'] = 40

            # Step 3
            if self.target_language.get() != self.transcription_language.get():
                self.log("Translating captions...")
                translated_text = translate_text(original_text, self.target_language.get())
                self.log(f"Translated Text: {translated_text}")
                self.progress['value'] = 60

                # Step 4
                self.log("Generating subtitles...")
                generate_subtitles(segments, translated_text, subtitle_path)
                self.progress['value'] = 70

                # Step 5
                self.log("Generating AI voice...")
                generate_voice(translated_text, translated_audio_path)
                self.log("Overlaying AI voice and subtitles...")
                overlay_audio_and_subtitles(video_path, translated_audio_path, subtitle_path, output_video_path)
            else:
                self.log("Using original audio...")
                generate_subtitles(segments, original_text, subtitle_path)
                overlay_audio_and_subtitles(video_path, audio_path, subtitle_path, output_video_path)

            self.progress['value'] = 100
            self.log(f"Process completed! Output saved to: {output_video_path}")
            messagebox.showinfo("Success", f"Video translation completed!\nSaved to: {output_video_path}")

            # Open the output video
            subprocess.Popen(["start", output_video_path], shell=True)

        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.log(f"Error: {str(e)}")

def main():
    root = tk.Tk()
    app = VideoTranslatorUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()