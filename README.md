<p align="center">
  <img src="src/assets/southern_company_logo.png" alt="Southern Company" width="280"/>
</p>

<h1 align="center">Southern Company Fleet Analytics</h1>

<p align="center">
  <strong>Enterprise Intelligence Platform for Network Lifecycle Risk Management</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?logo=streamlit&logoColor=white" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/Plotly-5.18+-3F4F75?logo=plotly&logoColor=white" alt="Plotly"/>
  <img src="https://img.shields.io/badge/OpenAI-GPT--4o-412991?logo=openai&logoColor=white" alt="OpenAI"/>
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License"/>
</p>

---

## Overview

A data-driven analytics dashboard built for **Southern Company** to provide strategic insights into fleet device lifecycle status, geographic risk distribution, financial exposure, and investment planning — all unified under a single, interactive platform.

Built for the **UA Innovate 2026 Hackathon** at The University of Alabama.

---

## Key Features

| Module | What It Does |
|---|---|
| **📊 Executive Overview** | High-level KPIs, risk distribution breakdowns, AI executive briefs, and lifecycle status alerts |
| **🌍 Geographic Risk Intelligence** | Interactive 3D risk map with state-level hotspots and priority site clustering |
| **⚙️ Lifecycle & Asset Health** | End-of-Life trend tracking, aging infrastructure timelines, and critical overdue asset monitoring |
| **💲 Cost & Support Risk** | Financial exposure analysis, support coverage gap visualization, and technical debt tracking |
| **🎯 Investment Prioritization** | Budget simulator with priority ranking and site-level CapEx action plans |
| **🔮 Predictive Risk Forecast** | Forward-looking risk trajectories using scikit-learn, with scenario-based what-if analysis |
| **📤 Data Automation** | Upload new datasets with automated validation and ETL pipeline integration |

### Southern Spark — AI Copilot

An always-available AI assistant embedded within every dashboard page. Powered by **OpenAI GPT-4o** with streaming responses, it provides context-aware answers about the data currently on screen — including risk breakdowns, cost summaries, and actionable recommendations.

- Streaming token-by-token typing animation
- Page-aware context injection
- Glassmorphism frosted-glass UI panel

---

## Tech Stack

- **Frontend:** [Streamlit](https://streamlit.io) with custom HTML/CSS theming (glassmorphism, micro-animations, Inter font)
- **Visualizations:** [Plotly](https://plotly.com/python/) (interactive charts, 3D maps, treemaps, sunbursts)
- **AI Copilot:** [OpenAI GPT-4o](https://platform.openai.com/) with streaming API
- **ML Forecasting:** [scikit-learn](https://scikit-learn.org/) (risk prediction models)
- **Data:** Pandas, NumPy, openpyxl — reading from `.csv` and `.xlsx` datasets

---

## Getting Started

### Prerequisites

- Python 3.10+
- An [OpenAI API key](https://platform.openai.com/api-keys) (for the AI Copilot)

### Installation

```bash
# Clone the repository
git clone https://github.com/girwandhakal/southern-company-analytics.git
cd southern-company-analytics

# Create a virtual environment
python -m venv venv

# Activate it
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configure Secrets

Create a `.streamlit/secrets.toml` file in the project root:

```toml
OPENAI_API_KEY = "sk-your-openai-api-key-here"
```

> **Note:** This file is git-ignored. Never commit API keys to version control.

### Run the App

```bash
streamlit run Home.py
```

The app will open at [http://localhost:8501](http://localhost:8501).

---

## Project Structure

```
southern-company-analytics/
├── Home.py                          # Landing page
├── pages/
│   ├── 1_Executive_Overview.py      # Executive KPI dashboard
│   ├── 2_Geographic_Risk_Intelligence.py
│   ├── 3_Lifecycle_Asset_Health.py
│   ├── 5_Support_Security_Cost.py
│   ├── 6_Data_Automation.py         # Dataset upload & ETL
│   ├── 6_Investment_Prioritization.py
│   └── 7_Predictive_Risk_Forecast.py
├── src/
│   ├── theme.py                     # Design system (colors, CSS, Plotly layouts)
│   ├── dashboard_chatbot.py         # Southern Spark AI Copilot
│   ├── data_loader.py               # Data loading & sidebar utilities
│   └── download_utils.py            # CSV/Excel export helpers
├── dataset/                         # Source data files
├── requirements.txt
└── .streamlit/
    └── secrets.toml                 # API keys (git-ignored)
```

---

## Deployment

This app is deployable to [Streamlit Community Cloud](https://streamlit.io/cloud):

1. Push the repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect the repo.
3. Set the **main file** to `Home.py`.
4. Add your `OPENAI_API_KEY` under **App Settings → Secrets**.

---

## License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

© 2026 Girwan Dhakal & Rahul Mondal