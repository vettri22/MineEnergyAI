# MineEnergy AI
### Intelligent Energy Management System for Iron Ore Mining Operations

MineEnergy AI is a full-stack, AI-assisted energy management platform built for
iron ore mining operations. It monitors, analyzes, predicts, and helps optimize
energy consumption across crushers, conveyors, excavators, pumps, drills, and
processing plants — the kind of system you'd expect to find running inside a
company like Tata Steel, NMDC, Rio Tinto, or BHP.

---

## 1. Feature Overview

- **Industrial dashboard** — glassmorphism cards, dark/light theme toggle, live
  clock, animated KPI counters, and six interactive Chart.js visualizations
  (area, line, bar, pie/doughnut).
- **Machine management** — full CRUD, search, status filters, and pagination
  across 50 seeded machines of 6 types.
- **Energy entry** — a validated form for logging daily readings, instantly
  analyzed by the AI pipeline (efficiency score + anomaly detection).
- **AI recommendation engine** — rule-based expert system that explains *why*
  a machine is consuming abnormal energy and *what* to do about it.
- **Efficiency scoring** — transparent 0–100 formula based on specific energy
  consumption, utilization, and idle time — color-coded Green/Yellow/Red.
- **Anomaly detection & alerts** — rolling-average comparison flags Critical
  and Medium severity events; alerts can be resolved from the UI.
- **AI energy prediction** — scikit-learn Linear Regression forecasts the next
  7 days of energy consumption, plant-wide or per machine, with a day-of-week
  seasonal adjustment and a model confidence (R²) score.
- **Reports** — generate professional Daily/Monthly PDF (ReportLab) and Excel
  (openpyxl) reports with a single click; report history is tracked.
- **Authentication** — session-based login/logout via Flask-Login with role
  support (Admin / Manager / Operator).
- **365 days × 50 machines of realistic seeded history** (18,250+ records),
  generated automatically the first time the app runs.

---

## 2. Technology Stack

| Layer          | Technology                                               |
|----------------|-----------------------------------------------------------|
| Frontend       | HTML5, CSS3 (custom design system), Bootstrap 5, JavaScript (ES6), Chart.js, Font Awesome, Google Fonts |
| Backend        | Python, Flask, SQLAlchemy (Flask-SQLAlchemy), SQLite       |
| AI / ML        | Rule-based recommendation engine, anomaly detection, efficiency scoring, scikit-learn Linear Regression |
| Reports        | ReportLab (PDF), openpyxl (Excel)                          |
| Auth           | Flask-Login (session-based)                                |

---

## 3. Project Structure

```
MineEnergyAI/
├── app.py                     # App factory, blueprint registration, entry point
├── config.py                  # Central configuration (Config classes)
├── extensions.py              # Shared db / login_manager instances
├── requirements.txt
├── README.md
├── database.db                 # Created automatically on first run
│
├── models/
│   ├── __init__.py
│   └── models.py               # User, Machine, EnergyRecord, Alert, Prediction, Report
│
├── routes/                     # Flask blueprints (thin controllers)
│   ├── auth.py                 # /login /logout
│   ├── dashboard.py             # /  /dashboard
│   ├── machines.py             # /machines (CRUD, search, pagination)
│   ├── energy.py                # /energy (entry form + history)
│   ├── alerts.py                # /alerts (list, resolve)
│   ├── predictions.py           # /predictions (AI forecast)
│   ├── reports.py               # /reports (generate/download)
│   └── api.py                   # /api/* (JSON endpoints for live widgets)
│
├── services/                    # Business logic between routes and AI/models
│   ├── analysis_service.py      # Ties AI modules together for energy entries
│   └── dashboard_service.py     # KPI + chart data aggregation queries
│
├── ai/                           # The "AI Module"
│   ├── efficiency_score.py       # 0–100 efficiency formula
│   ├── anomaly_detection.py      # Rolling-average based anomaly rules
│   ├── recommendation_engine.py  # Rule-based diagnosis + recommendations
│   └── prediction_engine.py      # scikit-learn Linear Regression forecasting
│
├── reports/
│   ├── pdf_generator.py          # ReportLab PDF report builder
│   ├── excel_generator.py        # openpyxl Excel report builder
│   └── generated/                # Output folder for generated report files
│
├── utils/
│   ├── seed_data.py              # Generates 50 machines × 365 days of history
│   └── helpers.py                # Shared template filters / decorators
│
├── templates/                    # Jinja2 templates (Bootstrap 5 based)
│   ├── base.html                 # Sidebar + topbar shell, theme toggle
│   ├── login.html
│   ├── dashboard.html
│   ├── machines.html
│   ├── machine_form.html
│   ├── energy.html
│   ├── alerts.html
│   ├── predictions.html
│   ├── reports.html
│   ├── 404.html
│   └── 403.html
│
└── static/
    ├── css/style.css             # Full design system (dark/light, glass cards)
    ├── js/main.js                # Theme toggle, live clock, counters, toasts
    └── images/
```

