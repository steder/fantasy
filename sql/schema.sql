-- Fantasy Football DB

-- CREATE DATABASE fantasy;


-- "14344": ["QB", "T.J. Yates", "86701", "27", "1000", "5000", 0, "1", false, 0, "", "old", ""],

-- {"week": "1", "lastUpdate": null, "name": "Peyton Manning", "practiceStatus": null, "playerId": "66", "standard": "24.30", "standardLow": "16.50", "ppr": "24.30", "pprLow": "16.50", "standardHigh": "32.00", "pprHigh": "32.00", "team": "DEN", "position": "QB", "injury": null, "gameStatus": null}

CREATE TABLE IF NOT EXISTS players (
       id SERIAL,
       name TEXT,
       team TEXT,
       position TEXT,
       year INTEGER,
       week INTEGER,

       practice_status TEXT DEFAULT NULL,
       injury TEXT DEFAULT NULL,
       game_status TEXT DEFAULT NULL,
       salary MONEY DEFAULT 0.0,
       fanduel_points_per_game NUMERIC(6, 2),

       standard NUMERIC(6, 2) DEFAULT 0.0,
       standard_low NUMERIC(6, 2) DEFAULT 0.0,
       standard_high NUMERIC(6, 2) DEFAULT 0.0,
       ppr NUMERIC(6,2) DEFAULT 0.0,
       ppr_high NUMERIC(6,2) DEFAULT 0.0,
       ppr_low NUMERIC(6,2) DEFAULT 0.0,

       -- trigger updated created/modified timestamps
       created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE OR REPLACE FUNCTION update_modified_timestamp() RETURNS TRIGGER
LANGUAGE plpgsql
AS
$$
BEGIN
    IF (NEW != OLD) THEN
        NEW.modified = CURRENT_TIMESTAMP;
        RETURN NEW;
    END IF;
    RETURN OLD;
END;
$$;


CREATE TRIGGER update_modified_timestamp
  BEFORE UPDATE
  ON players
  FOR EACH ROW
  EXECUTE PROCEDURE update_modified_timestamp();
