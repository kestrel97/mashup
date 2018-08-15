import os
import re
from flask import Flask, jsonify, render_template, request

from cs50 import SQL,eprint
from helpers import lookup

# Configure application
app = Flask(__name__)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///mashup.db")


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    """Render map"""
    return render_template("index.html")


@app.route("/articles")
def articles():
    """Look up articles for geo"""

    # if request.args.get("geo") == None
    geo = request.args.get("geo")
    article = lookup(geo)
    # eprint(article.)
    del article[5:]
    return jsonify(article)


@app.route("/search")
def search():
    """Search for places that match query"""

    # TODO
    rows = []
    q = request.args.get("q")
    regex = re.compile('[^a-zA-Z0-9()]')
    qlist = [regex.sub('', x) for x in q.split(",")]
    if len(qlist) == 1:
        q = q + "%"
        q1 = "%" + q
        rows = db.execute("SELECT * FROM places WHERE postal_code LIKE :q OR place_name LIKE :q OR admin_name1 LIKE :q OR latitude LIKE :q1 OR longitude LIKE :q1 ", q=q, q1=q1)
        # return jsonify(rows)
    elif len(qlist) == 2:
        qlist[0] = qlist[0] + "%"
        qlist[1] = qlist[1] + "%"
        q1  = "%" + qlist[0]
        q12 = "%" + qlist[1]
        rows = db.execute("SELECT * FROM (SELECT * FROM places WHERE postal_code LIKE :q OR place_name LIKE :q OR admin_name1 LIKE :q OR latitude LIKE :q1 OR longitude LIKE :q1) where country_code LIKE :q0 OR postal_code LIKE :q0 OR place_name LIKE :q0 OR admin_name1 LIKE :q0 OR latitude LIKE :q10 OR longitude LIKE :q10",q=qlist[0], q1=q1, q0=qlist[1] , q10=q12)
        # return jsonify(rows)
    elif len(qlist) == 3 or (len(qlist) == 4):
        qlist[0] = qlist[0] + "%"
        qlist[1] = qlist[1] + "%"
        qlist[2] = qlist[2] + "%"
        q1  = "%" + qlist[0]
        q12 = "%" + qlist[1]
        q13 = "%" + qlist[2]
        rows = db.execute("SELECT * FROM(SELECT * FROM (SELECT * FROM places WHERE postal_code LIKE :q OR place_name LIKE :q OR admin_name1 LIKE :q OR latitude LIKE :q1 OR longitude LIKE :q1) where country_code LIKE :q0 OR postal_code LIKE :q0 OR place_name LIKE :q0 OR admin_name1 LIKE :q0 OR latitude LIKE :q12 OR longitude LIKE :q12) WHERE country_code LIKE :q00 OR postal_code LIKE :q00 OR place_name LIKE :q00 OR admin_name1 LIKE :q00 OR latitude LIKE :q13 OR longitude LIKE :q13",q=qlist[0], q1=q1, q0=qlist[1] , q12=q12, q00=qlist[2] ,q13=q13)
        # return jsonify(row)

    # eprint(rows)
    return jsonify(rows)

@app.route("/update")
def update():
    """Find up to 10 places within view"""

    # Ensure parameters are present
    if not request.args.get("sw"):
        raise RuntimeError("missing sw")
    if not request.args.get("ne"):
        raise RuntimeError("missing ne")

    # Ensure parameters are in lat,lng format
    if not re.search("^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$", request.args.get("sw")):
        raise RuntimeError("invalid sw")
    if not re.search("^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$", request.args.get("ne")):
        raise RuntimeError("invalid ne")

    # Explode southwest corner into two variables
    sw_lat, sw_lng = map(float, request.args.get("sw").split(","))

    # Explode northeast corner into two variables
    ne_lat, ne_lng = map(float, request.args.get("ne").split(","))

    # Find 10 cities within view, pseudorandomly chosen if more within view
    if sw_lng <= ne_lng:

        # Doesn't cross the antimeridian
        rows = db.execute("""SELECT * FROM places
                          WHERE :sw_lat <= latitude AND latitude <= :ne_lat AND (:sw_lng <= longitude AND longitude <= :ne_lng)
                          GROUP BY country_code, place_name, admin_code1
                          ORDER BY RANDOM()
                          LIMIT 10""",
                          sw_lat=sw_lat, ne_lat=ne_lat, sw_lng=sw_lng, ne_lng=ne_lng)

    else:

        # Crosses the antimeridian
        rows = db.execute("""SELECT * FROM places
                          WHERE :sw_lat <= latitude AND latitude <= :ne_lat AND (:sw_lng <= longitude OR longitude <= :ne_lng)
                          GROUP BY country_code, place_name, admin_code1
                          ORDER BY RANDOM()
                          LIMIT 10""",
                          sw_lat=sw_lat, ne_lat=ne_lat, sw_lng=sw_lng, ne_lng=ne_lng)

    # Output places as JSON
    # eprint(rows)
    # for row in rows:
    #     eprint(row['latitude'])
    return jsonify(rows)
