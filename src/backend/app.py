import json
import os

import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='../frontend', static_url_path='')


def get_db():
    return psycopg2.connect(
        os.environ['DATABASE_URL'],
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})


@app.route('/api/incidents')
def incidents():
    year = request.args.get('year', type=int)
    bbox = request.args.get('bbox')  # minLon,minLat,maxLon,maxLat — used in V4

    if year is None:
        return jsonify({'error': 'year parameter required'}), 400

    query = """
        SELECT
            id,
            ST_X(geom) AS lon,
            ST_Y(geom) AS lat,
            year, month, day, hour, minute,
            lgt_cond, weather, route, rur_urb,
            state, county, age, sex, inj_sev
        FROM incidents
        WHERE year = %s
    """
    params = [year]

    if bbox:
        try:
            min_lon, min_lat, max_lon, max_lat = (float(x) for x in bbox.split(','))
        except ValueError:
            return jsonify({'error': 'bbox must be minLon,minLat,maxLon,maxLat'}), 400
        query += """
            AND ST_Intersects(
                geom,
                ST_MakeEnvelope(%s, %s, %s, %s, 4326)
            )
        """
        params.extend([min_lon, min_lat, max_lon, max_lat])

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
    finally:
        conn.close()

    features = [
        {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [row['lon'], row['lat']],
            },
            'properties': {
                k: v for k, v in row.items() if k not in ('lon', 'lat')
            },
        }
        for row in rows
    ]

    return jsonify({
        'type': 'FeatureCollection',
        'features': features,
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
