"""
SIR Inventory - Download & Combine
====================================
Downloads the 6 SIR Inventory Excel files from the NY DPS website,
maps columns to a standardized schema, and saves a single CSV file.

Requirements:
    pip install requests pandas openpyxl py7zr xlrd

Usage:
    python sir_download_combine.py
"""

import re
import logging
from datetime import datetime
from pathlib import Path

import requests
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path.home() / "Downloads" / "SIR_Inventory"

# Direct download URLs — stable, no scraping needed
DOWNLOAD_URLS = [
    {"name": "National Grid",       "url": "https://dps.ny.gov/national-grid-interconnection-queue-data-0"},
    {"name": "Con Edison",          "url": "https://dps.ny.gov/con-edison-interconnection-queue-data"},
    {"name": "Central Hudson",      "url": "https://dps.ny.gov/central-hudson-interconnection-queue-data-0"},
    {"name": "Orange and Rockland", "url": "https://dps.ny.gov/orange-and-rockland-interconnection-queue-data-0"},
    {"name": "NYSEG and RG&E",      "url": "https://dps.ny.gov/nyseg-and-rge-interconnection-queue-data-0"},
    {"name": "PSEG LI",             "url": "https://dps.ny.gov/pseg-li-interconnection-queue-data-0"},
]

# Map Content-Type headers to file extensions
CONTENT_TYPE_MAP = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-excel": ".xls",
    "application/x-7z-compressed": ".7z",
    "application/zip": ".zip",
}

# ---------------------------------------------------------------------------
# Output schema: (output_column_name, group_label, [accepted_variants])
# Variants are matched after normalizing whitespace and newlines.
# ---------------------------------------------------------------------------

