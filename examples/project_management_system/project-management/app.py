@app.route('/review/approve', methods=['POST'])
@login_required
def approve_review():
    data = request.get_json()
    context = {'author_id': data.get('author_id')}
    user = current_zrb_user()
    op = store.get_operation('review:approve')
    zone = get_current_zone()
    if not engine.decide(user, op, zone, mode='inferential', context=context):
        abort(403)
    return jsonify({"status": "review approved"})