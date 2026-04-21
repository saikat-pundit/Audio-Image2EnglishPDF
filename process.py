import os
import sys
import re
import gdown
import whisper
from pydub import AudioSegment
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from faster_whisper import WhisperModel
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
    model = WhisperModel("large", device="cpu", compute_type="int8")
    segments, info = model.transcribe(wav_path, task="translate", language=None)
    text = " ".join([seg.text for seg in segments])
    return text

def add_header_footer(canvas, doc, filename):
    canvas.saveState()
    header_text = f"{filename} | Page {doc.page}"
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawCentredString(letter[0]/2.0, letter[1] - 20, header_text)
    canvas.restoreState()

def create_pdf(text, pdf_path, audio_filename):
    if not text or len(text.strip()) == 0:
        raise ValueError("Cannot create PDF: No text content to write.")
    
    doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                            topMargin=50, bottomMargin=50,
                            leftMargin=50, rightMargin=50)
    
    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle(
        'JustifiedNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=18,
        alignment=TA_JUSTIFY,
        spaceAfter=6
    )
    
    story = []
    for para in text.split('\n'):
        if para.strip():
            story.append(Paragraph(para, style_normal))
            story.append(Spacer(1, 0.1*inch))
    
    def header_footer(canvas, doc):
        canvas.saveState()
        header_text = f"{audio_filename} | Page {doc.page}"
        canvas.setFont('Helvetica-Bold', 10)
        canvas.drawCentredString(letter[0]/2.0, letter[1] - 20, header_text)
        canvas.restoreState()
    
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)

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
        display_name = original_name
    else:
        pdf_file = "output.pdf"
        display_name = "audio_file"
    print(f"Output PDF will be: {pdf_file}")
    print("Converting M4A to WAV...")
    convert_m4a_to_wav(m4a_file, wav_file)
    print("Transcribing and translating to English using Whisper large model...")
    english_text = transcribe_and_translate_to_english(wav_file)
    if not english_text:
        print("ERROR: Transcription returned empty text.")
        sys.exit(1)
    print("Creating PDF with formatted headers and justified text...")
    create_pdf(english_text, pdf_file, display_name)
    print(f"Done. PDF saved as {pdf_file}")

if __name__ == "__main__":
    main()
