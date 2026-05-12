# Casco Energy Group — Client Hub

Web application for Casco Energy Group built with Streamlit.
Currently includes the SIR Inventory scraper and a LOI Generator placeholder.

## Project Structure

```
scraper/
├── app.py                      ← Main entry point (home screen + login)
├── sir_download_combine.py     ← SIR scraper core logic
├── requirements.txt
├── .gitignore
├── .streamlit/
│   └── secrets.toml            ← Credentials (never commit this file)
└── pages/
    ├── SIR_Inventory.py        ← SIR Inventory app
    └── LOI_Generator.py        ← LOI Generator app
```

## Local Setup

```bash
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate        # Mac/Linux
.venv\Scripts\Activate.ps1       # Windows

pip install -r requirements.txt
streamlit run app.py
```

## Credentials

Create `.streamlit/secrets.toml` with the following content:

```toml
LOGIN_USERNAME = "casco"
LOGIN_PASSWORD = "your_password"
```

This file is excluded from Git via `.gitignore` — never commit it.

## Adding a New App

1. Create `pages/My_New_App.py`
2. Add `st.set_page_config(...)` at the top
3. Add an entry to the `APPS` list in `app.py` for the home screen card

Streamlit picks it up automatically in the sidebar.

## Deploy — Streamlit Cloud (free, recommended for testing)

1. Push repo to GitHub (must be public for free tier)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app** → select your repo → set main file to `app.py`
4. Go to **Settings → Secrets** and paste the contents of your `secrets.toml`
5. Click **Deploy**

## Deploy — Digital Ocean Droplet

```bash
# On your droplet
git clone https://github.com/YOUR_USER/casco_energy_app.git /opt/casco_energy_app
cd /opt/casco_energy_app
pip install -r requirements.txt

# Create secrets file
mkdir -p .streamlit
nano .streamlit/secrets.toml   # paste your credentials here

# Create systemd service
sudo nano /etc/systemd/system/casco.service
```

```ini
[Unit]
Description=Casco Energy Group App
After=network.target

[Service]
WorkingDirectory=/opt/casco_energy_app
ExecStart=/usr/local/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable casco
sudo systemctl start casco
```

App will be available at `http://your-droplet-ip:8501`
