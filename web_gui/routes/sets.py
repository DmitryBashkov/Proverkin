from flask import Blueprint, render_template, request, redirect, url_for

from database.admin import Admin
from utils.clients import generator_client

bp = Blueprint('sets', __name__, url_prefix = '/sets')


@bp.route('/')
def list_sets():
    sets_ = Admin.list_sets()
    # Подмешаем pending count для каждого set'а
    enriched = []
    for s in sets_:
        set_id = s[0]
        pending = generator_client.queue_size(set_id)
        enriched.append(s + (pending,))
    return render_template('sets/list.html', sets = enriched)


@bp.route('/new', methods = ['GET', 'POST'])
def new_set():
    accounts = Admin.list_accounts()
    if request.method == 'POST':
        Admin.create_set(
            account_id = int(request.form.get('account_id') or 0),
            set_name = (request.form.get('set_name') or '').strip(),
            generator_prompt = (request.form.get('generator_prompt') or '').strip() or None,
            generator_model = (request.form.get('generator_model') or '').strip() or None,
            target_pool_size = int(request.form.get('target_pool_size') or 0)
        )
        return redirect(url_for('sets.list_sets'))
    return render_template('sets/edit.html', set_ = None, accounts = accounts)


@bp.route('/<int:set_id>/edit', methods = ['GET', 'POST'])
def edit_set(set_id):
    set_ = Admin.get_set(set_id)
    if set_ is None:
        return redirect(url_for('sets.list_sets'))
    accounts = Admin.list_accounts()

    if request.method == 'POST':
        Admin.edit_set(
            set_id = set_id,
            set_name = (request.form.get('set_name') or '').strip(),
            generator_prompt = (request.form.get('generator_prompt') or '').strip() or None,
            generator_model = (request.form.get('generator_model') or '').strip() or None,
            target_pool_size = int(request.form.get('target_pool_size') or 0)
        )
        return redirect(url_for('sets.list_sets'))

    return render_template('sets/edit.html', set_ = set_, accounts = accounts)


@bp.route('/<int:set_id>/delete', methods = ['POST'])
def delete_set(set_id):
    Admin.delete_set(set_id)
    return redirect(url_for('sets.list_sets'))


@bp.route('/<int:set_id>/generate', methods = ['POST'])
def generate_one(set_id):
    generator_client.generate_one(set_id)
    return redirect(url_for('sets.list_sets'))
