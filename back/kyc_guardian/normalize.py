"""
Normalize raw sanction/watchlist data into a common JSON structure.
"""

import os, csv, json
import xml.etree.ElementTree as ET
from pathlib import Path
from kyc_guardian.utils.text import norm

RAW = Path("data/raw")
PROC = Path("data/processed")
PROC.mkdir(parents=True, exist_ok=True)

def normalize_ofac():
    out = []
    path = RAW / "ofac/sdn.csv"
    if not path.exists():
        print("!! no OFAC data found")
        return []
    with open(path, encoding="latin-1") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rec = {
                "source": "OFAC",
                "name": norm(row.get("SDN_Name")),
                "type": row.get("SDN_Type"),
                "program": row.get("Program"),
                "title": row.get("Title"),
                "dob": row.get("DOB"),
                "address": row.get("Address"),
                "citizenship": row.get("Citizenship"),
                "remarks": row.get("Remarks"),
            }
            out.append(rec)
    (PROC / "ofac.jsonl").write_text("\n".join(json.dumps(r) for r in out))
    print(f"normalized {len(out)} OFAC records")
    return out

def normalize_un():
    path = RAW / "un/consolidated.xml"
    if not path.exists():
        print("!! no UN data found")
        return []
    
    out = []
    tree = ET.parse(path)
    root = tree.getroot()

    # Parse Individuals
    for ind in root.findall(".//INDIVIDUAL"):
        name_parts = [
            ind.findtext("FIRST_NAME", ""),
            ind.findtext("SECOND_NAME", ""),
            ind.findtext("THIRD_NAME", ""),
            ind.findtext("FOURTH_NAME", ""),
        ]
        name = " ".join(p for p in name_parts if p).strip()
        dob = ind.findtext("DATE_OF_BIRTH", "")
        nationality = ind.findtext("NATIONALITY", "")
        rec = {
            "source": "UN",
            "name": norm(name),
            "dob": dob,
            "citizenship": nationality,
        }
        out.append(rec)

    # Parse Entities
    for ent in root.findall(".//ENTITY"):
        name = ent.findtext("FIRST_NAME", "")
        rec = {
            "source": "UN",
            "name": norm(name),
            "type": "Entity",
        }
        out.append(rec)

    (PROC / "un.jsonl").write_text("\n".join(json.dumps(r) for r in out))
    print(f"normalized {len(out)} UN records")
    return out

def normalize_all():
    all_recs = []
    all_recs.extend(normalize_ofac())
    all_recs.extend(normalize_un())
    # TODO: add UK OFSI + Interpol later
    (PROC / "all.jsonl").write_text("\n".join(json.dumps(r) for r in all_recs))
    print(f"total normalized records: {len(all_recs)}")

if __name__ == "__main__":
    normalize_all()
