"""Ancestry3d: a GEDCOM family tree as a 3D time cylinder, as a Streamlit app.

The app is a full-screen frame around viewer.html. Python reads the GED files
in data/ (character set detection in gedcom_io.py) and hands them to the
viewer; everything else (opening your own file, language, search, display
options) lives in the viewer's own menu.
"""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from gedcom_io import decode_ged

HERE = Path(__file__).parent
DATA = HERE / "data"
VIEWER = (HERE / "viewer.html").read_text(encoding="utf-8")
SKELETON = (
    '<!doctype html><html><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
    "<style>html,body{height:100%}body{margin:0;font:14px system-ui,sans-serif}img{max-width:100%}"
    "[hidden]{display:none!important}</style></head><body>{embed}{page}</body></html>"
)
# Streamlit chrome off, the frame fills the whole window (dvh follows mobile browser bars)
FULLSCREEN = """<style>
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], footer { display: none !important; }
html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"], [data-testid="stMain"] { overflow: hidden !important; }
.block-container, [data-testid="stMainBlockContainer"] { padding: 0 !important; max-width: 100% !important; }
[data-testid="stVerticalBlock"] { gap: 0 !important; }
[data-testid="stElementContainer"]:has(> .stHtml) { display: none; }
iframe { display: block; width: 100vw !important; height: 100vh !important; height: 100dvh !important; border: 0; }
</style>"""

st.set_page_config(page_title="Ancestry3d", page_icon="🌳", layout="wide", initial_sidebar_state="collapsed")
st.html(FULLSCREEN)


@st.cache_data(show_spinner=False)
def repo_files() -> list[dict]:
    return [{"name": p.name, "text": decode_ged(p.read_bytes())} for p in sorted(DATA.glob("*.ged"))]


# Language: the viewer follows the browser and remembers the viewer's own switch
embed = {"title": "Ancestry3d", "files": repo_files()}
# JSON inside <script>: escape "<" so no file content can close the script tag
payload = json.dumps(embed, ensure_ascii=False).replace("<", "\\u003c")
html = SKELETON.replace("{embed}", f"<script>window.GED_EMBED={payload};</script>").replace("{page}", VIEWER)

iframe = getattr(st, "iframe", None)
if iframe:
    iframe(html, height=900)
else:  # older Streamlit versions
    import streamlit.components.v1 as components
    components.html(html, height=900)
