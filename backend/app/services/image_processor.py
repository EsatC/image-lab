"""
ImageLab — Image Processing Service
Provides image manipulation functions using Pillow and OpenCV.
"""
import cv2
import numpy as np
from PIL import Image, ImageFilter


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
}

SUPPORTED_FORMATS = {"png", "jpg", "jpeg", "webp", "bmp", "tiff"}
