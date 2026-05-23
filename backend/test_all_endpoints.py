"""Final integration test for all processing endpoints including metadata."""
import os
os.environ.setdefault("FLASK_ENV", "development")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-long!!")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-32-chars-l!")

from app import create_app, db
from app.models import User, Image
from PIL import Image as PILImage
from PIL.ExifTags import Base as ExifBase

app = create_app()

PASS = 0
FAIL = 0

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} — {detail}")

with app.app_context():
    db.drop_all()
    db.create_all()
    
    user = User(username="testuser", email="test@test.com")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    
    upload_folder = app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)
    
    # Create test image WITH EXIF
    test_img = PILImage.new("RGB", (200, 200), color=(128, 64, 32))
    exif = test_img.getexif()
    exif[ExifBase.Make] = "TestCam"
    exif[ExifBase.Model] = "Model X"
    exif[ExifBase.Software] = "ImageLab"
    test_path = os.path.join(upload_folder, "exif_test.jpg")
    test_img.save(test_path, format="JPEG", exif=exif.tobytes())
    
    img_record = Image(
        user_id=user.id, original_filename="photo.jpg",
        storage_path=test_path, file_size=os.path.getsize(test_path),
        mime_type="image/jpeg", width=200, height=200,
    )
    db.session.add(img_record)
    db.session.commit()
    image_id = img_record.id

with app.test_client() as c:
    resp = c.post("/api/auth/login", json={"username": "testuser", "password": "password123"})
    token = resp.get_json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    # ---- Metadata Tools ----
    print("\n📋 METADATA TOOLS")
    
    resp = c.get(f"/api/images/{image_id}/metadata", headers=h)
    check("GET metadata returns 200", resp.status_code == 200, f"got {resp.status_code}")
    meta = resp.get_json().get("metadata", {})
    check("Metadata is not empty", len(meta) > 0, f"got {meta}")
    check("Metadata contains 'Make'", "Make" in meta, f"keys: {list(meta.keys())}")
    check("Make value is 'TestCam'", meta.get("Make") == "TestCam", f"got {meta.get('Make')}")
    
    resp = c.post(f"/api/images/{image_id}/remove_metadata", headers=h, json={})
    check("POST remove_metadata returns 201", resp.status_code == 201, f"got {resp.status_code}")
    clean_img = resp.get_json().get("image", {})
    check("Response has 'image' key", bool(clean_img), f"got {resp.get_json()}")
    check("Clean image has filename", bool(clean_img.get("filename")), f"got {clean_img}")
    check("Clean image has width/height", clean_img.get("width") == 200, f"got {clean_img}")
    
    # Verify metadata is actually stripped
    clean_id = clean_img.get("id")
    if clean_id:
        resp2 = c.get(f"/api/images/{clean_id}/metadata", headers=h)
        clean_meta = resp2.get_json().get("metadata", {})
        check("Stripped image has no EXIF", len(clean_meta) == 0, f"got {clean_meta}")

    # ---- Existing Tools ----
    print("\n🎨 SINGLE OPERATIONS")
    for op in ["grayscale", "sepia", "invert", "sharpen", "blur", "edge_detection",
                "histogram_equalization", "noise_reduction"]:
        resp = c.post(f"/api/images/{image_id}/process", headers=h, json={"operation": op})
        check(f"{op}", resp.status_code == 201, f"got {resp.status_code}: {resp.get_json()}")

    print("\n✂️ TRANSFORM TOOLS")
    resp = c.post(f"/api/images/{image_id}/process", headers=h,
                  json={"operation": "resize", "params": {"width": 100}})
    check("Resize", resp.status_code == 201, f"got {resp.status_code}")
    
    resp = c.post(f"/api/images/{image_id}/process", headers=h,
                  json={"operation": "crop", "params": {"x": 10, "y": 10, "width": 50, "height": 50}})
    check("Crop", resp.status_code == 201, f"got {resp.status_code}")
    
    resp = c.post(f"/api/images/{image_id}/process", headers=h,
                  json={"operation": "rotate", "params": {"angle": 90}})
    check("Rotate", resp.status_code == 201, f"got {resp.status_code}")

    print("\n📦 COMPRESS")
    resp = c.post(f"/api/images/{image_id}/compress", headers=h, json={"quality": 50})
    check("Compress q50", resp.status_code == 201, f"got {resp.status_code}")

    print("\n🔄 FORMAT CONVERSION")
    for fmt in ["png", "webp", "bmp"]:
        resp = c.post(f"/api/images/{image_id}/convert", headers=h, json={"format": fmt})
        check(f"Convert to {fmt}", resp.status_code == 201, f"got {resp.status_code}")

    print("\n🔄 PIPELINE")
    resp = c.post(f"/api/images/{image_id}/pipeline", headers=h, json={
        "pipeline": [
            {"operation": "grayscale"},
            {"operation": "resize", "params": {"width": 50}},
            {"operation": "sharpen"},
        ]
    })
    check("Pipeline (3 steps)", resp.status_code == 201, f"got {resp.status_code}")

print(f"\n{'='*40}")
print(f"Results: {PASS} passed, {FAIL} failed out of {PASS+FAIL} tests")
if FAIL > 0:
    exit(1)
