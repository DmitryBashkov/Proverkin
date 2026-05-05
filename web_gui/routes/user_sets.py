from flask import Blueprint, render_template, request, redirect, url_for

from database.admin import Admin

bp = Blueprint('user_sets', __name__, url_prefix = '/users/<int:user_id>/sets')


@bp.route('/', methods = ['GET', 'POST'])
def manage(user_id):
    user = Admin.get_user_full(user_id)
    if user is None:
        return redirect(url_for('users.list_users'))

    # все доступные set'ы из аккаунта пользователя + общие (account_id=0 = trial)
    account_id = user[5]
    candidate_sets = Admin.list_sets()  # показываем все, отфильтрует админ глазами

    if request.method == 'POST':
        action = request.form.get('action')
        set_id = int(request.form.get('set_id') or 0)
        qty = int(request.form.get('qty') or 0)

        if action == 'remove':
            Admin.remove_user_set(user_id, set_id)
        else:
            if qty > 0 and set_id > 0:
                Admin.upsert_user_set(user_id, set_id, qty)
        return redirect(url_for('user_sets.manage', user_id = user_id))

    bound = Admin.list_user_sets(user_id)
    return render_template(
        'user_sets/manage.html',
        user = user,
        bound = bound,
        candidate_sets = candidate_sets
    )
