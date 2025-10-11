"""
Upload Blueprint - Handles file upload and management routes
"""
from flask import Blueprint, render_template, request, send_file, jsonify, abort
from models import UploadDetail, OtrsTicket, db
from services import ticket_service, analysis_service
from utils import validate_json_data
import os
import glob
from werkzeug.utils import secure_filename

upload_bp = Blueprint('upload', __name__, url_prefix='/upload')

@upload_bp.route('/')
def view_uploads():
    """View all uploaded data sources"""
    upload_sessions = UploadDetail.query.order_by(UploadDetail.upload_time.desc()).all()
    return render_template('uploads.html', upload_sessions=upload_sessions)

@upload_bp.route('/download/<int:upload_id>')
def download_upload(upload_id):
    """Download the original Excel file for a specific upload"""
    from config import Config
    
    upload_record = UploadDetail.query.get_or_404(upload_id)
    uploads_dir = Config.UPLOAD_FOLDER or 'uploads'
    uploads_path = os.path.abspath(os.path.join(upload_record.__class__.query.session.get_bind().url.database.rsplit('/', 1)[0], uploads_dir)) if '://' in str(upload_record.__class__.query.session.get_bind().url) else os.path.abspath(os.path.join(os.getcwd(), uploads_dir))

    if not os.path.isdir(uploads_path):
        abort(404, description='上传文件目录不存在')

    def _candidate_path(filename):
        if not filename:
            return None
        candidate = os.path.abspath(os.path.join(uploads_path, filename))
        try:
            if os.path.commonpath([uploads_path, candidate]) != uploads_path:
                return None
        except ValueError:
            return None
        return candidate if os.path.exists(candidate) else None

    file_path = _candidate_path(upload_record.stored_filename)

    if not file_path:
        safe_original = secure_filename(upload_record.filename) if upload_record.filename else None
        if safe_original:
            pattern = os.path.join(uploads_path, f"*_{safe_original}")
            matches = sorted(glob.glob(pattern), reverse=True)

            if upload_record.upload_time:
                prefix = upload_record.upload_time.strftime('%Y%m%d_%H%M%S')
                for match in matches:
                    if os.path.basename(match).startswith(prefix):
                        file_path = match
                        break

            if not file_path and matches:
                file_path = matches[0]

            if file_path:
                stored_name = os.path.basename(file_path)
                if stored_name != upload_record.stored_filename:
                    upload_record.stored_filename = stored_name
                    try:
                        db.session.commit()
                    except Exception:
                        db.session.rollback()
        
        if file_path:
            file_path = os.path.abspath(file_path)
            try:
                if os.path.commonpath([uploads_path, file_path]) != uploads_path:
                    file_path = None
            except ValueError:
                file_path = None

    if not file_path:
        abort(404, description='上传文件不存在或已被删除')

    download_name = upload_record.filename or os.path.basename(file_path)
    return send_file(file_path, as_attachment=True, download_name=download_name)

@upload_bp.route('/details/<filename>')
def view_upload_details(filename):
    """View details of a specific upload file"""
    # Find the upload session for this filename
    upload_session = UploadDetail.query.filter_by(filename=filename).first()
    
    if not upload_session:
        # If no UploadDetail record found, create a mock one for backward compatibility
        upload_session = type('MockSession', (), {
            'filename': filename,
            'upload_time': None,
            'record_count': 0,
            'import_mode': 'Unknown'
        })()
    
    # Get tickets for this filename
    tickets = OtrsTicket.query.filter_by(data_source=filename).all()
    
    return render_template('upload_details.html', upload_session=upload_session, tickets=tickets)

@upload_bp.route('/process', methods=['POST'])
def upload_file():
    """Handle file upload and analysis"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Process upload using ticket service
        result = ticket_service.process_upload(file)
        
        # Get analysis statistics
        stats = analysis_service.analyze_tickets_from_database()
        
        # Log the analysis
        analysis_service.log_statistic_query(
            'main_analysis',
            upload_id=result['upload_id'],
            record_count=result['total_records']
        )
        
        # Prepare response
        response_data = {
            'success': True,
            'total_records': result['total_records'],
            'new_records_count': result['new_records_count'],
            'stats': stats,
            'filename': result['filename']
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500