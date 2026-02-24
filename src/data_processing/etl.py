"""
ETL: FARS National CSV zips → PostGIS incidents table.

Usage:
    python -m src.data_processing.etl --years 2022 --data-dir data/raw
    python -m src.data_processing.etl --years 2010-2022 --data-dir data/raw
"""

import argparse
import csv
import io
import os
import sys
import zipfile
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Sentinel values that indicate missing/not-reported coordinates
LAT_SENTINELS = {'', '77.7777', '99.9999', '88.8888', '0', '0.0'}
LON_SENTINELS = {'', '77.7777', '99.9999', '888.8888', '0', '0.0'}


def _sentinel(val: str, sentinels: set) -> bool:
    v = val.strip()
    if v in sentinels:
        return True
    try:
        # Also catch values outside plausible US bounds
        f = float(v)
        return f == 0.0
    except ValueError:
        return True


def _int_or_none(val: str) -> int | None:
    v = val.strip()
    if not v:
        return None
    try:
        return int(float(v))
    except ValueError:
        return None


def _find_csv(zf: zipfile.ZipFile, name: str) -> str | None:
    """Return the zip member path matching name (case-insensitive)."""
    for member in zf.namelist():
        if Path(member).name.lower() == name.lower():
            return member
    return None


def _read_csv_from_zip(zf: zipfile.ZipFile, member: str) -> list[dict]:
    with zf.open(member) as f:
        text = io.TextIOWrapper(f, encoding='latin-1')
        return list(csv.DictReader(text))


def _normalise(row: dict) -> dict:
    """Return dict with lowercased keys."""
    return {k.lower().strip(): v.strip() for k, v in row.items()}


def process_year(year: int, data_dir: Path, conn) -> int:
    zip_path = data_dir / str(year) / f'FARS{year}NationalCSV.zip'
    if not zip_path.exists():
        print(f'  [{year}] zip not found: {zip_path}', file=sys.stderr)
        return 0

    print(f'  [{year}] opening {zip_path.name}')
    with zipfile.ZipFile(zip_path) as zf:
        acc_member = _find_csv(zf, 'accident.csv')
        per_member = _find_csv(zf, 'person.csv')

        if not acc_member or not per_member:
            print(f'  [{year}] could not find ACCIDENT.csv or PERSON.csv', file=sys.stderr)
            return 0

        accidents = {
            row['st_case']: row
            for row in (_normalise(r) for r in _read_csv_from_zip(zf, acc_member))
        }
        persons = [
            _normalise(r) for r in _read_csv_from_zip(zf, per_member)
            if _normalise(r).get('per_typ', '').strip() == '5'
        ]

    print(f'  [{year}] {len(persons)} pedestrian person records found')

    inserted = 0
    skipped = 0

    with conn.cursor() as cur:
        for per in persons:
            st_case = per.get('st_case', '')
            acc = accidents.get(st_case)
            if acc is None:
                skipped += 1
                continue

            lat = acc.get('latitude', '').strip()
            lon = acc.get('longitud', '').strip()

            if _sentinel(lat, LAT_SENTINELS) or _sentinel(lon, LON_SENTINELS):
                skipped += 1
                continue

            try:
                lat_f = float(lat)
                lon_f = float(lon)
            except ValueError:
                skipped += 1
                continue

            # Sanity-check US bounds (inclusive of territories)
            if not (-180 <= lon_f <= -60) or not (15 <= lat_f <= 72):
                skipped += 1
                continue

            cur.execute(
                """
                INSERT INTO incidents
                    (geom, year, month, day, hour, minute,
                     lgt_cond, weather, route, rur_urb,
                     state, county, age, sex, inj_sev)
                VALUES
                    (ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                     %s, %s, %s, %s, %s,
                     %s, %s, %s, %s,
                     %s, %s, %s, %s, %s)
                """,
                (
                    lon_f, lat_f,
                    year,
                    _int_or_none(acc.get('month', '')),
                    _int_or_none(acc.get('day', '')),
                    _int_or_none(acc.get('hour', '')),
                    _int_or_none(acc.get('minute', '')),
                    _int_or_none(acc.get('lgt_cond', '')),
                    _int_or_none(acc.get('weather', '')),
                    _int_or_none(acc.get('route', '')),
                    _int_or_none(acc.get('rur_urb', '')),
                    _int_or_none(acc.get('state', '')),
                    _int_or_none(acc.get('county', '')),
                    _int_or_none(per.get('age', '')),
                    _int_or_none(per.get('sex', '')),
                    _int_or_none(per.get('inj_sev', '')),
                ),
            )
            inserted += 1

        conn.commit()

    print(f'  [{year}] inserted {inserted}, skipped {skipped}')
    return inserted


def parse_year_range(spec: str) -> list[int]:
    if '-' in spec:
        start, end = spec.split('-')
        return list(range(int(start), int(end) + 1))
    return [int(spec)]


def main():
    parser = argparse.ArgumentParser(description='Load FARS pedestrian data into PostGIS')
    parser.add_argument('--years', required=True,
                        help='Year or range, e.g. 2022 or 2010-2022')
    parser.add_argument('--data-dir', default='data/raw',
                        help='Path to directory containing per-year FARS zips')
    args = parser.parse_args()

    years = parse_year_range(args.years)
    data_dir = Path(args.data_dir)

    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print('DATABASE_URL not set', file=sys.stderr)
        sys.exit(1)

    conn = psycopg2.connect(db_url)
    total = 0
    for year in years:
        total += process_year(year, data_dir, conn)
    conn.close()

    print(f'\nDone. Total inserted: {total}')


if __name__ == '__main__':
    main()