SCHEMA = [
    # --- Summary ---
    ("Company",                                                 "Summary",       ["Company"]),
    ("Developer",                                               "Summary",       ["Developer"]),
    ("Application / Job #",                                     "Summary",       ["Application / Job #", "Application /\nJob #", "Application / \nJob #"]),
    ("Division",                                                "Summary",       ["Division"]),
    ("City/Town",                                               "Summary",       ["City/Town"]),
    ("County",                                                  "Summary",       ["County"]),
    ("Zip Code",                                                "Summary",       ["Zip Code", "Zip\nCode"]),
    ("NYISO Load Zone",                                         "Summary",       ["NYISO Load Zone", "NYISO\nLoad\nZone", "NYISO Zone"]),
    ("Circuit ID",                                              "Summary",       ["Circuit ID"]),
    ("Substation",                                              "Summary",       ["Substation"]),
    # --- System Type ---
    ("Hybrid (Y/N)",                                            "System Type",   ["Hybrid (Y/N)", "Hybrid\n(Y/N)", "Hybrid (Y/N)\n"]),
    ("Related Application/Job #",                               "System Type",   ["Related Application/Job #", "Related\nApplication /\nJob #", "Related Application / Job #"]),
    ("PV (kWAC)",                                               "System Type",   ["PV (kWAC)", "PV\n(kWAC)"]),
    ("ESS (kWAC)",                                              "System Type",   ["ESS (kWAC)", "ESS\n(kWAC)"]),
    ("WIND (kWAC)",                                             "System Type",   ["WIND (kWAC)", "WIND\n(kWAC)"]),
    ("MT (kWAC)",                                               "System Type",   ["MT (kWAC)", "MT\n(kWAC)"]),
    ("SG (kWAC)",                                               "System Type",   ["SG (kWAC)", "SG\n(kWAC)"]),
    ("IG (kWAC)",                                               "System Type",   ["IG (kWAC)", "IG\n(kWAC)"]),
    ("FW (kWAC)",                                               "System Type",   ["FW (kWAC)", "FW\n(kWAC)"]),
    ("FC (kWAC)",                                               "System Type",   ["FC (kWAC)", "FC\n(kWAC)"]),
    ("CHP (kWAC)",                                              "System Type",   ["CHP (kWAC)", "CHP\n(kWAC)"]),
    ("GT (kWAC)",                                               "System Type",   ["GT (kWAC)", "GT\n(kWAC)"]),
    ("HYDRO (kWAC)",                                            "System Type",   ["HYDRO (kWAC)", "HYDRO\n(kWAC)"]),
    ("ICE (kWAC)",                                              "System Type",   ["ICE (kWAC)", "ICE\n(kWAC)"]),
    ("ST (kWAC)",                                               "System Type",   ["ST (kWAC)", "ST\n(kWAC)"]),
    ("OTHER (kWAC)",                                            "System Type",   ["OTHER (kWAC)", "OTHER\n(kWAC)"]),
    # --- Metering ---
    ("Metering (NA / NM / RNM / CDG)",                          "Metering",      ["Metering (NA / NM / RNM / CDG)", "Metering\n(NA / NM / RNM / CDG)",
                                                                                  "Metering1\n(NA / NM / RNM / \nRC / CDG / S-SFA)", "Metering1\n(NA / NM / RNM /\nRC / CDG / S-SFA)", "Metering\n(NA / NM / RNM / CDG /RC)"]),
    ("Value Stack (Y/N)",                                       "Metering",      ["Value Stack (Y/N)", "Value Stack\n(Y/N)", "Value\nStack\n(Y/N)"]),
    # --- Protective Equipment ---
    ("Protective Equipment",                                    "Protective Equipment", ["Protective Equipment", 'Protective Equipment - "Inverter or Synchronous"']),
    # --- 10 business days ---
    ("Start Date (10bd)",                                       "10 business days", ["Start Date"]),       # resolved by group context
    ("End Date (10bd)",                                         "10 business days", ["End Date"]),         # resolved by group context
    ("Calculated Duration (10bd)",                              "10 business days", ["Calculated Duration", "Calculated\nDuration"]),
    ("Application Approved Date (Utility)",                     "10 business days", ["Application Approved Date \n(Utility)", "Application Approved Date\n(Utility)", "Application Approved Date (Utility)"]),
    # --- 15 business days ---
    ("Prelim Start Date (Must Match Application Approved Date)", "15 business days", ["Prelim Start Date (Must Match Application Approved Date)",
                                                                                      "Start Date\n(Must Match Application\nApproved Date)",
                                                                                      "Start Date (Must Match Application Approved Date)"]),
    ("End Date (15bd)",                                         "15 business days", ["End Date"]),         # resolved by group context
    ("Calculated Duration (15bd)",                              "15 business days", ["Calculated Duration", "Calculated\nDuration"]),
    # --- 60 / 100 business days ---
    ("CESIR Payment Received Date",                             "60 / 100 business days", ["CESIR Payment Received Date", "CESIR Payment\nReceived Date", "Payment Received Date"]),
    ("Start Date (60bd)",                                       "60 / 100 business days", ["Start Date"]),  # resolved by group context
    ("End Date (60bd)",                                         "60 / 100 business days", ["End Date"]),    # resolved by group context
    ("Calculated Duration (60bd)",                              "60 / 100 business days", ["Calculated Duration", "Calculated\nDuration"]),
    # --- SIR Costs ---
    ("CESIR Study cost paid by applicant",                      "CESIR Costs",   ["CESIR Study cost paid by applicant",
                                                                                  "CESIR Study\ncost paid by \napplicant4",
                                                                                  "CESIR Study\ncost paid by \napplicant",
                                                                                  "Study Cost Paid by Applicant",
                                                                                  "CESIR cost to customer"]),
    ("Estimated Upgrade Costs Identified by Utility (CESIR or Not)", "Project Installation / Upgrade Costs",
                                                                                 ["Estimated Upgrade Costs Identified by Utility (CESIR or Not)",
                                                                                  "Estimated Upgrade Costs Identified by Utility\n(CESIR or Not)",
                                                                                  "Estimated Costs by Utility","Estimated Upgrade Cost Identified  by Utility (CESIR or Not)"]),
    ("Actual Project Costs Paid by Applicant",                  "Project Installation / Upgrade Costs",
                                                                                 ["Actual Project Costs Paid by Applicant",
                                                                                  "Actual Project\nCosts Paid\nby Applicant",
                                                                                  "Actual Customer Project Costs", "Actual Project Cost Paid by Applicant"]),
    # --- Payments ---
    ("Down Payment Date",                                       "Payments",      ["Down Payment Date", "Down\nPayment\nDate"]),
    ("Full Payment Date",                                       "Payments",      ["Full Payment Date", "Full\nPayment\nDate"]),
    ("Construction Start Date",                                 "Payments",      ["Construction Start Date"]),
    ("Construction Complete Date",                              "Payments",      ["Construction Complete Date", "Construction\nComplete Date"]),
    # --- Others ---
    ("Verification Testing or Final Acceptance Date",           "Others",        ["Verification Testing or Final Acceptance Date",
                                                                                  "Verification Testing or Final Acceptance Date5"]),
    ("Final Letter of Acceptance Date",                         "Others",        ["Final Letter of Acceptance Date", "Final Letter of\nAcceptance\nDate"]),
    ("Project Complete (Y/N/W)",                                "Others",        ["Project Complete (Y/N/W)", "Project\nComplete\n(Y/N/W)"]),
    ("Project Reconciliation Date",                             "Others",        ["Project Reconciliation Date", "Project Recenciliation Date",
                                                                                  "Project\nReconciliation\nDate6"]),
    ("Utility Retention of REC (Y/N)",                          "Others",        ["Utility Retention of REC (Y/N)", "Utility\nRetention of\nREC (Y/N)"]),
]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Step 1 — Download files
# ---------------------------------------------------------------------------

