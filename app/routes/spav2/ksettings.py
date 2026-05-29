from flask import Blueprint, request, jsonify
from app import db
from app.models import UserKSettings
from app.utils.helpers import get_current_user_id

spav2_ksettings_bp = Blueprint('spav2_ksettings', __name__, url_prefix='/api')


@spav2_ksettings_bp.route('/k/settings', methods=['GET'])
def get_settings():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    ks = UserKSettings.query.filter_by(user_id=current_user_id).first()
    if not ks:
        ks = UserKSettings(user_id=current_user_id, settings={})
        db.session.add(ks)
        db.session.commit()

    return jsonify({'success': True, 'data': ks.to_dict()})


@spav2_ksettings_bp.route('/k/settings', methods=['PUT'])
def save_settings():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    data = request.get_json() or {}
    settings = data.get('settings')
    if settings is None:
        return jsonify({'success': False, 'error': {'code': 'INVALID_INPUT', 'message': 'settings field required'}}), 400

    ks = UserKSettings.query.filter_by(user_id=current_user_id).first()
    if not ks:
        ks = UserKSettings(user_id=current_user_id, settings=settings)
        db.session.add(ks)
    else:
        ks.settings = settings

    db.session.commit()
    return jsonify({'success': True, 'data': ks.to_dict()})
