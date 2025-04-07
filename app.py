import streamlit as st
import pytesseract
import cv2
import re
import fitz  # PyMuPDF
from PIL import Image
import numpy as np
from io import BytesIO

# OCR config
CUSTOM_CONFIG = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-'
TAG_PATTERN = r'WH-\d{4}-[A-Z]{2}-\d{2}-FSL\d{2}'

st.set_page_config(page_title="OCR Tag Extractor", layout="wide")
st.title("📄 OCR Tag Extractor (WH-XXXX-XX-XX-FSLXX)")

uploaded_file = st.file_uploader("Upload PDF or Image", type=["pdf", "png", "jpg", "jpeg"])

def preprocess_image(image: Image.Image):
    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                   cv2.THRESH_BINARY_INV, 15, 8)
    return thresh

def extract_tags_with_boxes(image):
    data = pytesseract.image_to_data(image, config=CUSTOM_CONFIG, output_type=pytesseract.Output.DICT)
    boxes = []
    tags = []

    for i in range(len(data["text"])):
        word = data["text"][i]
        if re.fullmatch(TAG_PATTERN, word):
            tags.append(word)
            (x, y, w, h) = (data["left"][i], data["top"][i], data["width"][i], data["height"][i])
            boxes.append((x, y, w, h))

    return tags, boxes, data

def draw_boxes_on_image(image_pil, boxes):
    image_cv = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
    for (x, y, w, h) in boxes:
        cv2.rectangle(image_cv, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return Image.fromarray(cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB))

def pdf_to_images(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    images = []
    for page in doc:
        pix = page.get_pixmap(dpi=200)
        img = Image.open(BytesIO(pix.tobytes("png")))
        images.append(img)
    return images

if uploaded_file:
    file_ext = uploaded_file.name.split('.')[-1].lower()

    if file_ext == 'pdf':
        images = pdf_to_images(uploaded_file)
        total_pages = len(images)
        st.info(f"📄 PDF has {total_pages} page(s).")

        selected_page = st.slider("Select a page", 1, total_pages, 1)
        selected_image = images[selected_page - 1]
        st.image(selected_image, caption=f"Page {selected_page}", use_column_width=True)

        if st.button("🔍 Run OCR on this page"):
            processed_image = preprocess_image(selected_image)
            tags, boxes, _ = extract_tags_with_boxes(processed_image)
            boxed_image = draw_boxes_on_image(selected_image, boxes)

            st.image(boxed_image, caption="📍 Tags Detected", use_column_width=True)

            st.subheader("🔍 Extracted Tags")
            st.write(tags if tags else "No matching tags found.")

    elif file_ext in ['png', 'jpg', 'jpeg']:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)

        if st.button("🔍 Run OCR on this image"):
            processed_image = preprocess_image(image)
            tags, boxes, _ = extract_tags_with_boxes(processed_image)
            boxed_image = draw_boxes_on_image(image, boxes)

            st.image(boxed_image, caption="📍 Tags Detected", use_column_width=True)

            st.subheader("🔍 Extracted Tags")
            st.write(tags if tags else "No matching tags found.")
