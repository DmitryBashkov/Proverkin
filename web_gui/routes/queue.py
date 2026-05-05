from flask import Blueprint, render_template, request, redirect, url_for

from database.admin import Admin
from utils.clients import generator_client

bp = Blueprint('queue', __name__, url_prefix = '/queue')


@bp.route('/')
def list_queue():
    set_id = request.args.get('set_id', type = int)
    status = request.args.get('status') or None
    items = Admin.list_queue(set_id = set_id, status = status)
    sets_ = Admin.list_sets()
    return render_template(
        'queue/list.html',
        items = items, sets = sets_,
        filter_set_id = set_id, filter_status = status
    )


@bp.route('/<int:item_id>/promote', methods = ['POST'])
def promote(item_id):
    Admin.queue_promote_to_questions(item_id)
    return redirect(url_for('queue.list_queue'))


@bp.route('/<int:item_id>/reject', methods = ['POST'])
def reject(item_id):
    Admin.queue_reject(item_id)
    return redirect(url_for('queue.list_queue'))


@bp.route('/generate_now', methods = ['POST'])
def generate_now():
    generator_client.generate_now()
    return redirect(url_for('queue.list_queue'))
