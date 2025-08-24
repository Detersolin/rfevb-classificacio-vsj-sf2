# -*- coding: utf-8 -*-
"""
VSJ SF2 — Scraper de classificació RFEVB -> CSV local per a OBS.
Guarda:
  C:\Guillem\Temporada 25-26\Overlay\VSJ\SF2\classificacio.csv
  C:\Guillem\Temporada 25-26\Overlay\VSJ\SF2\classificacio_top3.txt
"""

import os
import sys
import io
import time
import pandas as pd
import requests

# Carpeta d'output (ajustada a la teva)
OUT_DIR = r"C:\Guillem\Temporada 25-26\Overlay\VSJ\SF2"
CSV_OUT = os.path.join(OUT_DIR, "classificacio.csv")
TOP3_TXT = os.path.join(OUT_DIR, "classificacio_top3.txt")

# 👉 Actualitza l'ID/URLs quan surti la temporada nova
URLS = [
    "https://rfevb-web.dataproject.com/CompetitionHome.aspx?ID=136",  # exemple (temporada anterior)
    "https://www.rfevb.com/superliga-femenina-2-grupo-b-clasificacion",
]

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def pick_standing_table(tables):
    """Tria la taula més probable de classificació per paraules clau."""
    KEYWORDS = ["pos", "equ", "team", "pt", "punt", "points", "pj", "jug", "clasific", "clasificación"]
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


def read_html_tables(html_text: str):
    """
    Llegeix taules HTML des d'un string.
    Prova primer 'lxml' i, si falla, intenta 'html5lib'.
    """
    # 1) Intent amb lxml
    try:
        return pd.read_html(io.StringIO(html_text), flavor="lxml")
    except Exception as e1:
        print(f"   ⚠️  lxml no ha funcionat: {e1}")

    # 2) Fallback a html5lib
    try:
        return pd.read_html(io.StringIO(html_text), flavor="html5lib")
    except ImportError:
        print("   ❗ Falta el parser 'html5lib'. Instal·la'l a l'entorn virtual:")
        print(r"      .\.venv\Scripts\pip.exe install html5lib")
        return []
    except Exception as e2:
        print(f"   ✖️  html5lib tampoc ha funcionat: {e2}")
        return []


def fetch_table():
    """Baixa cadascuna de les URL i retorna el DataFrame de classificació triat."""
    for url in URLS:
        try:
            print(f"➡️  Baixant URL: {url}")
            res = requests.get(url, headers=HEADERS, timeout=20)
            res.raise_for_status()
            html = res.text

            tables = read_html_tables(html)
            print(f"   → trobades {len(tables)} taules HTML")
            if not tables:
                continue

            # ⚠️ No usar 'or' amb DataFrame: fa avaluació booleana i peta.
            df = pick_standing_table(tables)
            if df is None:
                df = tables[0]

            if df is not None and not df.empty:
                df = df.dropna(how="all")
                # A vegades venen MultiIndex a columnes: aplanem
                if isinstance(df.columns, pd.MultiIndex):
                    new_cols = []
                    for tup in df.columns.values:
                        parts = [str(x) for x in tup if not str(x).lower().startswith("unnamed")]
                        new_cols.append(" ".join(parts).strip() or "col")
                    df.columns = new_cols
                else:
                    df.columns = [str(c).strip() for c in df.columns]

                print(f"   → TAULA ESCOLLIDA: {list(df.columns)}  (files={len(df)})")
                return df
            else:
                print("   ⚠️  Taula buida o no vàlida.")
        except Exception as e:
            print(f"   ✖️  Error amb {url}: {e}")
            continue
    return None


def save_outputs(df: pd.DataFrame):
    """Desa CSV i un TOP-3 en text pla per a OBS Text (GDI+)."""
    os.makedirs(OUT_DIR, exist_ok=True)

    # CSV complet
    df.to_csv(CSV_OUT, index=False, encoding="utf-8-sig")
    print("💾 CSV escrit:", CSV_OUT, "files:", len(df))

    # TOP-3 (heurística: 1a col = posició, 2a = equip, última = punts)
    top = df.head(3).copy()
    cols = list(top.columns)

    def getval(row, colname):
        try:
            return str(row.get(colname, "")).strip()
        except Exception:
            return ""

    lines = []
    for _, r in top.iterrows():
        pos = getval(r, cols[0])
        equip = getval(r, cols[1])
        punts = getval(r, cols[-1])
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
            print(f"✖️  Error inesperat: {e}")
        time.sleep(poll_seconds)


if __name__ == "__main__":
    if "--once" in sys.argv:
        run_once()
    else:
        main_loop(300)  # cada 5 minuts
