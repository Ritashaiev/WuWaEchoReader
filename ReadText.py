import os
import cv2
import numpy as np
import pytesseract


pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


DEBUG_FOLDER = "Debug"


def group_active_lines(active_y, min_height=8):
    boundaries = []
    in_bar = False
    start_y = 0

    for y, active in enumerate(active_y):
        if active and not in_bar:
            start_y = y
            in_bar = True

        elif not active and in_bar:
            end_y = y
            in_bar = False

            if end_y - start_y >= min_height:
                boundaries.append((start_y, end_y))

    if in_bar:
        end_y = len(active_y) - 1
        if end_y - start_y >= min_height:
            boundaries.append((start_y, end_y))

    return boundaries


def find_highlight_bar_boundaries(img):
    height, width = img.shape[:2]

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    x1 = int(width * 0.07)
    x2 = int(width * 0.95)

    active_y = []

    for y in range(height):
        line = hsv[y, x1:x2, :]

        v = line[:, 2]

        # Remove white text pixels
        non_text_pixels = line[v < 180]

        if len(non_text_pixels) < 20:
            active_y.append(False)
            continue

        median_h = np.median(non_text_pixels[:, 0])
        median_s = np.median(non_text_pixels[:, 1])
        median_v = np.median(non_text_pixels[:, 2])

        # Highlight bar: light yellow / grey
        is_highlight = (
            45 <= median_h <= 105 and
            median_s <= 55 and
            60 <= median_v <= 140
        )

        active_y.append(is_highlight)

    return group_active_lines(active_y, min_height=10)


def preprocess_row_for_ocr(row_img):
    gray = cv2.cvtColor(row_img, cv2.COLOR_BGR2GRAY)

    gray = cv2.resize(
        gray,
        None,
        fx=3,
        fy=3,
        interpolation=cv2.INTER_CUBIC
    )

    _, thresh = cv2.threshold(
        gray,
        150,
        255,
        cv2.THRESH_BINARY
    )

    return thresh


def read_row_text(row_img):
    processed = preprocess_row_for_ocr(row_img)

    config = "--psm 7"

    text = pytesseract.image_to_string(
        processed,
        config=config
    )

    return text.strip()


def read_highlighted_substats(image_path: str):
    """
    Input:
        cropped stat panel image

    Output:
        list[str], for example:
        [
            "+ Crit. Rate 7.5%",
            "+ Crit. DMG 15.0%"
        ]
    """
    img = cv2.imread(image_path)

    if img is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")

    os.makedirs(DEBUG_FOLDER, exist_ok=True)

    height, width = img.shape[:2]

    boundaries = find_highlight_bar_boundaries(img)

    # Ignore main stat and fixed class/type rows.
    # For your 384x360 crop, useful substats begin around y=160.
    substat_start_y = 160

    substat_boundaries = [
        (y1, y2)
        for (y1, y2) in boundaries
        if y1 >= substat_start_y
    ]

    debug_img = img.copy()
    ocr_lines = []

    for i, (y1, y2) in enumerate(substat_boundaries, start=1):
        pad = 0

        crop_y1 = max(0, y1 - pad)
        crop_y2 = min(height, y2 + pad)

        row = img[crop_y1:crop_y2, :]

        row_file = os.path.join(DEBUG_FOLDER, f"ocr_substat_row_{i}.png")
        cv2.imwrite(row_file, row)

        text = read_row_text(row)

        if text:
            ocr_lines.append(text)

        cv2.rectangle(
            debug_img,
            (0, crop_y1),
            (width - 1, crop_y2),
            (0, 0, 255),
            1
        )

    debug_path = os.path.join(DEBUG_FOLDER, "debug_ocr_substat_rows.png")
    cv2.imwrite(debug_path, debug_img)

    return ocr_lines