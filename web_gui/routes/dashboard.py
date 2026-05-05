from flask import Blueprint, render_template

from database.admin import Admin
from database.connector import PostgresConnector as pg

bp = Blueprint('dashboard', __name__)


@bp.route('/')
def index():
    users = Admin.list_users()
    sets_ = Admin.list_sets()
    queue_pending = pg.execute(
        '''
        select s.set_name, count(*) as pending
        from generation_queue gq
        join sets s on s.set_id = gq.set_id
        where gq.status = 'pending'
        group by s.set_name
        order by pending desc
        ''',
        'fetchall'
    ) or []
    return render_template(
        'dashboard.html',
        users_count = len(users),
        sets_count = len(sets_),
        queue_pending = queue_pending
    )
