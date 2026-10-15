"""Ingest EADA (ope.ed.gov/athletics) bulk file into NIL Scoreboard dataset.
Usage: python3 scripts/ingest_eada.py   (downloads if raw file missing)
Writes data/schools.csv, data/schools.json, data/values_long.csv
"""
import csv, json, os, zipfile, urllib.request, datetime
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
FILE = "EADA_All_Data_Combined_2024-2025_SAS_SPSS_EXCEL.zip"
URL = "https://ope.ed.gov/athletics/api/dataFiles/file?fileName=" + FILE
SOURCE_PAGE = "https://ope.ed.gov/athletics/#/datafile/list"
FY = "FY2025"  # EADA collection year 2025 = academic year 2024-25 (July 1 2024 - June 30 2025)
ACCESSED = datetime.date.today().isoformat()

METRICS = {  # our field -> EADA column
    "eada_total_revenue": "GRND_TOTAL_REVENUE",
    "eada_total_expenses": "GRND_TOTAL_EXPENSE",
    "eada_football_revenue": "TOTAL_REVENUE_ALL_Football",
    "eada_football_expenses": "TOTAL_EXPENSE_ALL_Football",
    "eada_mbb_revenue": "REV_MEN_Bskball",
    "eada_mbb_expenses": "EXP_MEN_Bskball",
}

def load():
    xlsx = os.path.join(RAW, "eada2025", "EADA_2025.xlsx")
    if not os.path.exists(xlsx):
        os.makedirs(RAW, exist_ok=True)
        z = os.path.join(RAW, FILE)
        urllib.request.urlretrieve(URL, z)
        zipfile.ZipFile(z).extractall(os.path.join(RAW, "eada2025"))
    return pd.read_excel(xlsx)

def clean(v):
    if pd.isna(v): return None
    return int(round(float(v)))

def main():
    df = load().set_index("unitid")
    seed = list(csv.DictReader(open(os.path.join(ROOT, "data", "schools_seed.csv"))))
    schools, long = [], []
    for s in seed:
        uid = int(s["unitid"]); r = df.loc[uid] if uid in df.index else None
        rec = {k: s[k] for k in ("slug", "name", "conference", "state")}
        rec["unitid"] = uid
        rec["eada_institution_name"] = r["institution_name"] if r is not None else None
        sector = r["sector_name"] if r is not None else ""
        rec["control"] = "Public" if str(sector).startswith("Public") else ("Private" if sector else None)
        rec["metrics"] = {}
        for f, col in METRICS.items():
            v = clean(r[col]) if r is not None and col in df.columns else None
            m = {"value": v, "fiscal_year": FY,
                 "source": "U.S. Dept. of Education EADA, 2025 collection (2024-25)",
                 "source_url": f"https://ope.ed.gov/athletics/#/institution/details/{uid}",
                 "bulk_file_url": URL, "as_of": ACCESSED,
                 "confidence": "Official filing" if v is not None else None}
            rec["metrics"][f] = m
            long.append({"slug": s["slug"], "metric": f, **{k: m[k] for k in ("value","fiscal_year","source","source_url","as_of","confidence")}})
        # Knight-Newhouse: copyrighted, registration-gated, non-commercial only -> not ingested; link only
        kn = "https://www.knightnewhousedata.org/fbs"
        for f in ("kn_total_revenue", "kn_total_expenses", "kn_contributions"):
            rec["metrics"][f] = {"value": None, "fiscal_year": FY, "source": "Knight-Newhouse College Athletics Database (not ingested: license)",
                                 "source_url": kn, "as_of": ACCESSED, "confidence": None}
            long.append({"slug": s["slug"], "metric": f, "value": None, "fiscal_year": FY,
                         "source": rec["metrics"][f]["source"], "source_url": kn, "as_of": ACCESSED, "confidence": None})
        # Placeholders for future records-request data
        for f in ("mfrs_contributions", "revenue_share_budget_fy26"):
            rec["metrics"][f] = {"value": None, "fiscal_year": None, "source": None, "source_url": None, "as_of": None, "confidence": None}
        schools.append(rec)
    out = os.path.join(ROOT, "data")
    json.dump({"generated": ACCESSED, "schools": schools}, open(os.path.join(out, "schools.json"), "w"), indent=1)
    flat = []
    for r in schools:
        row = {k: r[k] for k in ("slug","name","conference","control","state","unitid","eada_institution_name")}
        for f, m in r["metrics"].items():
            row[f] = m["value"]; row[f+"_confidence"] = m["confidence"]
        row["eada_source_url"] = r["metrics"]["eada_total_revenue"]["source_url"]; row["as_of"] = ACCESSED
        flat.append(row)
    with open(os.path.join(out, "schools.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(flat[0])); w.writeheader(); w.writerows(flat)
    with open(os.path.join(out, "values_long.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(long[0])); w.writeheader(); w.writerows(long)
    miss = [r["name"] for r in schools if r["eada_institution_name"] is None]
    print(len(schools), "schools; unmatched:", miss)

if __name__ == "__main__":
    main()
