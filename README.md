# Analysisstant

A web application for stock market analysis built on daily National Stock Exchange of India (NSE) closing data.

Analysisstant automatically collects the NSE daily bhavcopy (end-of-day closing inventory), stores it in a PostgreSQL database, and presents it through a Flask web interface with user accounts, market summaries, and browsable company and trade data.

## Features

- **Daily data automation** – downloads the previous trading day's bhavcopy `.zip`/`.csv` from the NSE website, extracts and processes it, and loads it into PostgreSQL (`automation.py`).
- **Company name enrichment** – scrapes company names from CDSL by ISIN code and maintains a `Company` table.
- **User registration & login** – accounts stored with hashed passwords (Werkzeug).
- **Market dashboard** – after login, shows overall trade entries, quantity, value, and trades, plus the top three companies by trading activity for the latest available trading day.
- **Companies browser** – searchable, sortable, paginated list of companies (DataTables).
- **NSE data browser** – searchable, sortable, paginated view of processed closing data.
- **Profile page** – displays the logged-in user's details.
- **Holiday handling** – the automation treats a day as a non-working day when the bhavcopy file is not available from the generated URL, so no separate holiday schedule table is needed.

## Technologies

- Python 3
- Flask (Jinja2 templates, Werkzeug)
- PostgreSQL (psycopg2)
- BeautifulSoup (web scraping)
- Bootstrap 4, DataTables (front end)

## Requirements

- Python 3.9+
- PostgreSQL (with the `stockapp` database created)
- Python packages in `requirements.txt`

## Installation

```bash
git clone <repository-url>
cd analysisstant
python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create the database and tables:

```bash
createdb stockapp
psql -d stockapp -f schema.sql
```

The application reads its database settings from environment variables, falling back to local-development defaults:

| Variable      | Default    | Description              |
|---------------|------------|--------------------------|
| `DB_NAME`     | `stockapp` | Database name            |
| `DB_USER`     | `postgres` | Database user            |
| `DB_PASSWORD` | `123456`   | Database password        |
| `DB_HOST`     | `127.0.0.1`| Database host            |
| `DB_PORT`     | `5432`     | Database port            |

Set the appropriate values for your environment before running, for example:

```bash
export DB_PASSWORD=your_password
```

## Running the web application

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000), register an account, and log in.

## Updating daily data

Run the automation script to fetch and store the previous trading day's data:

```bash
python automation.py
```

The script prints its progress to the console. If the day was a holiday or non-working day it reports it and exits. To keep the data updated automatically, schedule the script with a job scheduler such as CronJob (for example, shortly after the market closes):

```cron
10 1 * * * cd /path/to/analysisstant && python automation.py
```

## Project structure

```
analysisstant/
├── app.py              # Flask application (routes and views)
├── automation.py       # Daily NSE bhavcopy download and database update script
├── requirements.txt    # Python dependencies
├── schema.sql          # PostgreSQL schema (tables: Company, users, raw and processed NSE data)
├── static/             # CSS, favicon, and homepage image
└── templates/          # HTML templates (home, about, login, register, dashboard, etc.)
```

## Database tables

| Table                       | Purpose                                  |
|-----------------------------|------------------------------------------|
| `Company`                   | Listed companies keyed by ISIN code      |
| `nse_script_closing_raw_data` | Raw bhavcopy rows loaded by automation |
| `nse_script_closing_prs_data` | Processed closing data linked to company |
| `users`                     | Registered user accounts                 |

## Known limitations

- Sign-in state is held in a module-level variable, so the app is not safe for multi-user or production deployment; restarting the server logs all users out.
- The automation depends on the upstream NSE and CDSL endpoints and file formats. If those providers change their URLs or formats, the scripts need corresponding updates.
- The application requires a running, reachable PostgreSQL instance.