def download_files(dest_dir: Path) -> list[Path]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0"

    paths = []
    for item in DOWNLOAD_URLS:
        log.info("Downloading: %s", item["name"])
        resp = session.get(item["url"], timeout=120, stream=True)
        resp.raise_for_status()

        # Try Content-Disposition first, fallback to Content-Type
        cd = resp.headers.get("Content-Disposition", "")
        m  = re.search(r'filename="?([^";\n]+)"?', cd)
        if m:
            filename = m.group(1).strip()
        else:
            content_type = resp.headers.get("Content-Type", "").split(";")[0].strip()
            ext = CONTENT_TYPE_MAP.get(content_type, ".xlsx")
            filename = item["name"].replace(" ", "_").replace("&", "and") + ext

        path = dest_dir / filename
        with open(path, "wb") as f:
            for chunk in resp.iter_content(65536):
                f.write(chunk)

        log.info("  Saved: %s (%.1f MB)", filename, path.stat().st_size / 1e6)
        paths.append(path)

    return paths

# ---------------------------------------------------------------------------
# Step 2 — Parse multi-row headers with group context
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    """Normalize a header string for comparison: strip quotes, collapse whitespace."""
    s = str(text).strip()
    # Remove surrounding single quotes added by openpyxl for text-formatted cells
    if s.startswith("'") and s.endswith("'") and len(s) > 1:
        s = s[1:-1].strip()
    return re.sub(r'\s+', ' ', s)


