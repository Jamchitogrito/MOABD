from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import re
import pandas as pd

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

model = joblib.load('language_final.pkl')

class TextRequest(BaseModel):
    text: str

@app.get('/')
def index():
    return {'status': 'ok', 'message': 'Language Detection API работает'}

@app.post('/predict')
def predict(req: TextRequest):
    text = req.text.strip()
    if not text:
        return {'error': 'Текст не может быть пустым'}

    predicted_lang = model.predict([text])[0]
    proba_array    = model.predict_proba([text])[0]
    max_proba      = float(proba_array.max())

    all_probas = {
        lang: round(float(prob), 4)
        for lang, prob in sorted(
            zip(model.classes_, proba_array),
            key=lambda x: x[1],
            reverse=True
        )
    }

    return {
        'language':      predicted_lang,
        'probability':   round(max_proba, 4),
        'probabilities': all_probas
    }

@app.get('/stats')
def stats():
    return {
        'supported_languages': list(model.classes_),
        'total_languages':     len(model.classes_)
    }