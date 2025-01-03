import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session
from models.visitor import db, Visitor # type: ignore

visitor_blueprint = Blueprint("visitor", __name__)

@visitor_blueprint.route("/", methods=["GET", "POST"])
def home():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    visitors = Visitor.query.all()
    return render_template("view_visitors.html", visitors=visitors)

@visitor_blueprint.route("/add", methods=["POST"])
def add_visitor():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    name = request.form["name"]
    contact = request.form["contact"]
    purpose = request.form["purpose"]
    visitor = Visitor(name=name, contact=contact, purpose=purpose, check_in=datetime.now())
    db.session.add(visitor)
    db.session.commit()
    return redirect(url_for("visitor.home"))
