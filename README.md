# Ancestry3d

A GEDCOM family tree as a 3D time cylinder. Every person sits at the height of their birth year (one year = one unit, older at the top). Click a person and their line lights up: ancestors in gold, descendants in cyan, spouses in pink. The current view can be exported as a PNG of about 4K.

Ein GEDCOM-Stammbaum als 3D-Zeitzylinder. Jede Person steht auf der Höhe ihres Geburtsjahres (ein Jahr = eine Einheit, Ältere oben). Ein Klick hebt den Strang hervor: Vorfahren gold, Nachfahren cyan, Ehepartner rosa. Die Ansicht lässt sich als PNG in etwa 4K exportieren.

The interface is available in **English and German** (switch in the viewer header).

## Run locally

```
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Go to https://share.streamlit.io and choose **Create app**.
2. Repository `tomkpunkt/Ancestry3d`, branch `main`, main file `app.py`.

## Files

| File | Purpose |
| --- | --- |
| `app.py` | Streamlit shell: runs the viewer full screen and passes every `.ged` from `data/` into its menu (open your own file there too) |
| `gedcom_io.py` | GEDCOM reader in plain Python (UTF-8, UTF-16, ANSI/Latin-1) |
| `viewer.html` | The 3D view (Three.js from cdn.jsdelivr.net). Works on its own too: open it and load a GED file |
| `data/example-family.ged` | Fictional example tree, all people are invented |

## Privacy

Files you open in the viewer stay in your browser and are not uploaded or stored. Do not commit real family data (living people!) to a public repository; `.gitignore` ignores every `.ged` except the example.

## How heights are estimated

A birth or baptism date sets the height exactly. Without one, the year is estimated from the spouse (±2 years), parents (+28), children (−27), the marriage year (−26) or the death year (−68), and marked with ≈.

## Viewer configuration

`viewer.html` reads an optional `window.GED_EMBED` (set by the app) or `window.GED_DEFAULTS`:

```js
{ text, name, title, start, home, src, lang }
```

`text` is the GEDCOM content, `src` a URL to fetch instead, `start` the person to select, `home` the person for the third visibility button, `lang` `"de"` or `"en"`.
