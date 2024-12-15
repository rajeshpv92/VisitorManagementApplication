# from flask import Blueprint, render_template, request, send_file
# import pandas as pd
# from models.visitor import Visitor

# report = Blueprint('report', __name__)

# @report.route('/generate_report')
# def generate_report():
#     visitors = Visitor.query.all()
#     data = [{
#         'Name': v.name,
#         'Contact': v.contact,
#         'Purpose': v.purpose,
#         'Check-In': v.check_in,
#         'Check-Out': v.check_out or 'N/A'
#     } for v in visitors]
#     df = pd.DataFrame(data)
#     df.to_excel('visitors_report.xlsx', index=False)
#     return send_file('visitors_report.xlsx', as_attachment=True)
from flask import Blueprint, render_template, session, redirect, url_for
from . import Visitor

report_blueprint = Blueprint("report", __name__)

@report_blueprint.route("/")
def view_report():
    if not session.get("is_admin"):
        return redirect(url_for("visitor.home"))
    visitors = Visitor.query.all()
    return render_template("report.html", visitors=visitors)
