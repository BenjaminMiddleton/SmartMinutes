import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import uuid
import logging
from flask import Flask, request, jsonify, send_file, current_app, send_from_directory
from flask_cors import CORS
from marshmallow import Schema, fields, validate
from backend.config import Config
from backend.utils import handle_errors, APIError
from backend.logger import configure_logger
import backend.meeting_minutes
from werkzeug.utils import secure_filename
import threading
import io
from datetime import datetime
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sys
from pathlib import Path
from flask_socketio import SocketIO, emit
import json
import traceback
from fpdf import FPDF


# Near the top after imports
def configure_logging():
    """Configure logging to silence unnecessary messages."""
    # Silence socket.io and engineio loggers
    logging_level = logging.CRITICAL  # Most restrictive level

    # Configure socketio and engineio logging
    for logger in ['engineio', 'socketio', 'engineio.server', 'socketio.server']:
        logger = logging.getLogger(logger)
        logger.setLevel(logging_level)
        logger.propagate = False
        
        # Remove existing handlers and add null handler
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        logger.addHandler(logging.NullHandler())
    
    # Reduce werkzeug logs
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.WARNING)
    
    # Set lower level for app logger to ensure important messages still show
    app_logger = logging.getLogger('flask.app')
    app_logger.setLevel(logging.INFO)

# Apply logging configuration immediately
configure_logging()

# Add the backend directory to Python path if running directly
if __name__ == "__main__":
    backend_dir = Path(__file__).parent.parent
    sys.path.append(str(backend_dir))



