"""
ImageLab — Image CRUD Routes
"""
import os
import uuid
from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from PIL import Image as PILImage
from app import db
from app.models import Image

images_bp = Blueprint("images", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp", "tiff"}


@images_bp.route("/files/<filename>", methods=["GET"])
def serve_file(filename):
    """Serve an image file publicly. UUID filenames are unguessable = secure."""
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    file_path = os.path.join(upload_folder, filename)

    # Prevent directory traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        return jsonify({"errors": ["Invalid filename."]}), 400

    if not os.path.exists(file_path):
        return jsonify({"errors": ["File not found."]}), 404

    return send_file(file_path)


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _save_upload(file, upload_folder: str) -> tuple:
    """Save uploaded file with a unique name. Returns (storage_path, mime_type)."""
    ext = file.filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    storage_path = os.path.join(upload_folder, unique_name)
    file.save(storage_path)
    mime_type = file.content_type or f"image/{ext}"
    return storage_path, mime_type


@images_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload():
    """Upload one or more images."""
    user_id = int(get_jwt_identity())
    upload_folder = current_app.config["UPLOAD_FOLDER"]

    if "file" not in request.files:
        return jsonify({"errors": ["No file part in the request."]}), 400

    files = request.files.getlist("file")
    uploaded = []

    for f in files:
        if f.filename == "":
            continue
        if not _allowed_file(f.filename):
            continue

        storage_path, mime_type = _save_upload(f, upload_folder)
        file_size = os.path.getsize(storage_path)

        # Get dimensions
        try:
            with PILImage.open(storage_path) as img:
                width, height = img.size
        except Exception:
            width, height = None, None

        image = Image(
            user_id=user_id,
            original_filename=f.filename,
            storage_path=storage_path,
            file_size=file_size,
            mime_type=mime_type,
            width=width,
            height=height,
        )
        db.session.add(image)
        db.session.commit()
        uploaded.append(image.to_dict())

    if not uploaded:
        return jsonify({"errors": ["No valid image files were uploaded."]}), 400

    return jsonify({"images": uploaded}), 201


@images_bp.route("", methods=["GET"])
@jwt_required()
def list_images():
    """List all images for the current user."""
    user_id = int(get_jwt_identity())
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    pagination = (
        Image.query.filter_by(user_id=user_id)
        .order_by(Image.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    return jsonify({
        "images": [img.to_dict() for img in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
    }), 200


@images_bp.route("/<int:image_id>", methods=["GET"])
@jwt_required()
def get_image(image_id):
    """Get image metadata or download the file."""
    user_id = int(get_jwt_identity())
    image = Image.query.filter_by(id=image_id, user_id=user_id).first()
    if image is None:
        return jsonify({"errors": ["Image not found."]}), 404

    if request.args.get("download") == "true":
        return send_file(
            image.storage_path,
            as_attachment=True,
            download_name=image.original_filename,
        )

    return jsonify({"image": image.to_dict()}), 200


@images_bp.route("/<int:image_id>", methods=["DELETE"])
@jwt_required()
def delete_image(image_id):
    """Delete an image."""
    user_id = int(get_jwt_identity())
    image = Image.query.filter_by(id=image_id, user_id=user_id).first()
    if image is None:
        return jsonify({"errors": ["Image not found."]}), 404

    # Remove file from disk
    if os.path.exists(image.storage_path):
        os.remove(image.storage_path)

    db.session.delete(image)
    db.session.commit()
    return jsonify({"message": "Image deleted."}), 200
