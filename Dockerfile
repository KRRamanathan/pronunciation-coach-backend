FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download Whisper model at build time to avoid cold-start download
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('small.en', device='cpu', compute_type='int8')"

# Pre-download Allosaurus model
RUN python -c "from allosaurus.app import read_recognizer; read_recognizer()"

# Pre-download g2p_en NLTK data
RUN python -c "import nltk; nltk.download('averaged_perceptron_tagger_eng'); nltk.download('cmudict'); from g2p_en import G2p; G2p()"

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PORT=7860
EXPOSE 7860

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