def create_app(config=None):
    """Application factory pattern to create and configure Flask app."""
    app = Flask(__name__)
    
    # Load configuration
    if config:
        app.config.from_object(config)
    else:
        app.config.from_object(Config())
    
    # Set up CORS
    # Determine allowed origins based on environment
    let_origins = os.environ.get("CORS_ALLOWED_ORIGINS")
    

    # put origins here 

    app.logger.info(f"CORS allowed origins: {allowed_origins}")
    CORS(app, resources={
        r"/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True  # Changed to True for session support if needed
        }
    })
    
    # Ensure upload directory exists
    upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'uploads'))
    os.makedirs(upload_dir, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_dir

    # Set allowed extensions
    app.config['ALLOWED_AUDIO_EXTENSIONS'] = {'wav', 'mp3', 'ogg', 'flac', 'm4a'}
    app.config['ALLOWED_VTT_EXTENSIONS'] = {'vtt', 'srt'}

    # Set default file cleanup configuration
    app.config.setdefault('COMPLETED_JOB_RETENTION_HOURS', 24)
    app.config.setdefault('INTERRUPTED_JOB_RETENTION_MINUTES', 30)
    app.config.setdefault('ENABLE_SCHEDULED_CLEANUP', True)

    # Configure logging
    configure_logger(app)

    # Set up rate limiting
    limiter = Limiter(app=app, key_func=get_remote_address)

    # Initialize Socket.IO with allowed origins determined dynamically
    socketio = SocketIO(
        app,
        cors_allowed_origins=allowed_origins,
        async_mode='threading',
        transports=['websocket', 'polling']
    )
    app.socketio = socketio

    # Make socketio available at the module level
    app.socketio = socketio
    # Register Socket.IO event handlers
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection."""
        app.logger.info(f"Client connected: {request.sid}")
        emit('connection_response', {'status': 'connected', 'sid': request.sid})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        app.logger.info(f"Client disconnected: {request.sid}")
    
    @socketio.on('test_connection')
    def handle_test_connection(data):
        """Test socket connection."""
        app.logger.info(f"Test connection from client: {data}")
        emit('test_response', {'server': 'response', 'received': data, 'sid': request.sid})
    
    @socketio.on('rejoin_job')
    def handle_rejoin_job(data):
        """Handle client rejoining a job."""
        job_id = data.get('job_id')
        app.logger.info(f"Client {request.sid} rejoined job {job_id}")
        emit('rejoin_response', {'status': 'rejoined', 'job_id': job_id})
        
        # Check job status using your existing function
        job_status = get_job_status(job_id)
        
        # If job is completed, resend the results with all required fields
        if job_status.get('status') == 'completed' and 'minutes' in job_status:
            minutes = job_status.get('minutes', {})
            # Ensure we have all fields
            complete_minutes = ensure_complete_minutes(minutes)
            
            emit('processing_complete', {
                'job_id': job_id,
                'status': 'completed',
                'minutes': complete_minutes,
                'pdf_path': job_status.get('pdf_path', ''),
                'timestamp': job_status.get('timestamp', '')
            })
    
    # Create upload directory with absolute path
    upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'uploads'))
    os.makedirs(upload_dir, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_dir

    # Set allowed extensions
    app.config['ALLOWED_AUDIO_EXTENSIONS'] = {'wav', 'mp3', 'ogg', 'flac', 'm4a'}
    app.config['ALLOWED_VTT_EXTENSIONS'] = {'vtt', 'srt'}  # Add this line to define VTT extensions

    # Load configuration
    if config is None:
        if os.environ.get("FLASK_ENV", "development") == "production":
            from production_config import ProductionConfig
            app.config.from_object(ProductionConfig())
        else:
            app.config.from_object(Config())
    else:
        app.config.from_object(config)
        
    # Configure logging
    configure_logger(app)

    # Ensure upload directory exists
    UPLOAD_FOLDER = app.config['UPLOAD_FOLDER']
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Add default values for cleanup configuration
    app.config.setdefault('COMPLETED_JOB_RETENTION_HOURS', 24)  # Keep completed jobs for 24 hours
    app.config.setdefault('INTERRUPTED_JOB_RETENTION_MINUTES', 30)  # Keep interrupted jobs for 30 minutes
    app.config.setdefault('ENABLE_SCHEDULED_CLEANUP', True)  # Enable scheduled cleanup by default
    
    # Set up rate limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address
    )
    
    # Register routes and handlers
    register_routes(app, limiter)
    
    # Load ML models with app context
    with app.app_context():
        load_models()
        initialize_ai_models(app)  # Pass the app instance to the function
        
        # Start scheduled cleanup tasks if enabled
        if app.config.get('ENABLE_SCHEDULED_CLEANUP', True):
            app.cleanup_scheduler = schedule_cleanup_task(app)
            app.logger.info("Scheduled cleanup task initialized")
    return app, socketio

def register_routes(app, limiter):
    """Register all application routes."""
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint to verify system functionality."""
        try:
            # Check disk access (upload folder)
            upload_folder = app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            test_file = os.path.join(upload_folder, 'health_check.txt')
            with open(test_file, 'w') as f:
                f.write('health_check')
            os.remove(test_file)
            
            # Check PDF output folder
            pdf_folder = os.path.join(os.path.dirname(__file__), '..', 'pdf_output_files')
            os.makedirs(pdf_folder, exist_ok=True)
            
            # Check job results folder
            results_folder = os.path.join(os.path.dirname(__file__), '..', 'job_results')
            os.makedirs(results_folder, exist_ok=True)
            
            # Check model availability (if applicable)
            models_loaded = hasattr(app, 'models_loaded') and app.models_loaded
            
            return jsonify({
                'status': 'healthy',
                'version': '1.0.0',
                'timestamp': datetime.now().isoformat(),
                'upload_folder_writable': True,
                'pdf_folder_writable': True,
                'models_loaded': models_loaded
            })
        except Exception as e:
            app.logger.error(f"Health check failed: {str(e)}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()        
            }), 500

    @app.route("/upload", methods=["POST"])
    @limiter.limit("30 per minute")
    @handle_errors
    def upload_file():
        try:
            if "file" not in request.files:
                raise APIError("No file uploaded", status_code=400)
            file = request.files["file"]
            if not file or file.filename == "":
                raise APIError("No selected file", status_code=400)

            # Log detailed file information for debugging
            app.logger.info(f"Received file: {file.filename}, Content-Type: {file.content_type}")
            app.logger.info(f"Request data: {request.form}")
            
            original_filename = file.filename
            file_extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
            
            app.logger.info(f"File extension detected: {file_extension}")
            
            # Check if extension is allowed
            if file_extension not in app.config['ALLOWED_AUDIO_EXTENSIONS'] and file_extension not in app.config['ALLOWED_VTT_EXTENSIONS']:
                allowed_exts = list(app.config['ALLOWED_AUDIO_EXTENSIONS']) + list(app.config['ALLOWED_VTT_EXTENSIONS'])
                raise APIError(f"File type not allowed. Allowed types: {', '.join(allowed_exts)}", status_code=400)
            
            # Create job ID for tracking
            job_id = str(uuid.uuid4())
            
            # Save file using storage module
            filename = secure_filename(f"{job_id}_{file.filename}")
            filepath = save_file(app, file, filename)
            
            # Start processing in background thread
            processing_thread = threading.Thread(
                target=process_file_background,
                args=(app, file_extension, filepath, job_id, original_filename)
            )
            processing_thread.daemon = True
            processing_thread.start()
            
            # Return immediate response with job ID
            return jsonify({
                "status": "processing",
                "job_id": job_id,
                "message": "File uploaded successfully and processing started. Check status at /job_status/{job_id}"
            })
            
        except Exception as e:
            app.logger.error(f"Upload error: {str(e)}")
            raise APIError("Failed to process file", status_code=400)

    class ExportSchema(Schema):
        """Schema for document export validation."""
        title = fields.Str(required=True)
        duration = fields.Str(required=True)
        summary = fields.Str(required=True)
        action_points = fields.List(fields.Str(), required=True)
        transcription = fields.Str(required=True)

    @app.route("/export/<format>", methods=["POST"])
    @handle_errors
    def export_document(format):
        """Export meeting details as PDF or DOCX document."""
        # Validate input
        schema = ExportSchema()
        errors = schema.validate(request.json)
        if errors:
            raise APIError(f"Invalid request data: {errors}", 400)

        data = request.json
        if not data:
            raise APIError("No data provided", status_code=400)

        if format not in ['pdf', 'docx']:
            raise APIError("Unsupported format", status_code=400)

        # Generate appropriate document
        try:
            if format == 'docx':
                return generate_docx(data)
            else:
                return generate_pdf(data)
        except Exception as e:
            app.logger.error(f"Error generating document: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route("/export/pdf", methods=["POST"])
    def export_pdf():
        data = request.json
        return generate_downloadable_pdf(data)

    @app.route("/job_status/<job_id>", methods=["GET"])
    @limiter.exempt  # This will exempt this route from rate limiting
    def get_job_status_endpoint(job_id):
        """Check status of a processing job."""
        response_data = get_job_status(job_id)
        return jsonify(response_data)

    @app.route("/pdf/<filename>", methods=["GET"])
    def get_pdf(filename):
        """Serve PDF files."""
        try:
            pdf_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'pdf_output_files'))
            return send_file(
                os.path.join(pdf_dir, filename),
                mimetype='application/pdf',
                as_attachment=False
            )
        except Exception as e:
            app.logger.error(f"Error serving PDF: {str(e)}")
            return jsonify({"error": str(e)}), 404

    @app.route('/test-upload', methods=['POST'])
    def test_upload():
        """Test endpoint for file upload and verification."""
        try:
            if 'file' not in request.files:
                return jsonify({'error': 'No file part'}), 400
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
                
            if not allowed_file(file.filename, app.config['ALLOWED_AUDIO_EXTENSIONS']):
                return jsonify({'error': 'File type not allowed'}), 400
            
            # Generate unique filename
            filename = secure_filename(f"test_{uuid.uuid4()}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save file
            file.save(filepath)
            
            # Verify file exists and has content
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                result = {
                    'status': 'success',
                    'filename': filename,
                    'filepath': filepath,
                    'file_size': file_size,
                    'file_exists': True
                }
            else:
                result = {
                    'status': 'error',
                    'message': 'File was not saved correctly',
                    'filename': filename,
                    'filepath': filepath,
                    'file_exists': False
                }
            return jsonify(result)
        except Exception as e:
            app.logger.error(f"Test upload error: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/ping', methods=['GET'])
    def ping():
        """Simple endpoint to test API connectivity"""
        app.logger.info("Ping received from client")
        return jsonify({
            'status': 'success',
            'message': 'API server is running',
            'timestamp': datetime.now().isoformat()
        })

    @app.route('/debug-upload', methods=['POST'])
    def debug_upload():
        """Debug endpoint for troubleshooting file upload issues."""
        try:
            app.logger.info(f"Received debug upload request with Content-Type: {request.content_type}")
            app.logger.info(f"Request headers: {dict(request.headers)}")
            
            # Check if files are in the request
            if 'file' not in request.files:
                app.logger.error("No file part in request")
                return jsonify({'error': 'No file part'}), 400
            
            file = request.files['file']
            app.logger.info(f"File details: name={file.filename}, content_type={file.content_type}")
            
            if file.filename == '':
                app.logger.error("No selected file")
                return jsonify({'error': 'No selected file'}), 400
            
            # Get file content
            file_content = file.read()
            file_size = len(file_content)
            app.logger.info(f"File size: {file_size} bytes")
            
            # Check if content is empty
            if file_size == 0:
                return jsonify({'error': 'File is empty'}), 400
            
            # Check if file type is allowed
            file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            
            is_audio = file_extension in app.config['ALLOWED_AUDIO_EXTENSIONS']
            is_vtt = file_extension in app.config.get('ALLOWED_VTT_EXTENSIONS', set())
            
            return jsonify({
                'status': 'success',
                'message': 'File received successfully',
                'filename': file.filename,
                'content_type': file.content_type,
                'file_size': file_size,
                'file_extension': file_extension,
                'is_audio_extension': is_audio,
                'is_vtt_extension': is_vtt,
                'allowed_audio': list(app.config['ALLOWED_AUDIO_EXTENSIONS']),
                'allowed_vtt': list(app.config.get('ALLOWED_VTT_EXTENSIONS', set())),
                'request_method': request.method,
                'request_json': request.get_json(silent=True)
            })
            
        except Exception as e:
            app.logger.error(f"Debug upload error: {str(e)}", exc_info=True)
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route("/api/config", methods=["GET"])
    def get_config():
        """Return environment configuration."""
        # Add CORS headers since this endpoint might be called directly
        response = jsonify(Environment.get_config_json())
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    @app.route("/api/job_status/<job_id>", methods=["GET"])
    @limiter.exempt
    def get_job_status_endpoint_alias(job_id):
        """Alias for job status endpoint under /api path."""
        return get_job_status_endpoint(job_id)

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_static(path):
        """Serve static files from the React build."""
        # First check if file exists in static directory
        static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))
        
        # Check if path points to an existing file
        if path and os.path.exists(os.path.join(static_dir, path)):
            return send_from_directory(static_dir, path)
            
        # For the UI build directory (from Railway build process)
        ui_build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'UI', 'dist'))
        if os.path.exists(ui_build_dir):
            # Check if path exists in UI build directory
            if path and os.path.exists(os.path.join(ui_build_dir, path)):
                return send_from_directory(ui_build_dir, path)
            # Fallback to index.html for SPA routing
            try:
                return send_from_directory(ui_build_dir, 'index.html')
            except:
                app.logger.warning(f"Could not serve UI build files from {ui_build_dir}")
        
        # Final fallback to static/index.html
        try:
            return send_from_directory(static_dir, 'index.html')
        except:
            return jsonify({"error": "Not found"}), 404

