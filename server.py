from flask import Flask
from flask import render_template
from flask import request
from flask.json import jsonify
from flask.ext.cors import CORS
from sqlalchemy import create_engine
from sqlalchemy import text
from werkzeug.serving import make_ssl_devcert

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['CORS_HEADERS'] = 'Content-Type'


cors = CORS(app)


engine = create_engine('postgresql://127.0.0.1/fantasy', echo=True)


@app.route("/")
def hello():
    return render_template("home.html")


@app.route("/stats/<int:week>")
def get_data(week):
    connection = engine.connect()
    query = text("""
    select name, team, position, practice_status, injury, game_status, salary :: numeric, ppr, (ppr_high / (salary / MONEY(1000))) as PROJ
    from players where week = :week and salary > MONEY(0)
    order by (ppr / (salary / MONEY(1000))) DESC
    """)

    players = []

    for p in connection.execute(query, week=week):
        print "name:", p['name']
        players.append(
            {
                u"name": p['name'],
                u"proj": round(float(p['proj']), 2),
                u"points": float(p['ppr']),
            }
        )

    return jsonify(players=players)


@app.route("/points")
def get_points_for_players():
    week = request.args.get("week")
    print "week:", week
    name_list = request.args.getlist("names[]")
    print "names:", name_list

    names = ",".join(["'%s'"%(name,) for name in name_list])

    connection = engine.connect()
    query = text("""
    select name, ppr_high as points
    from players
    where name = ANY (:names) AND week = :week
    """)
    players = []
    for p in connection.execute(query, names=name_list, week=week):
        players.append({u"name": p.name,
                        u"points": float(p.points)})

    return jsonify(players=players)


if __name__ == "__main__":
    app.run('0.0.0.0', debug=True, port=5000, ssl_context=('server.crt', 'server.key'))
