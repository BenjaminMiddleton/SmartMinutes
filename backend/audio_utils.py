"""Audio processing utilities for the meeting minutes application."""

import os
from pydub import AudioSegment
from flask import current_app
from werkzeug.utils import secure_filename
import uuid
from backend.utils import APIError
import logging  # <== new import
logger = logging.getLogger(__name__)  # <== new logger definition

def process_audio_duration(file_path):
    """Calculate audio duration from file path."""
    try:
        audio = AudioSegment.from_file(file_path)
        return len(audio) / 1000.0
    except Exception as e:
        logger.error(f"Error calculating audio duration: {str(e)}")
        return 0.0  # Return 0.0 instead of raising an exception for better error handling

def format_duration(duration_seconds):
    """Format duration in seconds to HH:MM:SS or MM:SS."""
    if duration_seconds >= 3600:
        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)
        seconds = int(duration_seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

def process_audio_file(app, file):
    """Process audio file through diarization and transcription."""
    from speaker_diarization import diarize_audio
    import meeting_minutes
    
    filepath = None
    try:
        app.logger.info(f"Received file: {file.filename}, Content-Type: {file.content_type}")
        
        # Validate file type
        if not allowed_file(file.filename, app.config['ALLOWED_AUDIO_EXTENSIONS']):
            raise APIError("Audio file type not supported")

        # Generate unique filename
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        
        # Save file locally first
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Run diarization

            
    finally:
        if filepath and os.path.exists(filepath):
            cleanup_file(app, filepath)

def allowed_file(filename, allowed_extensions):
    """Check if a filename has an allowed extension."""
    if not filename:
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def cleanup_file(app, filepath):
    """Remove a temporary file from disk with error handling."""
    if not filepath:
        return
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            app.logger.info(f"Cleaned up file: {os.path.basename(filepath)}")
    except Exception as e:
        app.logger.error(f"Error cleaning up file {filepath}: {str(e)}")

def process_vtt_file(app, file):
    """Extract text content from a VTT file."""
    filepath = None
    try:
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        transcript = handle_vtt_file(app, filepath)
        return transcript, []
    finally:
        if filepath and os.path.exists(filepath):
            cleanup_file(app, filepath)

def handle_vtt_file(app, filepath):
    """Parse VTT file to extract plain transcript."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        transcription = []
        for line in lines:
            line = line.strip()
            if line and '-->' not in line and not line.isdigit() and line != 'WEBVTT':
                transcription.append(line)

        return "\n".join(transcription)
    except Exception as e:
        app.logger.error(f"Error processing VTT file: {str(e)}")
        raise APIError("Failed to process VTT file")