# AI-Multilingual-Tool
TL;DR
A simple tool to transcribe and voice-overs videos.


#Full Explanation:
# Video Translator

This project is a video translation tool that extracts audio from a video file, transcribes it, translates the transcription into a target language, generates subtitles, and overlays the translated audio and subtitles back onto the video.

## Features
- Extracts audio from video files.
- Transcribes audio using Whisper.
- Translates text using Hugging Face's translation models.
- Generates AI voice from translated text using pyttsx3.
- Creates subtitles in SRT format.
- Overlays audio and subtitles onto the original video.

## Requirements
- Python 3.x
- FFmpeg (for audio extraction and video processing)
- Required Python packages:
  - `whisper`
  - `transformers`
  - `pyttsx3`
  - `srt`
  - `tkinter` (comes with Python standard library)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Ahad4200/AI-Multilingual-Tool.git
   cd AI-Multilingual-Tool
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   # Activate the virtual environment
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```

3. Install the required packages:
   ```bash
   pip install whisper transformers pyttsx3 srt
   ```

4. Install FFmpeg:
   - **Windows**: Download from [FFmpeg official site](https://ffmpeg.org/download.html) and add it to your system PATH.
   - **Mac**: Install via Homebrew:
     ```bash
     brew install ffmpeg
     ```
   - **Linux**: Install via package manager:
     ```bash
     sudo apt-get install ffmpeg
     ```

## Usage

1. Run the application:
   ```bash
   python version2.py
   ```

2. Select the input video file using the "Browse" button.

3. Choose the original language of the video and the target language for translation.

4. Click the "Start" button to begin the translation process.

5. The output video will be saved in the same directory with translated audio and subtitles.

## Notes
- Translation process will be skipped if input video language is same as target language.
- The application will open the output video automatically after processing.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
- [Hugging Face](https://huggingface.co/) for providing the translation models.
- [OpenAI Whisper](https://github.com/openai/whisper) for audio transcription.
- [pyttsx3](https://pypi.org/project/pyttsx3/) for text-to-speech conversion.
