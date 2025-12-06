from flask import Blueprint, request, jsonify, send_file, current_app
import os
import uuid
import mimetypes
from app import db
from app.models import Message
from app.utils import get_current_user, get_current_user_id, get_file_type, create_thumbnail, format_file_size

files_bp = Blueprint('files', __name__)


def allowed_file(filename):
    """Check if file extension is allowed"""
    if '.' not in filename:
        return False

    ext = filename.rsplit('.', 1)[1].lower()

    # Define allowed extensions locally
    allowed_extensions = {
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp',  # images
        'pdf', 'doc', 'docx', 'txt', 'rtf',  # documents
        'zip', 'rar', '7z',  # archives
        'mp3', 'mp4', 'm4a', 'wav', 'ogg', 'avi', 'mov', 'mkv'  # media
    }

    return ext in allowed_extensions


@files_bp.route('/uploads/<path:filename>')
def serve_file(filename):
    """Serve uploaded files - SIMPLIFIED VERSION"""
    try:
        # Try multiple possible locations
        possible_paths = [
            os.path.join('uploads', filename),
            os.path.join(os.getcwd(), 'uploads', filename),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'uploads', filename)
        ]

        for file_path in possible_paths:
            file_path = os.path.normpath(file_path)
            if os.path.exists(file_path):
                return send_file(file_path)

        return "File not found", 404
    except Exception as e:
        return str(e), 500


@files_bp.route('/upload_file', methods=['POST'])
def upload_file():
    """Handle file uploads - SIMPLIFIED VERSION"""
    if not get_current_user():
        return jsonify({'error': 'Not authenticated'}), 401

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

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

        # Save file
        upload_path = os.path.join('uploads', upload_dir, unique_filename)
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        file.save(upload_path)

        # Create message (simplified)
        return jsonify({
            'success': True,
            'filename': unique_filename,
            'url': f'/uploads/{upload_dir}/{unique_filename}'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Test route
@files_bp.route('/test_uploads')
def test_uploads():
    """Test if uploads directory is accessible"""
    try:
        result = []
        if os.path.exists('uploads'):
            for root, dirs, files in os.walk('uploads'):
                for file in files:
                    path = os.path.join(root, file)
                    result.append({
                        'file': file,
                        'path': path,
                        'exists': os.path.exists(path),
                        'size': os.path.getsize(path) if os.path.exists(path) else 0
                    })

        return jsonify({
            'uploads_exists': os.path.exists('uploads'),
            'files': result,
            'current_dir': os.getcwd()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500