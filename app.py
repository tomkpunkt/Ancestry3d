"""Ancestry3d: a GEDCOM family tree as a 3D time cylinder, as a Streamlit app.

Python reads the GED file (upload or data/ in this repository), shows key
figures and a person picker. The 3D view is viewer.html, embedded in an iframe.
"""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from gedcom_io import decode_ged, parse_ged

HERE = Path(__file__).parent
DATA = HERE / "data"
VIEWER = (HERE / "viewer.html").read_text(encoding="utf-8")
SKELETON = (
    '<!doctype html><html><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
    "<style>body{margin:0;font:14px system-ui,sans-serif}img{max-width:100%}"
    "[hidden]{display:none!important}</style></head><body>{embed}{page}</body></html>"
)

TEXT = {
    "de": {
        "upload": "GED-Datei öffnen",
        "upload_help": "GEDCOM 5.5/5.5.1, UTF-8, UTF-16 oder ANSI. Die Datei bleibt in dieser Sitzung und wird nicht gespeichert.",
        "repo_file": "…oder Datei aus dem Repository",
        "no_source": "Lade links eine GED-Datei hoch oder lege .ged-Dateien in den Ordner data/.",
        "unreadable": "{name} ließ sich nicht lesen ({err}). Erwartet wird eine GEDCOM-Datei (.ged).",
        "no_people": "In {name} wurden keine Personen gefunden. Ist das eine GEDCOM-Datei?",
        "people": "Personen", "families": "Familien", "oldest": "Ältestes Geburtsjahr", "youngest": "Jüngstes",
        "missing": "{n} Personen ohne Geburts- oder Taufjahr; ihre Höhe im Raum wird geschätzt (≈).",
        "highlight": "Person hervorheben", "placeholder": "Name eingeben …",
        "title": "Titel", "height": "Höhe der Ansicht (px)", "nee": "geb.", "language": "Sprache",
    },
    "en": {
        "upload": "Open GED file",
        "upload_help": "GEDCOM 5.5/5.5.1, UTF-8, UTF-16 or ANSI. The file stays in this session and is not stored.",
        "repo_file": "…or a file from the repository",
        "no_source": "Upload a GED file on the left or put .ged files into the data/ folder.",
        "unreadable": "{name} could not be read ({err}). A GEDCOM file (.ged) is expected.",
        "no_people": "No people found in {name}. Is it a GEDCOM file?",
        "people": "People", "families": "Families", "oldest": "Earliest birth year", "youngest": "Latest",
        "missing": "{n} people without a birth or baptism year; their height is estimated (≈).",
        "highlight": "Highlight person", "placeholder": "Type a name …",
        "title": "Title", "height": "View height (px)", "nee": "née", "language": "Language",
    },
}

st.set_page_config(page_title="Ancestry3d", page_icon="🌳", layout="wide", initial_sidebar_state="expanded")
st.markdown("<style>.block-container{padding-top:3.4rem;padding-bottom:0;max-width:100%}</style>", unsafe_allow_html=True)


def browser_lang() -> str:
    locale = getattr(getattr(st, "context", None), "locale", None) or ""
    return "de" if str(locale).lower().startswith("de") else "en"


@st.cache_data(show_spinner=False)
def load(raw: bytes):
    text = decode_ged(raw)
    return text, parse_ged(text)


# ---------- language and source ----------
with st.sidebar:
    st.header("Ancestry3d")
    langs = ["de", "en"]
    lang = st.radio("Sprache / Language", langs, index=langs.index(browser_lang()), horizontal=True,
                    format_func=lambda l: {"de": "Deutsch", "en": "English"}[l], key="lang")
    T = TEXT[lang]
    upload = st.file_uploader(T["upload"], type=None, help=T["upload_help"])
    repo_files = sorted(DATA.glob("*.ged"))
    choice = None
    if not upload and repo_files:
        choice = st.selectbox(T["repo_file"], repo_files, format_func=lambda p: p.name)

if upload:
    name, raw = upload.name, upload.getvalue()
elif choice:
    name, raw = choice.name, choice.read_bytes()
else:
    st.info(T["no_source"])
    st.stop()

try:
    text, tree = load(raw)
except Exception as err:  # unreadable file: show a hint instead of a traceback
    st.error(T["unreadable"].format(name=name, err=err))
    st.stop()
if not tree.people:
    st.error(T["no_people"].format(name=name))
    st.stop()

# ---------- key figures and person picker ----------
with st.sidebar:
    years = tree.years
    c1, c2 = st.columns(2)
    c1.metric(T["people"], len(tree.people))
    c2.metric(T["families"], len(tree.families))
    if years:
        c1.metric(T["oldest"], years[0])
        c2.metric(T["youngest"], years[-1])
    missing = sum(1 for p in tree.people.values() if not p.birth_year)
    st.caption(T["missing"].format(n=missing))

    people = sorted(tree.people.values(), key=lambda p: (p.name.lower(), p.birth_year or 0))
    start = st.selectbox(T["highlight"], people, index=None, format_func=lambda p: p.label(T["nee"]),
                         placeholder=T["placeholder"])
    title = st.text_input(T["title"], value=Path(name).stem.replace("-", " ").replace("_", " ").title())
    height = st.slider(T["height"], 520, 1400, 860, 20)

# ---------- 3D view ----------
embed = {"text": text, "name": name, "title": title, "lang": lang, "start": start.id if start else None}
# JSON inside <script>: escape "<" so no file content can close the script tag
payload = json.dumps(embed, ensure_ascii=False).replace("<", "\\u003c")
html = SKELETON.replace("{embed}", f"<script>window.GED_EMBED={payload};</script>").replace("{page}", VIEWER)

iframe = getattr(st, "iframe", None)
if iframe:
    iframe(html, height=height)
else:  # older Streamlit versions
    import streamlit.components.v1 as components
    components.html(html, height=height)
