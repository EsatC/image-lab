"""
ImageLab — Image Processing & Conversion Routes
"""
import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from PIL import Image as PILImage

from app import db
from app.models import Image
from app.services.image_processor import OPERATIONS, SUPPORTED_FORMATS, convert_format

processing_bp = Blueprint("processing", __name__)


@processing_bp.route("/<int:image_id>/process", methods=["POST"])
@jwt_required()
def process_image(image_id):
    """Apply an image processing operation."""
    user_id = int(get_jwt_identity())
    image = Image.query.filter_by(id=image_id, user_id=user_id).first()
    if image is None:
        return jsonify({"errors": ["Image not found."]}), 404

    data = request.get_json() or {}
    operation = data.get("operation")
    params = data.get("params", {})

    if operation not in OPERATIONS:
        return jsonify({
            "errors": [f"Unknown operation '{operation}'."],
            "available_operations": list(OPERATIONS.keys()),
        }), 400

    # Open, process, save
    try:
        with PILImage.open(image.storage_path) as img:
            img = img.convert("RGB") if img.mode not in ("RGB", "L") else img
            fn = OPERATIONS[operation]
            # Pass extra params if the function accepts them
            import inspect
            sig = inspect.signature(fn)
            if len(sig.parameters) > 1:
                processed = fn(img, **params)
            else:
                processed = fn(img)

        # Save processed image
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        ext = image.original_filename.rsplit(".", 1)[-1].lower()
        if ext in ("jpg", "jpeg"):
            save_ext = "jpg"
            pil_format = "JPEG"
        else:
            save_ext = ext
            pil_format = ext.upper()

        unique_name = f"{uuid.uuid4().hex}.{save_ext}"
        storage_path = os.path.join(upload_folder, unique_name)

        if processed.mode == "L" and pil_format == "JPEG":
            processed.save(storage_path, format=pil_format)
        else:
            processed.save(storage_path, format=pil_format)

        file_size = os.path.getsize(storage_path)
        w, h = processed.size

        new_image = Image(
            user_id=user_id,
            original_filename=f"{operation}_{image.original_filename}",
            storage_path=storage_path,
            file_size=file_size,
            mime_type=image.mime_type,
            width=w,
            height=h,
            parent_id=image.id,
            processing_info=operation,
        )
        db.session.add(new_image)
        db.session.commit()

        return jsonify({"image": new_image.to_dict()}), 201

    except Exception as e:
        current_app.logger.error(f"Processing error: {e}")
        return jsonify({"errors": [str(e)]}), 500


@processing_bp.route("/<int:image_id>/convert", methods=["POST"])
@jwt_required()
def convert_image(image_id):
    """Convert image to a different format."""
    user_id = int(get_jwt_identity())
    image = Image.query.filter_by(id=image_id, user_id=user_id).first()
    if image is None:
        return jsonify({"errors": ["Image not found."]}), 404

    data = request.get_json() or {}
    target_format = data.get("format", "").lower()
    if target_format not in SUPPORTED_FORMATS:
        return jsonify({
            "errors": [f"Unsupported format '{target_format}'."],
            "supported_formats": list(SUPPORTED_FORMATS),
        }), 400

    try:
        with PILImage.open(image.storage_path) as img:
            img = convert_format(img, target_format)

            upload_folder = current_app.config["UPLOAD_FOLDER"]
            pil_format = "JPEG" if target_format in ("jpg", "jpeg") else target_format.upper()
            unique_name = f"{uuid.uuid4().hex}.{target_format}"
            storage_path = os.path.join(upload_folder, unique_name)

            img.save(storage_path, format=pil_format)

        file_size = os.path.getsize(storage_path)
        base_name = image.original_filename.rsplit(".", 1)[0]
        mime_type = f"image/{'jpeg' if target_format in ('jpg', 'jpeg') else target_format}"

        with PILImage.open(storage_path) as saved_img:
            w, h = saved_img.size

        new_image = Image(
            user_id=user_id,
            original_filename=f"{base_name}.{target_format}",
            storage_path=storage_path,
            file_size=file_size,
            mime_type=mime_type,
            width=w,
            height=h,
            parent_id=image.id,
            processing_info=f"convert_to_{target_format}",
        )
        db.session.add(new_image)
        db.session.commit()

        return jsonify({"image": new_image.to_dict()}), 201

    except Exception as e:
        current_app.logger.error(f"Conversion error: {e}")
        return jsonify({"errors": [str(e)]}), 500
