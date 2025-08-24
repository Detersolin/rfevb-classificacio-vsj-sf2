# -*- coding: utf-8 -*-
"""
VSJ SF2 — Scraper de classificació RFEVB -> CSV local per a OBS

Escriu:
    C:\Guillem\Temporada 25-26\Overlay\VSJ\SF2\classificacio.csv
    C:\Guillem\Temporada 25-26\Overlay\VSJ\SF2\classificacio_top3.txt
"""

import time
import os
import sys
import io
import pandas as pd
import requests

# Carpeta on es guardaran els fitxers per a l’OBS
OUT_DIR = r"C:\Guillem\Temporada 25-26\Overlay\VSJ\SF2"
CSV_OUT = os.path.join(OUT_DIR, "classificacio.csv")
TOP3_TXT = os.path.join(OUT_DIR, "classificacio_top3.txt")

# 👉 Quan surti la temporada nova, actualitza l'ID del microsite aquí
URLS = [
    "https://rfevb-web.dataproject.com/CompetitionHome.aspx?ID=136",  # exemple (temp. anterior)
    "https://www.rfevb.com/superliga-femenina-2-grupo-b-clasificacion",
]

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def pick_standing_table(tables):
    """Tria la taula que sembli una classificació (pos, equip, punts...)."""
    KEYWORDS = ["pos", "equ", "team", "pt", "punt", "points", "pj", "jug"]
    best = None
    best_score = -1
    for i, df in enumerate(tables):
        cols = [str(c).strip().lower() for c in df.columns]
        score = sum(any(k in c for k in KEYWORDS) for c in cols)
        print(f"  - Taula #{i} columnes: {cols} => score={score}")
        if score > best_score:
            best = df
            best_score = score
    return best


def fetch_table():
    for url in URLS:
        try:
            print(f"➡️  Baixant URL: {url}")
            res = requests.get(url, headers=HEADERS, timeout=20)
            res.raise_for_status()
            html = res.text
            # Future-proof: llegir HTML amb StringIO
            tables = pd.read_html(io.StringIO(html))
            print(f"   → trobades {len(tables)} taules HTML")
            if not tables:
                continue
            df = pick_standing_table(tables) or tables[0]
            df = df.dropna(how="all")
            df.columns = [str(c).strip() for c in df.columns]
            print(f"   → TAULA ESCOLLIDA: {list(df.columns)}  (files={len(df)})")
            return df
        except Exception as e:
            print(f"   ✖️ Error amb {url}: {e}")
            continue
    return None


def save_outputs(df):
    os.makedirs(OUT_DIR, exist_ok=True)
    # CSV
    df.to_csv(CSV_OUT, index=False, encoding="utf-8-sig")
    print("💾 CSV escrit:", CSV_OUT, "files:", len(df))

    # TOP-3 text (per OBS Text GDI+)
    top = df.head(3).copy()
    cols = list(top.columns)
    lines = []
    for _, r in top.iterrows():
        pos = str(r.get(cols[0], "")).strip()
        equip = str(r.get(cols[1], "")).strip()
        punts = str(r.get(cols[-1], "")).strip()
        lines.append(f"{pos} - {equip} ({punts})")
    with open(TOP3_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("📝 TOP3 escrit:", TOP3_TXT)


def run_once():
    df = fetch_table()
    if df is not None and not df.empty:
        save_outputs(df)
    else:
        print("⚠️  No s'ha pogut obtenir cap taula de classificació.")


def main_loop(poll_seconds=300):
    while True:
        try:
            run_once()
        except Exception as e:
            print(f"✖️ Error inesperat: {e}")
        time.sleep(poll_seconds)


if __name__ == "__main__":
    # Si rep l'argument --once fa una sola passada i surt (ideal per proves)
    if "--once" in sys.argv:
        run_once()
    else:
        main_loop(300)  # cada 5 minuts
