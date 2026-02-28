Your job is to scaffold a clean, production-grade Streamlit dashboard project with a clear directory structure and 5 pages (one per business question). Use vibecoding techniques: work in small, verifiable steps, keep changes tight, and always leave the code runnable.

## Non-negotiable rules
1. Do not commit or push anything. Only provide the exact commands I should run, and if relevant, suggested commit messages (but never run git commands yourself).
2. Do not add secrets or credentials. If anything needs config, use `.env.example` and/or `.streamlit/secrets.toml` (but keep `secrets.toml` out of git).
3. Keep refactors minimal. Only add what is required to scaffold the app.
4. Every new module must have type hints where reasonable, docstrings for public functions, and clear naming.
5. After each step, provide a quick smoke test command and what success looks like.
6. Prefer pure functions for data cleaning and analytics; keep Streamlit UI code thin.

## Goal
Create a Streamlit project layout that supports a 24-hour hackathon dashboard. The app must have 5 pages, each addressing one question. It must run locally with a sample dataset path (placeholder) and include caching patterns.

## The 5 pages (match these file names and sidebar titles exactly)
1. `1_Overview.py` — high-level KPIs and summary of fleet + lifecycle status
2. `2_Risk_Geography.py` — where risk is highest (state/affiliate/county/lat/long) and what is approaching EoS/EoL
3. `3_Radius_Bundling.py` — find sites within radius (1/5/10 mi) that should be lifecycle’d together
4. `4_Exceptions_And_In_Production.py` — devices past lifecycle but still in production + exception capture workflow
5. `5_Support_Security_Cost.py` — lifecycle status vs support coverage, security risk, and cost; prioritization suggestions

## Tech constraints
- Use Python 3.11+ style.
- Use Streamlit multipage conventions (pages directory).
- Use pandas for data tables; plotly for charts; scikit-learn optional for clustering.
- Use parquet caching for cleaned data if helpful.
- No external services required.

## Deliverables
Create these directories/files exactly (if they don’t exist), with starter code that runs:
