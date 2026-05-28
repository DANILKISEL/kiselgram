from datetime import datetime
from flask import Blueprint, request, jsonify
from app import db
from app.models import User, Contact, BlockedUser
from app.utils.helpers import get_current_user_id

spav2_contacts_bp = Blueprint('spav2_contacts', __name__, url_prefix='/api')


@spav2_contacts_bp.route('/contacts', methods=['GET'])
def get_contacts():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    contacts = Contact.query.filter_by(user_id=current_user_id).all()
    result = []
    for c in contacts:
        user = User.query.get(c.contact_id)
        if user:
            result.append({
                'user_id': user.id,
                'username': user.username,
                'display_name': user.display_name or user.username,
                'avatar_url': user.avatar_url,
                'custom_name': c.custom_name,
                'is_online': getattr(user, 'is_online', False),
                'last_seen': user.last_seen.isoformat() if user.last_seen else None,
                'added_at': c.created_at.isoformat() if c.created_at else None
            })

    return jsonify({'success': True, 'data': {'contacts': result, 'total': len(result)}})


@spav2_contacts_bp.route('/contacts', methods=['POST'])
def add_contact():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    data = request.get_json() or {}
    contact_id = data.get('contact_id')
    if not contact_id:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'contact_id is required'}}), 400

    existing = Contact.query.filter_by(user_id=current_user_id, contact_id=contact_id).first()
    if existing:
        return jsonify({'success': False, 'error': {'code': 'ALREADY_CONTACT', 'message': 'User is already in your contacts'}}), 400

    user = User.query.get(contact_id)
    if not user:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'User not found'}}), 404

    c = Contact(user_id=current_user_id, contact_id=contact_id, created_at=datetime.utcnow())
    db.session.add(c)
    db.session.commit()

    return jsonify({'success': True, 'data': {'contact': {
        'user_id': user.id, 'username': user.username,
        'display_name': user.display_name or user.username,
        'avatar_url': user.avatar_url,
        'custom_name': None, 'added_at': c.created_at.isoformat() if c.created_at else None
    }}}), 201


@spav2_contacts_bp.route('/contacts/rename', methods=['POST'])
def rename_contact():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    data = request.get_json() or {}
    contact_id = data.get('contact_id')
    name = data.get('name', '').strip()

    if not contact_id:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'contact_id is required'}}), 400

    contact = Contact.query.filter_by(user_id=current_user_id, contact_id=contact_id).first()
    if not contact:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Contact not found'}}), 404

    contact.custom_name = name
    db.session.commit()
    return jsonify({'success': True, 'data': {'user_id': contact_id, 'custom_name': name, 'updated_at': datetime.utcnow().isoformat()}})


@spav2_contacts_bp.route('/contacts/<int:contact_id>', methods=['DELETE'])
def remove_contact(contact_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    contact = Contact.query.filter_by(user_id=current_user_id, contact_id=contact_id).first()
    if contact:
        db.session.delete(contact)
        db.session.commit()
    return jsonify({'success': True, 'data': {'message': 'Contact removed'}})


@spav2_contacts_bp.route('/blocked_users', methods=['GET'])
def get_blocked_users():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    blocks = BlockedUser.query.filter_by(user_id=current_user_id).all()
    result = []
    for b in blocks:
        user = User.query.get(b.blocked_user_id)
        result.append({
            'user_id': b.blocked_user_id,
            'username': user.username if user else 'Unknown',
            'avatar_url': user.avatar_url if user else None,
            'blocked_at': b.created_at.isoformat() if b.created_at else None
        })

    return jsonify({'success': True, 'data': {'blocked_users': result, 'total': len(result)}})


@spav2_contacts_bp.route('/block_user/<int:user_id>', methods=['POST'])
def block_user(user_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    existing = BlockedUser.query.filter_by(user_id=current_user_id, blocked_user_id=user_id).first()
    if not existing:
        b = BlockedUser(user_id=current_user_id, blocked_user_id=user_id, created_at=datetime.utcnow())
        db.session.add(b)
        db.session.commit()
        blocked_at = datetime.utcnow().isoformat()
    else:
        blocked_at = existing.created_at.isoformat() if existing.created_at else datetime.utcnow().isoformat()

    user = User.query.get(user_id)
    return jsonify({'success': True, 'data': {
        'blocked_user_id': user_id,
        'username': user.username if user else None,
        'blocked_at': blocked_at
    }})


@spav2_contacts_bp.route('/unblock_user/<int:user_id>', methods=['POST'])
def unblock_user(user_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    existing = BlockedUser.query.filter_by(user_id=current_user_id, blocked_user_id=user_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()

    return jsonify({'success': True, 'data': {'unblocked_user_id': user_id, 'username': User.query.get(user_id).username if User.query.get(user_id) else None}})
