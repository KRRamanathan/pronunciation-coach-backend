# Local dev startup (Windows)
# Run from pronunciation-coach-backend folder

# Required on Windows without Developer Mode (HF model cache)
$env:HF_HUB_DISABLE_SYMLINKS = "1"

# Optional: Gemini feedback polish
# $env:GEMINI_API_KEY = "your-key-here"

.venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 7860 --reload