---

## 4. Installation & Running

**Requirements:** Python 3.10+

```bash
# 1. Navigate into the project folder
cd MineEnergyAI

# 2. (Recommended) create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python app.py
```

On first run, the app automatically creates `database.db` and seeds it with:
- 3 demo user accounts
- 50 machines (Crusher, Conveyor, Excavator, Pump, Drill, Processing Plant)
- 365 days of energy history per machine (~18,250 records)
- AI-generated alerts from detected anomalies in the seeded data

Then open **http://127.0.0.1:5000** in your browser.

### Demo Login Credentials

| Role     | Username  | Password     |
|----------|-----------|--------------|
| Admin    | admin     | admin123     |
| Manager  | manager   | manager123   |
| Operator | operator  | operator123  |

### Re-seeding the database
Delete `database.db` and restart `python app.py`, or run:
```bash
python -m utils.seed_data
```

---

## 5. AI Module — How It Works

The AI layer is intentionally **rule-based and explainable**, which is how
real industrial condition-monitoring software is built (mining engineers need
to trust and verify the logic, not just accept a black-box output):

1. **Efficiency Score** (`ai/efficiency_score.py`) — combines specific energy
   consumption (kWh/ton vs an ideal benchmark), utilization ratio, and idle
   penalty into a weighted 0–100 score.
2. **Anomaly Detection** (`ai/anomaly_detection.py`) — compares a new reading
   against the machine's own trailing 30-day rolling average energy use, and
   classifies deviations as Normal / Medium (≥15%) / Critical (≥25%).
3. **Recommendation Engine** (`ai/recommendation_engine.py`) — a knowledge
   base mapping each machine type to plausible causes (e.g. "worn bearings",
   "motor overload") and concrete corrective actions.
4. **Prediction Engine** (`ai/prediction_engine.py`) — fits a scikit-learn
   `LinearRegression` model against historical daily totals, applies a
   day-of-week seasonal adjustment to the residuals, and forecasts the next
   7 days along with an R² confidence score and trend direction.

---

## 6. Notes on Design

The interface uses a custom "industrial energy" design system rather than
default Bootstrap styling: a near-black steel background, electric-cyan and
reactor-amber accent colors, glassmorphism cards, hexagonal machine-health
badges (a nod to mining/ore imagery), and the Rajdhani/JetBrains Mono type
pairing for a technical, data-readout feel. Both dark and light themes are
supported via a single `data-theme` attribute and CSS custom properties.

---

## 7. Suggested Screenshots for Your Presentation

When preparing your hackathon/final-year submission slides, capture:
1. **Login screen** — dark themed, glass card, demo credentials visible.
2. **Dashboard (dark theme)** — full KPI row + charts + AI Insights panel.
3. **Dashboard (light theme)** — after clicking the theme toggle.
4. **Machine Management** — table with search/filter and a delete confirmation modal open.
5. **Energy Entry** — the form next to the "Recent Entries" history table.
6. **Alerts page** — Critical/Medium/Resolved KPI cards + colored severity table.
7. **AI Predictions** — the historical-vs-forecast line chart with the machine selector.
8. **Reports Center** — the generation form plus a sample downloaded PDF report.

---

## 8. License / Academic Use

This project was generated as a hackathon / final-year academic demonstration
of an industrial energy-management platform. Feel free to extend it (e.g.
swap SQLite for PostgreSQL, add JWT-based API auth, containerize with Docker,
or replace the rule-based prediction seasonal adjustment with a more advanced
time-series model) for further coursework or portfolio use.
