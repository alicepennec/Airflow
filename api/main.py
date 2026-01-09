from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
import os
import pandas as pd

app = FastAPI(title="JO Data API")

# Configuration de la connexion
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API des données JO"}

@app.get("/resultats")
def get_resultats(limit: int = 10):
    """Récupère les résultats sportifs avec une limite"""
    try:
        with engine.connect() as conn:
            query = text(f"SELECT * FROM resultats LIMIT :limit")
            result = conn.execute(query, {"limit": limit})
            # Conversion du résultat en liste de dictionnaires
            data = [dict(row._mapping) for row in result]
            return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/resultats/athlete/{nom}")
def get_athlete(nom: str):
    """Recherche les résultats pour un athlète spécifique"""
    try:
        with engine.connect() as conn:
            query = text("SELECT * FROM resultats WHERE athlete_nom ILIKE :nom")
            result = conn.execute(query, {"nom": f"%{nom}%"})
            data = [dict(row._mapping) for row in result]
            return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))