"""
ImageLab — Image Processing Service
Provides image manipulation functions using Pillow and OpenCV.
"""
import cv2
import numpy as np
from PIL import Image, ImageFilter, ExifTags

def extract_exif(img: Image.Image) -> dict:
    """Extract EXIF data and parse to a JSON-serializable dictionary."""
    metadata = {}
    exif_data = img.getexif()
    if not exif_data:
        return {}
        
    # Merge IFD0
    for tag_id, value in exif_data.items():
        tag = ExifTags.TAGS.get(tag_id, tag_id)
        metadata[str(tag)] = value
        
    # ExifIFD
    try:
        exif_ifd = exif_data.get_ifd(0x8769)
        for tag_id, value in exif_ifd.items():
            tag = ExifTags.TAGS.get(tag_id, tag_id)
            metadata[str(tag)] = value
    except Exception:
        pass

    # GPSIFD
    try:
        gps_ifd = exif_data.get_ifd(0x8825)
        for tag_id, value in gps_ifd.items():
            tag = ExifTags.GPSTAGS.get(tag_id, tag_id)
            metadata[f'GPS_{tag}'] = value
    except Exception:
        pass
        
    # Clean up values
    for tag, value in metadata.items():
        if isinstance(value, bytes):
            try:
                metadata[tag] = value.decode('utf-8', errors='replace').replace('\x00', '').strip()
            except:
                metadata[tag] = str(value)
        elif hasattr(value, 'numerator'):
            metadata[tag] = float(value)
        elif isinstance(value, (tuple, list)):
            clean_val = []
            for item in value:
                if isinstance(item, bytes):
                    try:
                        clean_item = item.decode('utf-8', errors='replace').replace('\x00', '').strip()
                    except:
                        clean_item = str(item)
                    clean_val.append(clean_item)
                elif hasattr(item, 'numerator'):
                    clean_val.append(float(item))
                else:
                    clean_val.append(item)
            metadata[tag] = clean_val
        elif not isinstance(value, (int, float, str, list, tuple)):
            metadata[tag] = str(value)
            
    return metadata

def strip_metadata(img: Image.Image) -> Image.Image:
    """Strip all EXIF/ICC profiles by copying pixel data into a new Image."""
    data = np.array(img)
    return Image.fromarray(data)


def histogram_equalize(img: Image.Image) -> Image.Image:
    """Apply histogram equalization to improve contrast."""
    cv_img = np.array(img)

    if len(cv_img.shape) == 2:
        # Grayscale
        eq = cv2.equalizeHist(cv_img)
    else:
        # Color — convert to YCrCb, equalize Y channel
        ycrcb = cv2.cvtColor(cv_img, cv2.COLOR_RGB2YCrCb)
        ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
        eq = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2RGB)

    return Image.fromarray(eq)


def reduce_noise(img: Image.Image, strength: int = 10) -> Image.Image:
    """Apply non-local means denoising."""
    cv_img = np.array(img)

    if len(cv_img.shape) == 2:
        denoised = cv2.fastNlMeansDenoising(cv_img, None, strength, 7, 21)
    else:
        denoised = cv2.fastNlMeansDenoisingColored(cv_img, None, strength, strength, 7, 21)

    return Image.fromarray(denoised)


def apply_blur(img: Image.Image, radius: int = 2) -> Image.Image:
    """Apply Gaussian blur."""
    return img.filter(ImageFilter.GaussianBlur(radius=radius))


def apply_sharpen(img: Image.Image) -> Image.Image:
    """Apply sharpening filter."""
    return img.filter(ImageFilter.SHARPEN)


def apply_edge_detection(img: Image.Image) -> Image.Image:
    """Detect edges using Canny algorithm."""
    cv_img = np.array(img.convert("L"))
    edges = cv2.Canny(cv_img, 100, 200)
    return Image.fromarray(edges)


def apply_grayscale(img: Image.Image) -> Image.Image:
    """Convert image to grayscale."""
    return img.convert("L")


def apply_sepia(img: Image.Image) -> Image.Image:
    """Apply sepia tone filter."""
    cv_img = np.array(img.convert("RGB"), dtype=np.float64)
    sepia_filter = np.array([
        [0.272, 0.534, 0.131],
        [0.349, 0.686, 0.168],
        [0.393, 0.769, 0.189],
    ])
    sepia = cv_img @ sepia_filter.T
    sepia = np.clip(sepia, 0, 255).astype(np.uint8)
    return Image.fromarray(sepia)


def apply_invert(img: Image.Image) -> Image.Image:
    """Invert image colors."""
    cv_img = np.array(img)
    inverted = cv2.bitwise_not(cv_img)
    return Image.fromarray(inverted)


def apply_resize(img: Image.Image, width: int = None, height: int = None) -> Image.Image:
    """Resize image to given dimensions. Maintains aspect ratio if only one dimension given."""
    orig_w, orig_h = img.size

    if width and height:
        new_size = (int(width), int(height))
    elif width:
        ratio = int(width) / orig_w
        new_size = (int(width), int(orig_h * ratio))
    elif height:
        ratio = int(height) / orig_h
        new_size = (int(orig_w * ratio), int(height))
    else:
        return img

    return img.resize(new_size, Image.LANCZOS)


def apply_crop(img: Image.Image, x: int = 0, y: int = 0, width: int = None, height: int = None) -> Image.Image:
    """Crop image to the specified rectangle (x, y, width, height)."""
    orig_w, orig_h = img.size
    x, y = int(x), int(y)
    w = int(width) if width else orig_w - x
    h = int(height) if height else orig_h - y

    # Clamp to image boundaries
    x = max(0, min(x, orig_w - 1))
    y = max(0, min(y, orig_h - 1))
    x2 = max(x + 1, min(x + w, orig_w))
    y2 = max(y + 1, min(y + h, orig_h))

    return img.crop((x, y, x2, y2))


def apply_rotate(img: Image.Image, angle: float = 90) -> Image.Image:
    """Rotate image by the given angle (degrees, counter-clockwise). Expands canvas to fit."""
    angle = float(angle)
    return img.rotate(angle, expand=True, resample=Image.BICUBIC)


def compress_image(img: Image.Image, quality: int = 75) -> dict:
    """Return save kwargs for JPEG compression. Used by the route layer."""
    quality = max(1, min(100, int(quality)))
    # Ensure JPEG-compatible mode
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    return img, {"format": "JPEG", "quality": quality, "optimize": True}


def convert_format(img: Image.Image, target_format: str) -> Image.Image:
    """Prepare image for format conversion (handle mode compatibility)."""
    fmt = target_format.upper()
    if fmt in ("JPEG", "JPG"):
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
    return img




# Registry for easy lookup
OPERATIONS = {
    "histogram_equalization": histogram_equalize,
    "noise_reduction": reduce_noise,
    "blur": apply_blur,
    "sharpen": apply_sharpen,
    "edge_detection": apply_edge_detection,
    "grayscale": apply_grayscale,
    "sepia": apply_sepia,
    "invert": apply_invert,
    "resize": apply_resize,
    "crop": apply_crop,
    "rotate": apply_rotate,
}

SUPPORTED_FORMATS = {"png", "jpg", "jpeg", "webp", "bmp", "tiff"}