def process_file_background(app, file_extension, filepath, job_id, original_filename):
    """Process the uploaded file in a background thread with improved error handling."""
    with app.app_context():
        try:
            # Verify file exists at the very start
            if not os.path.exists(filepath):
                error_msg = f"File {filepath} not found"
                app.logger.error(error_msg)
                # Diagnose: list files in UPLOAD_FOLDER and find similar names
                upload_dir = app.config['UPLOAD_FOLDER']
                app.logger.info(f"Checking upload directory: {upload_dir}")
                if os.path.exists(upload_dir):
                    files_in_dir = os.listdir(upload_dir)
                    app.logger.info(f"Files in upload directory: {files_in_dir}")
                    base_name = os.path.basename(filepath)
                    similar_files = [f for f in files_in_dir if base_name in f]
                    if similar_files:
                        app.logger.info(f"Found similar files: {similar_files}")
                        alt_filepath = os.path.join(upload_dir, similar_files[0])
                        app.logger.info(f"Attempting to use alternative file: {alt_filepath}")
                        filepath = alt_filepath
                        if os.path.exists(filepath):
                            app.logger.info(f"Alternative file exists, continuing with {filepath}")
                        else:
                            raise FileNotFoundError(error_msg)
                    else:
                        raise FileNotFoundError(error_msg)
                else:
                    app.logger.error(f"Upload directory {upload_dir} does not exist")
                    raise FileNotFoundError(error_msg)
            
            app.logger.info(f"Starting background processing for job: {job_id}")
            app.logger.info(f"File path: {filepath}, File extension: {file_extension}")
            app.logger.info(f"File exists: {os.path.exists(filepath)} Size: {os.path.getsize(filepath)} bytes")
            update_job_status(job_id, "started")
            
            # Prepare title from original filename
            base_filename = os.path.splitext(original_filename)[0]
            base_filename = base_filename.replace("_", " ").replace("-", " ").title()
            app.logger.info(f"Base filename (for title): {base_filename}")
            
            transcript = None
            speakers = []
            audio_duration = "N/A"
            duration_seconds = 0
            minutes = {}
            pdf_path = None
            
            try:
                if file_extension.lower() in app.config['ALLOWED_AUDIO_EXTENSIONS']:
                    app.logger.info(f"Processing audio file: {filepath}")
                    try:
                        app.socketio.emit("processing_update", {"job_id": job_id, "status": "processing_audio"})
                    except Exception as e:
                        app.logger.warning(f"SocketIO emit failed (processing_audio): {e}")

                elif file_extension.lower() in app.config['ALLOWED_VTT_EXTENSIONS']:
                    app.logger.info(f"Processing VTT file: {filepath}")
                    try:
                        app.socketio.emit("processing_update", {"job_id": job_id, "status": "processing_vtt"})
                    except Exception as e:
                        app.logger.warning(f"SocketIO emit failed (processing_vtt): {e}")
                    try:
                        transcript = handle_vtt_file(app, filepath)
                        speakers = []  # VTT does not include speakers
                        audio_duration = "N/A"
                        app.logger.info(f"VTT processing complete, transcript length: {len(transcript)}")
                    except Exception as vtt_error:
                        app.logger.error(f"VTT processing error: {str(vtt_error)}", exc_info=True)
                        raise Exception(f"VTT processing failed: {str(vtt_error)}")
                else:
                    raise ValueError(f"Unsupported file extension: {file_extension}")
                
                if not transcript or len(transcript) < 10:
                    app.logger.error("Transcript is empty or too short")
                    raise ValueError("Failed to extract meaningful content from the file")
                
                try:
                    app.socketio.emit("processing_update", {"job_id": job_id, "status": "generating_minutes"})
                except Exception as e:
                    app.logger.warning(f"SocketIO emit failed (generating_minutes): {e}")
                meeting_title = base_filename
                force_chunking = len(transcript) > 8000  # force chunking for long transcripts
                app.logger.info(f"Generating meeting minutes (length: {len(transcript)}, force_chunking: {force_chunking})")
                try:
                    minutes = generate_meeting_minutes(transcript, speakers=speakers, duration_seconds=duration_seconds)
                    minutes["title"] = meeting_title
                    minutes["duration"] = audio_duration
                    minutes["speakers"] = speakers
                    minutes["transcription"] = transcript
                    app.logger.info(f"Minutes generated successfully, summary length: {len(minutes.get('summary', ''))}")
                except Exception as minutes_error:
                    app.logger.error(f"Minutes generation error: {str(minutes_error)}", exc_info=True)
                    raise Exception(f"Minutes generation failed: {str(minutes_error)}")
            except Exception as processing_error:
                app.logger.error(f"Error during processing: {str(processing_error)}", exc_info=True)
                update_job_status(job_id, "error", error=str(processing_error))
                try:
                    app.socketio.emit("processing_error", {"job_id": job_id, "error": str(processing_error), "timestamp": datetime.now().isoformat()})
                except Exception as emit_error:
                    app.logger.warning(f"SocketIO emit failed (processing_error): {emit_error}")
                return
            
            try:
                app.socketio.emit("processing_update", {"job_id": job_id, "status": "generating_pdf"})
            except Exception as e:
                app.logger.warning(f"SocketIO emit failed (generating_pdf): {e}")
            try:
                app.logger.info("Generating PDF...")
                pdf_path = generate_pdf(minutes, job_id, original_filename)
                app.logger.info(f"PDF generated at {pdf_path}")
            except Exception as pdf_error:
                app.logger.error(f"PDF generation error: {str(pdf_error)}", exc_info=True)
                pdf_output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'pdf_output_files'))
                os.makedirs(pdf_output_dir, exist_ok=True)
                txt_filename = f"{job_id}_minutes.txt"
                txt_path = os.path.join(pdf_output_dir, txt_filename)
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(f"TITLE: {minutes.get('title', 'Meeting Minutes')}\n\n")
                    f.write(f"DURATION: {minutes.get('duration', 'N/A')}\n\n")
                    f.write(f"SUMMARY:\n{minutes.get('summary', 'No summary available')}\n\n")
                    f.write("ACTION POINTS:\n")
                    for point in minutes.get('action_points', []):
                        f.write(f"- {point}\n")
                    f.write("\n\nTRANSCRIPTION:\n")
                    f.write(minutes.get('transcription', 'No transcription available'))
                app.logger.info(f"Created fallback text file: {txt_path}")
                pdf_path = txt_path
            
            minutes = ensure_complete_minutes(minutes)
            minutes["pdf_path"] = pdf_path
            update_job_status(job_id, "completed", minutes=minutes)
            try:
                app.socketio.emit("processing_complete", {
                    "job_id": job_id,
                    "status": "completed",
                    "pdf_path": pdf_path,
                    "minutes": {
                        "title": minutes.get("title", ""),
                        "duration": minutes.get("duration", "00:00"),
                        "summary": minutes.get("summary", ""),
                        "action_points": minutes.get("action_points", []),
                        "transcription": minutes.get("transcription", ""),
                        "speakers": minutes.get("speakers", [])
                    },
                    "timestamp": datetime.now().isoformat(),
                    "eventType": "processing_complete"
                })
            except Exception as e:
                app.logger.warning(f"SocketIO emit failed (processing_complete): {e}")
            app.logger.info(f"Completed processing for job: {job_id}")
        except Exception as e:
            app.logger.error(f"Error in background processing: {str(e)}", exc_info=True)
            update_job_status(job_id, "error", error=str(e))
            try:
                app.socketio.emit("processing_error", {"job_id": job_id, "error": str(e), "timestamp": datetime.now().isoformat()})
            except Exception as emit_error:
                app.logger.warning(f"SocketIO emit failed (processing_error): {emit_error}")
        finally:
            # Clean up the uploaded file in any case (success or error)
            cleanup_file(app, filepath)
            # Run a targeted cleanup of any old files (more than 1 hour old) in the uploads directory
            # This helps clean up any "orphaned" files that might have been missed
            if app.config.get('ENABLE_IMMEDIATE_UPLOADS_CLEANUP', True):
                try:
                    uploads_dir = app.config.get('UPLOAD_FOLDER', 'uploads')
                    app.logger.info(f"Running immediate cleanup for old files in uploads directory: {uploads_dir}")
                    
                    # Import only when needed
                    from backend.cleanup import JobCleaner
                    
                    cleaner = JobCleaner(
                        job_results_dir=os.path.join(app.root_path, "..", "job_results"),
                        # Use more aggressive cleanup for immediate cleanup
                        completed_job_retention_hours=1,  # Clean files older than 1 hour
                        interrupted_job_retention_minutes=30  # Clean interrupted jobs older than 30 mins
                    )
                    # Only clean empty uploads, not job files
                    result = cleaner.cleanup_empty_uploads()
                    app.logger.info(f"Immediate cleanup completed: {result} empty files removed")
                except Exception as cleanup_err:
                    app.logger.warning(f"Error in immediate cleanup: {str(cleanup_err)}")

def ensure_complete_minutes(minutes):
    """Ensure minutes has all required fields, adding empty values for any missing fields."""
    required_fields = {
        "title": "",
        "duration": "00:00",
        "summary": "",
        "action_points": [],
        "transcription": "",
        "speakers": []
    }
    
    for field, default_value in required_fields.items():
        if field not in minutes or minutes[field] is None:
            minutes[field] = default_value
    
    return minutes

# App entry point - only call create_app once
app, socketio = create_app()

# Apply logging configuration again to ensure it takes effect
configure_logging()

if __name__ == "__main__":
    # Silence logs again just to be sure
    configure_logging()
    # Load models
    load_models()
    # Run with socketio instead of app.run()
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get("PORT", "5000")), debug=False)