def build_column_map(raw_df: pd.DataFrame, header_row: int) -> dict[str, int]:
    """
    Build a map from output_col_name -> source_col_index.
    Uses forward-fill on group rows to handle merged cells.
    """
    # Forward-fill each group row to propagate merged cell values
    group_rows = []
    for r in range(header_row):
        row = raw_df.iloc[r].astype(str).replace("nan", "").replace("None", "")
        row_ffilled = row.replace("", pd.NA).ffill().fillna("").tolist()
        group_rows.append(row_ffilled)

    header = raw_df.iloc[header_row].fillna("").astype(str).tolist()

    col_info = []
    for col_idx in range(len(header)):
        col_label = normalize(header[col_idx])
        group_ctx = " | ".join(
            normalize(group_rows[r][col_idx])
            for r in range(len(group_rows))
            if normalize(group_rows[r][col_idx])
        )
        col_info.append((col_idx, col_label, group_ctx))

    result = {}
    for (out_col, group_label, variants) in SCHEMA:
        norm_variants = [normalize(v) for v in variants]
        norm_group    = normalize(group_label)

        candidates = [
            (col_idx, col_label, group_ctx)
            for (col_idx, col_label, group_ctx) in col_info
            if col_label in norm_variants
        ]

        if not candidates:
            continue

        if len(candidates) == 1:
            result[out_col] = candidates[0][0]
            continue

        # Multiple candidates — score by group context match
        scored = []
        for (col_idx, col_label, group_ctx) in candidates:
            score = 0
            ctx_lower = group_ctx.lower()
            if norm_group and norm_group.lower() in ctx_lower:
                score += 2
            if "10bd" in out_col and any(kw in ctx_lower for kw in ["10 business", "application review", "application-submitted"]):
                score += 5
            if "15bd" in out_col and any(kw in ctx_lower for kw in ["15 business", "preliminary"]):
                score += 5
            if "60bd" in out_col and any(kw in ctx_lower for kw in ["60", "cesir", "study-submitted"]):
                score += 5
            scored.append((score, col_idx))

        scored.sort(key=lambda x: -x[0])
        result[out_col] = scored[0][1]

    return result


# ---------------------------------------------------------------------------
# Step 3 — Read and map a single source file
# ---------------------------------------------------------------------------

FILE_CONFIG = {
    # name_fragment -> (preferred_sheets, header_row)
    "national_grid":   (["March"],     2),
    "con_edison":      (["New Template", "March", "SIR", "Inventory"], 4),
    "central_hudson":  (["Inventory"], 4),
    "orange_and_rock": (["SIR"],       4),
    "nyseg":           (["Sheet1"],    4),
    "pseg_li":         (["March"],     4),
}


def get_file_config(path: Path) -> tuple[list[str], int]:
    """Return (preferred_sheets, header_row) for a given file path."""
    stem = path.stem.lower().replace("-", "_").replace(" ", "_")
    for key, config in FILE_CONFIG.items():
        if key in stem:
            return config
    return ([], 4)  # safe default


def read_and_map(path: Path, utility_name: str) -> pd.DataFrame:
    suffix = path.suffix.lower()

    # Con Edison ships as .7z — extract first
    if suffix == ".7z":
        log.info("  Extracting .7z: %s", path.name)
        import py7zr
        with py7zr.SevenZipFile(path, mode="r") as z:
            xlsx_names = [n for n in z.getnames() if n.lower().endswith((".xlsx", ".xls"))]
            if not xlsx_names:
                raise ValueError(f"No Excel file found inside {path.name}")
            z.extract(targets=[xlsx_names[0]], path=str(path.parent))
        path   = path.parent / xlsx_names[0]
        suffix = path.suffix.lower()

    engine = "xlrd" if suffix == ".xls" else "openpyxl"

    preferred_sheets, header_row = get_file_config(path)

    # Pick the right sheet
    xl = pd.ExcelFile(path, engine=engine)
    sheet = next((s for s in preferred_sheets if s in xl.sheet_names), xl.sheet_names[0])
    log.info("  Reading sheet '%s' from %s (header_row=%d)", sheet, path.name, header_row)

    # Load raw data (no header) to analyze multi-row headers
    raw = pd.read_excel(path, sheet_name=sheet, engine=engine, header=None)

    # Build column map using group context
    col_map = build_column_map(raw, header_row)
    log.info("  Mapped %d / %d schema columns", len(col_map), len(SCHEMA))

    # Extract data rows (below header row)
    data = raw.iloc[header_row + 1:].reset_index(drop=True)

    # Build output DataFrame with standardized columns
    output_cols = [out_col for (out_col, _, _) in SCHEMA]
    out = pd.DataFrame(index=data.index, columns=output_cols)

    for out_col in output_cols:
        if out_col in col_map:
            src_idx = col_map[out_col]
            if src_idx < data.shape[1]:
                out[out_col] = data.iloc[:, src_idx].values

    # Add source identifier
    out.insert(0, "Source_Utility", utility_name)

    # Drop rows where min data columns are empty
    data_cols = [c for c in out.columns if c != "Source_Utility"]
    min_fields = 3
    out = out[out[data_cols].notna().sum(axis=1) >= min_fields]
    out.reset_index(drop=True, inplace=True)

    log.info("  -> %d rows", len(out))
    return out

