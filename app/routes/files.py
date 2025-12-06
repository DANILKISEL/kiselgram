from flask import Blueprint, request, jsonify, send_file
import os
import uuid
from PIL import Image
from app import db
from app.models import Message
from app.utils.helpers import get_current_user, get_current_user_id, allowed_file, get_file_type, create_thumbnail, format_file_size
from app import db

files_bp = Blueprint('files', __name__)

@files_bp.route('/upload_file', methods=['POST'])
def upload_file():
    if not get_current_user():
        return jsonify({'error': 'Not authenticated'}), 401

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Get additional data
    receiver_id = request.form.get('receiver_id', type=int)
    group_id = request.form.get('group_id', type=int)
    channel_id = request.form.get('channel_id', type=int)
    message_text = request.form.get('message', '')

    if not receiver_id and not group_id and not channel_id:
        return jsonify({'error': 'No destination specified'}), 400

    if file and allowed_file(file.filename):
        try:
            # Generate unique filename
            file_ext = file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
            file_type = get_file_type(file.filename)

            # Determine upload directory
            if file_type == 'image':
                upload_dir = 'images'
            elif file_type in ['audio', 'video']:
                upload_dir = 'media'
            else:
                upload_dir = 'documents'

            file_path = os.path.join(app.config['UPLOAD_FOLDER'], upload_dir, unique_filename)
            file.save(file_path)
            file_size = os.path.getsize(file_path)

            # Create thumbnail for images
            thumbnail_path = None
            if file_type == 'image':
                thumbnail_filename = f"thumb_{unique_filename}"
                thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], 'images', thumbnail_filename)
                if create_thumbnail(file_path, thumbnail_path):
                    thumbnail_path = f"uploads/images/{thumbnail_filename}"

            # Create message record
            new_message = Message(
                content=message_text,
                sender_id=get_current_user_id(),
                receiver_id=receiver_id or get_current_user_id(),
                group_id=group_id,
                channel_id=channel_id,
                has_attachment=True,
                file_type=file_type,
                file_name=file.filename,
                file_path=f"uploads/{upload_dir}/{unique_filename}",
                file_size=file_size,
                thumbnail_path=thumbnail_path
            )

            db.session.add(new_message)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': {
                    'id': new_message.id,
                    'content': new_message.content,
                    'sender_name': new_message.sender.username,
                    'timestamp': new_message.timestamp.strftime('%H:%M'),
                    'is_own': True,
                    'has_attachment': True,
                    'file_type': new_message.file_type,
                    'file_name': new_message.file_name,
                    'file_size': format_file_size(new_message.file_size),
                    'file_url': f"/{new_message.file_path}",
                    'thumbnail_url': f"/{new_message.thumbnail_path}" if new_message.thumbnail_path else None
                }
            })

        except Exception as e:
            return jsonify({'error': f'Upload failed: {str(e)}'}), 500

    return jsonify({'error': 'File type not allowed'}), 400


@files_bp.route('/uploads/<path:filename>')
def serve_file(filename):
    """Serve uploaded files"""
    try:
        from app import app  # Import app here to avoid circular imports

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Security check
        if not os.path.abspath(file_path).startswith(os.path.abspath(app.config['UPLOAD_FOLDER'])):
            return "Access denied", 403

        if os.path.exists(file_path):
            return send_file(file_path)
        else:
            return "File not found", 404
    except Exception as e:
        return str(e), 500

@files_bp.route('/api/delete_message/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    if not get_current_user():
        return jsonify({'error': 'Not authenticated'}), 401

    message = Message.query.get_or_404(message_id)

    if message.sender_id != get_current_user_id():
        return jsonify({'error': 'Not authorized'}), 403

    try:
        if message.has_attachment and message.file_path:
            file_path = message.file_path
            if os.path.exists(file_path):
                os.remove(file_path)

            if message.thumbnail_path and os.path.exists(message.thumbnail_path):
                os.remove(message.thumbnail_path)

        db.session.delete(message)
        db.session.commit()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500