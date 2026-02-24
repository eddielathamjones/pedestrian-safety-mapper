CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS incidents (
    id          SERIAL PRIMARY KEY,
    geom        GEOMETRY(Point, 4326) NOT NULL,
    year        SMALLINT NOT NULL,
    month       SMALLINT,
    day         SMALLINT,
    hour        SMALLINT,   -- 0-23, 99 = unknown
    minute      SMALLINT,   -- 0-59, 99 = unknown
    lgt_cond    SMALLINT,   -- 1=Daylight 2=Dark-not lit 3=Dark-lit 4=Dawn 5=Dusk
    weather     SMALLINT,   -- 1=Clear 2=Rain 3=Sleet 4=Snow 10=Fog ...
    route       SMALLINT,   -- 1=Interstate 2=US Hwy 3=State 4=County 5=Local
    rur_urb     SMALLINT,   -- 1=Rural 2=Urban (available ~2013+, else NULL)
    state       SMALLINT,   -- FIPS state code
    county      SMALLINT,
    age         SMALLINT,   -- 998=Unknown 999=Not reported
    sex         SMALLINT,   -- 1=Male 2=Female 8=Not reported 9=Unknown
    inj_sev     SMALLINT    -- 4=Fatal (all records here are fatal)
);

CREATE INDEX IF NOT EXISTS incidents_geom_idx ON incidents USING GIST (geom);
CREATE INDEX IF NOT EXISTS incidents_year_idx ON incidents (year);
