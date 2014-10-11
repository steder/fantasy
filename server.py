from flask import Flask
from flask.json import jsonify
from sqlalchemy import create_engine
from sqlalchemy import text


app = Flask(__name__)
app.config['DEBUG'] = True


engine = create_engine('postgresql://127.0.0.1/fantasy', echo=True)


@app.route("/")
def hello():
    return "Hello World!"


@app.route("/stats/<int:week>")
def get_data(week):
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


@app.route("/bookmarklet")
def get_bookmarklet():
    """
    This endpoint serves our javascript program that pulls in our fantasy football stats data
    and inserts it into to the dom.

    Include the following in your page:

        javascript:(function(){document.body.appendChild(document.createElement('script')).src='http://localhost:5000/bookmarklet';})();

    """


if __name__ == "__main__":
    app.run()
