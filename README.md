# Balochi Mini Dictionary (Streamlit)

Searchable Balochi ↔ Urdu ↔ English dictionary, two sentence collections, and a quiz.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy (free)
1. Create a GitHub repo and upload **everything in this folder** (keep `app.py`, `requirements.txt`, `data/`, `.streamlit/`).
2. Go to https://share.streamlit.io → **Create app** → pick the repo, branch `main`, main file `app.py` → **Deploy**.

## Data (`data/`)
| File | Content |
|---|---|
| `dictionary.csv` | 558 words |
| `sentences_balochi_english.csv` | 500 Balochi-script sentences + English |
| `sentences_roman_urdu_english.csv` | 800 Roman Balochi + Urdu + English |
