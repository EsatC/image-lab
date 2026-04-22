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
from app.services.image_processor import OPERATIONS, SUPPORTED_FORMATS, convert_format, compress_image

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


@processing_bp.route("/<int:image_id>/compress", methods=["POST"])
@jwt_required()
def compress_image_route(image_id):
    """Compress image as JPEG with adjustable quality."""
    user_id = int(get_jwt_identity())
    image = Image.query.filter_by(id=image_id, user_id=user_id).first()
    if image is None:
        return jsonify({"errors": ["Image not found."]}), 404

    data = request.get_json() or {}
    quality = data.get("quality", 75)

    try:
        quality = max(1, min(100, int(quality)))
    except (ValueError, TypeError):
        return jsonify({"errors": ["Quality must be an integer between 1 and 100."]}), 400

    try:
        with PILImage.open(image.storage_path) as img:
            img = img.convert("RGB") if img.mode not in ("RGB", "L") else img
            compressed, save_kwargs = compress_image(img, quality=quality)

            upload_folder = current_app.config["UPLOAD_FOLDER"]
            unique_name = f"{uuid.uuid4().hex}.jpg"
            storage_path = os.path.join(upload_folder, unique_name)

            compressed.save(storage_path, **save_kwargs)

        file_size = os.path.getsize(storage_path)
        w, h = compressed.size

        base_name = image.original_filename.rsplit(".", 1)[0]
        new_image = Image(
            user_id=user_id,
            original_filename=f"{base_name}_compressed.jpg",
            storage_path=storage_path,
            file_size=file_size,
            mime_type="image/jpeg",
            width=w,
            height=h,
            parent_id=image.id,
            processing_info=f"compress_q{quality}",
        )
        db.session.add(new_image)
        db.session.commit()

        return jsonify({"image": new_image.to_dict()}), 201

    except Exception as e:
        current_app.logger.error(f"Compression error: {e}")
        return jsonify({"errors": [str(e)]}), 500


@processing_bp.route("/<int:image_id>/pipeline", methods=["POST"])
@jwt_required()
def pipeline_image(image_id):
    """Apply a sequence of operations."""
    user_id = int(get_jwt_identity())
    image = Image.query.filter_by(id=image_id, user_id=user_id).first()
    if image is None:
        return jsonify({"errors": ["Image not found."]}), 404

    data = request.get_json() or {}
    pipeline = data.get("pipeline", [])

    if not isinstance(pipeline, list) or not pipeline:
        return jsonify({"errors": ["Pipeline must be a non-empty list of operations."]}), 400

    for step in pipeline:
        if step.get("operation") not in OPERATIONS:
            return jsonify({
                "errors": [f"Unknown operation '{step.get('operation')}'."],
                "available_operations": list(OPERATIONS.keys()),
            }), 400

    try:
        with PILImage.open(image.storage_path) as img:
            img = img.convert("RGB") if img.mode not in ("RGB", "L") else img
            
            # Chain the operations
            for step in pipeline:
                operation = step.get("operation")
                params = step.get("params", {})
                
                fn = OPERATIONS[operation]
                import inspect
                sig = inspect.signature(fn)
                if len(sig.parameters) > 1:
                    img = fn(img, **params)
                else:
                    img = fn(img)

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

            if img.mode == "L" and pil_format == "JPEG":
                img.save(storage_path, format=pil_format)
            else:
                img.save(storage_path, format=pil_format)

        file_size = os.path.getsize(storage_path)
        w, h = img.size

        new_image = Image(
            user_id=user_id,
            original_filename=f"pipeline_{image.original_filename}",
            storage_path=storage_path,
            file_size=file_size,
            mime_type=image.mime_type,
            width=w,
            height=h,
            parent_id=image.id,
            processing_info="pipeline",
        )
        db.session.add(new_image)
        db.session.commit()

        return jsonify({"image": new_image.to_dict()}), 201

    except Exception as e:
        current_app.logger.error(f"Pipeline error: {e}")
        return jsonify({"errors": [str(e)]}), 500

@processing_bp.route("/<int:image_id>/metadata", methods=["GET"])
@jwt_required()
def get_metadata(image_id):
    """Retrieve EXIF metadata for the given image."""
    user_id = int(get_jwt_identity())
    image = Image.query.filter_by(id=image_id, user_id=user_id).first()
    if image is None:
        return jsonify({"errors": ["Image not found."]}), 404

    try:
        from app.services.image_processor import extract_exif
        with PILImage.open(image.storage_path) as img:
            metadata = extract_exif(img)
            
        return jsonify({"metadata": metadata}), 200
    except Exception as e:
        current_app.logger.error(f"Metadata read error: {e}")
        return jsonify({"errors": [str(e)]}), 500


@processing_bp.route("/<int:image_id>/remove_metadata", methods=["POST"])
@jwt_required()
def remove_metadata(image_id):
    """Strip all metadata and create a clean duplicate."""
    user_id = int(get_jwt_identity())
    image = Image.query.filter_by(id=image_id, user_id=user_id).first()
    if image is None:
        return jsonify({"errors": ["Image not found."]}), 404

    try:
        from app.services.image_processor import strip_metadata
        with PILImage.open(image.storage_path) as img:
            img = img.convert("RGB") if img.mode not in ("RGB", "L", "RGBA") else img
            clean_img = strip_metadata(img)

        upload_folder = current_app.config["UPLOAD_FOLDER"]
        ext = image.original_filename.rsplit(".", 1)[-1].lower()
        if ext in ("jpg", "jpeg"):
            save_ext = "jpg"
            pil_format = "JPEG"
        elif ext == "png":
            save_ext = "png"
            pil_format = "PNG"
        else:
            save_ext = ext
            pil_format = ext.upper()

        unique_name = f"{uuid.uuid4().hex}.{save_ext}"
        storage_path = os.path.join(upload_folder, unique_name)

        clean_img.save(storage_path, format=pil_format)

        file_size = os.path.getsize(storage_path)
        w, h = clean_img.size

        base_name = image.original_filename.rsplit(".", 1)[0]
        new_image = Image(
            user_id=user_id,
            original_filename=f"{base_name}_clean.{save_ext}",
            storage_path=storage_path,
            file_size=file_size,
            mime_type=image.mime_type,
            width=w,
            height=h,
            parent_id=image.id,
            processing_info="metadata_removed",
        )
        db.session.add(new_image)
        db.session.commit()

        return jsonify({"image": new_image.to_dict()}), 201

    except Exception as e:
        current_app.logger.error(f"Metadata strip error: {e}")
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