# ---------------------------------------------------------------------------
# Step 4 — Combine and save as CSV
# ---------------------------------------------------------------------------

def combine_and_save(dfs: list[pd.DataFrame], output_dir: Path) -> Path:
    log.info("Combining %d files...", len(dfs))
    combined    = pd.concat(dfs, ignore_index=True, sort=False)
    timestamp   = datetime.now().strftime("%Y%m%d_%H%M")
    output_path = output_dir / f"SIR_Inventory_Combined_{timestamp}.csv"

    log.info("Writing %d rows to CSV...", len(combined))
    combined.to_csv(output_path, index=False)

    log.info("Combined file saved: %s", output_path)
    log.info("Total rows: %d | Total columns: %d", *combined.shape)
    return output_path

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
# Map filename keywords to utility names
UTILITY_NAME_MAP = {
    "national_grid":   "National Grid",
    "con_edison":      "Con Edison",
    "central_hudson":  "Central Hudson",
    "orange":          "Orange and Rockland",
    "nyseg":           "NYSEG and RG&E",
    "pseg":            "PSEG LI",
}

def get_utility_name(path: Path) -> str:
    stem = path.stem.lower().replace("-", "_").replace(" ", "_")
    for key, name in UTILITY_NAME_MAP.items():
        if key in stem:
            return name
    return path.stem  # fallback to filename

def main():
    log.info("=" * 55)
    log.info("SIR Inventory — Download & Combine")
    log.info("=" * 55)

    raw_files = download_files(OUTPUT_DIR / "raw")

    dfs = []
    for path in raw_files:
        try:
            utility_name = get_utility_name(path)
            log.info("Processing: %s → %s", path.name, utility_name)
            df = read_and_map(path, utility_name)
            dfs.append(df)
        except Exception as e:
            log.error("Failed to process %s: %s", path.name, e)

    if not dfs:
        raise RuntimeError("No files could be processed.")

    output = combine_and_save(dfs, OUTPUT_DIR)
    log.info("Done! File saved at: %s", output)

def main_combine_only():
    """Run only the combine step using already-downloaded files."""
    log.info("=" * 55)
    log.info("SIR Inventory — Combine Only (skipping download)")
    log.info("=" * 55)

    raw_dir = OUTPUT_DIR / "raw"
    raw_files = sorted(raw_dir.glob("*"))
    raw_files = [f for f in raw_files if f.suffix.lower() in (".xlsx", ".xls", ".7z", ".zip", ".csv")]

    if not raw_files:
        raise RuntimeError(f"No files found in {raw_dir}")

    log.info("Found %d files in %s", len(raw_files), raw_dir)

    dfs = []
    for path in raw_files:
        try:
            utility_name = get_utility_name(path)
            log.info("Processing: %s → %s", path.name, utility_name)
            df = read_and_map(path, utility_name)
            dfs.append(df)
        except Exception as e:
            log.error("Failed to process %s: %s", path.name, e)

    if not dfs:
        raise RuntimeError("No files could be processed.")

    output = combine_and_save(dfs, OUTPUT_DIR)
    log.info("Done! File saved at: %s", output)

if __name__ == "__main__":
    main()
    #main_combine_only()