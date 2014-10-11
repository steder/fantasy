from flask import Flask
from flask.json import jsonify
from flask.ext.cors import CORS
from sqlalchemy import create_engine
from sqlalchemy import text


app = Flask(__name__)
app.config['DEBUG'] = True
app.config['CORS_HEADERS'] = 'Content-Type'

cors = CORS(app)


engine = create_engine('postgresql://127.0.0.1/fantasy', echo=True)


@app.route("/")
def hello():
    return "Hello World!"


@app.route("/stats/<int:week>")
def get_data(week):
    """
    Use this endpoint by setting up the following bookmarklet and using it on your page:

        javascript:(function(){document.body.appendChild(document.createElement('script')).src='http://localhost:5000/static/bookmarklet.js';})();
    """


    connection = engine.connect()
    query = text("""
    select name, team, position, practice_status, injury, game_status, salary :: numeric, ppr, (ppr / (salary / MONEY(1000))) as PROJ,
    (ppr_low / (salary / MONEY(1000))) as LOW,
    (ppr_high / (salary / MONEY(1000))) as HIGH,
    (ppr_high / (salary / MONEY(1000))) -  (ppr_low / (salary / MONEY(1000))) AS DELTA
    from players where week = :week and salary > MONEY(0)
    AND ppr > 0
    order by (ppr / (salary / MONEY(1000))) DESC
    """)

    players = []

    for p in connection.execute(query, week=week):
        print "name:", p['name']
        players.append(
            {
                u"name": p['name'],
                u"proj": float(p['proj']),
                u"points": float(p['ppr']),
            }
        )

    return jsonify(players=players)


if __name__ == "__main__":
    app.run('0.0.0.0', debug=True, port=5000, ssl_context='adhoc')
