import os

import psycopg2
import psycopg2.extras
import psycopg2.pool
from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='../frontend', static_url_path='')

# ── DB connection pool ────────────────────────────────────────────────────────
_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            dsn=os.environ['DATABASE_URL'],
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
    return _pool


class _PooledConn:
    """Context manager that checks a connection in/out of the pool."""

    def __enter__(self):
        self.conn = _get_pool().getconn()
        return self.conn

    def __exit__(self, exc_type, *_):
        if exc_type:
            self.conn.rollback()
        _get_pool().putconn(self.conn)


# ── CORS ─────────────────────────────────────────────────────────────────────

@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})


@app.route('/api/summary')
def summary():
    """Return total incident count per year across all loaded years."""
    try:
        with _PooledConn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT year, COUNT(*) AS count FROM incidents GROUP BY year ORDER BY year'
                )
                rows = cur.fetchall()
        return jsonify({str(r['year']): r['count'] for r in rows})
    except Exception as exc:
        return jsonify({'error': str(exc)}), 503


@app.route('/api/incidents')
def incidents():
    year = request.args.get('year', type=int)
    bbox = request.args.get('bbox')  # minLon,minLat,maxLon,maxLat

    # ── filters
    time_of_day = request.args.getlist('tod')   # dawn|day|dusk|night
    road_type = request.args.getlist('road')    # interstate|highway|local

    if year is None:
        return jsonify({'error': 'year parameter required'}), 400

    # Base query — always include fields needed by the frontend
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

    # ── bbox filter
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

    # ── time-of-day filter (derived from hour + lgt_cond)
    # Buckets: dawn (lgt_cond=4), day (lgt_cond=1), dusk (lgt_cond=5),
    #          night (lgt_cond IN 2,3,6)
    TOD_SQL = {
        'dawn':  'lgt_cond = 4',
        'day':   'lgt_cond = 1',
        'dusk':  'lgt_cond = 5',
        'night': 'lgt_cond IN (2, 3, 6)',
    }
    valid_tod = [t for t in time_of_day if t in TOD_SQL]
    if valid_tod:
        clauses = ' OR '.join(TOD_SQL[t] for t in valid_tod)
        query += f' AND ({clauses})'

    # ── road-type filter
    # interstate: route=1; highway: route IN (2,3); local: route IN (4,5,6,7)
    ROAD_SQL = {
        'interstate': 'route = 1',
        'highway':    'route IN (2, 3)',
        'local':      'route IN (4, 5, 6, 7)',
    }
    valid_road = [r for r in road_type if r in ROAD_SQL]
    if valid_road:
        clauses = ' OR '.join(ROAD_SQL[r] for r in valid_road)
        query += f' AND ({clauses})'

    try:
        with _PooledConn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
    except Exception as exc:
        return jsonify({'error': str(exc)}), 503

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
