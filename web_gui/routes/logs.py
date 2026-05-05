from flask import Blueprint, render_template, request

from database.admin import Admin

bp = Blueprint('logs', __name__, url_prefix = '/logs')


@bp.route('/')
def list_logs():
    limit = request.args.get('limit', default = 100, type = int)
    items = Admin.recent_logs(limit = limit)
    return render_template('logs/list.html', items = items, limit = limit)
