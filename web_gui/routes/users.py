from flask import Blueprint, render_template, request, redirect, url_for, flash

from database.admin import Admin
from utils.clients import quiz_client

bp = Blueprint('users', __name__, url_prefix = '/users')


@bp.route('/')
def list_users():
    users = Admin.list_users()
    return render_template('users/list.html', users = users)


@bp.route('/new', methods = ['GET', 'POST'])
def new_user():
    accounts = Admin.list_accounts()
    if request.method == 'POST':
        username = (request.form.get('telegram_username') or '').strip().lstrip('@')
        real_name = (request.form.get('real_name') or '').strip()
        account_id = int(request.form.get('account_id') or 0)
        user_type = request.form.get('user_type') or 'user'
        active = 1 if request.form.get('active') == 'on' else 0

        Admin.create_user(
            telegram_username = username,
            real_name = real_name,
            account_id = account_id,
            user_type = user_type,
            active = active
        )
        return redirect(url_for('users.list_users'))

    return render_template('users/edit.html', user = None, accounts = accounts)


@bp.route('/<int:user_id>/edit', methods = ['GET', 'POST'])
def edit_user(user_id):
    user = Admin.get_user_full(user_id)
    if user is None:
        return redirect(url_for('users.list_users'))

    accounts = Admin.list_accounts()

    if request.method == 'POST':
        username = (request.form.get('telegram_username') or '').strip().lstrip('@')
        real_name = (request.form.get('real_name') or '').strip()
        account_id = int(request.form.get('account_id') or 0)
        user_type = request.form.get('user_type') or 'user'
        active = 1 if request.form.get('active') == 'on' else 0

        Admin.edit_user(
            user_id = user_id,
            telegram_username = username,
            real_name = real_name,
            account_id = account_id,
            user_type = user_type,
            active = active
        )
        return redirect(url_for('users.list_users'))

    return render_template('users/edit.html', user = user, accounts = accounts)


@bp.route('/<int:user_id>/delete', methods = ['POST'])
def delete_user(user_id):
    Admin.delete_user(user_id)
    return redirect(url_for('users.list_users'))


@bp.route('/<int:user_id>/schedule', methods = ['POST'])
def schedule_user(user_id):
    user = Admin.get_user_full(user_id)
    if user is None or user[2] is None:
        # либо нет юзера, либо у него нет chat_id (не писал боту)
        return redirect(url_for('users.list_users'))

    quiz_client.schedule_user(
        chat_id = user[2],
        username = user[1],
        notify = True
    )
    return redirect(url_for('users.list_users'))
