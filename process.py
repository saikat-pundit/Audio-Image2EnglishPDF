import os
import sys
import re
import gdown
import whisper
from pydub import AudioSegment
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch

def extract_file_id(link):
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', link)
    if match:
        return match.group(1)
    raise ValueError("Could not extract file ID from Google Drive link")

def get_original_filename(file_id):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    try:
        import requests
        response = requests.head(url, allow_redirects=True)
        if 'Content-Disposition' in response.headers:
            filename_match = re.search(r'filename="(.+?)"', response.headers['Content-Disposition'])
            if filename_match:
                return filename_match.group(1)
    except:
        pass
    return None

def download_from_gdrive(link, output_path):
    file_id = extract_file_id(link)
    gdown.download(id=file_id, output=output_path, quiet=False)
    original_name = get_original_filename(file_id)
    return original_name

def convert_m4a_to_wav(m4a_path, wav_path):
    audio = AudioSegment.from_file(m4a_path, format="m4a")
    audio.export(wav_path, format="wav")

def transcribe_and_translate_to_english(wav_path):
    model = whisper.load_model("base")
    result = model.transcribe(wav_path, language=None, task="translate")
    return result["text"]

def create_pdf(text, pdf_path):
    if not text or len(text.strip()) == 0:
        raise ValueError("Cannot create PDF: No text content to write.")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    style = styles['Normal']
    story = []
    for para in text.split('\n'):
        if para.strip():
            story.append(Paragraph(para, style))
            story.append(Spacer(1, 0.2*inch))
    doc.build(story)

def main():
    if len(sys.argv) != 2:
        print("Usage: python process.py <google_drive_link>")
        sys.exit(1)
    drive_link = sys.argv[1]
    m4a_file = "input.m4a"
    wav_file = "input.wav"
    print("Downloading from Google Drive...")
    original_name = download_from_gdrive(drive_link, m4a_file)
    if original_name:
        base = os.path.splitext(original_name)[0]
        pdf_file = f"{base}.pdf"
    else:
        pdf_file = "output.pdf"
    print(f"Output PDF will be: {pdf_file}")
    print("Converting M4A to WAV...")
    convert_m4a_to_wav(m4a_file, wav_file)
    print("Transcribing and translating to English (auto language detection)...")
    english_text = transcribe_and_translate_to_english(wav_file)
    if not english_text:
        print("ERROR: Transcription returned empty text.")
        sys.exit(1)
    print("Creating PDF...")
    create_pdf(english_text, pdf_file)
    print(f"Done. PDF saved as {pdf_file}")

if __name__ == "__main__":
    main()
