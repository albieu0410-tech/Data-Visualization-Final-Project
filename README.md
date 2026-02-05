# Engine Atlas

Engine Atlas: data-driven analysis of car engine performance, efficiency, and evolution (1945–2020).

## Repo structure
```
engine-atlas/
  data/
    Car Dataset 1945-2020.csv
  notebooks/
    01_cleaning.ipynb
    02_analysis.ipynb
  app/
    Engine_Atlas.py
    pages/
      1_Trends.py
      2_Brand_Battles.py
      3_Best_Engines.py
      4_Engine_Clusters.py
    components/
      engine_dna/
  assets/
    styles.css
    svg/
```

## Setup
```bash
uv venv
uv sync
```

If you need Python 3.11 explicitly:
```bash
uv venv --python 3.11
```

## Dataset import (kagglehub)
```python
import kagglehub

path = kagglehub.dataset_download(
    "jahaidulislam/car-specification-dataset-1945-2020"
)
print(path)
```

## Data location
Place the CSV in `data/`.

## Run notebooks
```bash
uv run jupyter lab
```

## Run Streamlit
```bash
uv run streamlit run app/Engine_Atlas.py
```

## Streamlit Cloud
- Push the repo to GitHub.
- In Streamlit Cloud, set the app entrypoint to `app/Engine_Atlas.py`.
- Ensure `pyproject.toml` is in the repo root.

## Presentation outline
See `assets/presentation_outline.md` for slide structure and screenshot targets.
