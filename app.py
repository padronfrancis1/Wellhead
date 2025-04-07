import streamlit as st
import re
import requests
from PIL import Image, ImageEnhance
from io import BytesIO
from fitz import open as pdf_open

# Flexible tag pattern (e.g., WH-0601-PG-89-FSL32)
# TAG_PATTERN = r"WH[-_]\d{3,5}([-_][A-Z0-9]+){1,4}"
TAG_PATTERN = r"WH[-_]\d{3,5}[-_][A-Z0-9]{2}[-_]\d{2}[-_](?:FSL|CSL)\d{2}"


# OCR.space API key
OCR_SPACE_API_KEY = "K85818381288957"  # Replace with your own if needed

# Preprocess image before OCR
def preprocess_for_ocr(image: Image.Image):
    image = image.convert("L")  # Convert to grayscale
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(2.0)  # Boost contrast

# Extract matching tags
def extract_tags_from_ocr_text(text):
    tags = re.findall(TAG_PATTERN, text)
    return [tag for tag in tags if "FSL" in tag or "CSL" in tag]

# Send image to OCR.space
def ocr_space_file(file):
    result = requests.post(
        'https://api.ocr.space/parse/image',
        files={"filename": ("image.png", file, "image/png")},  # Fixed: set name + type
        data={
            "apikey": OCR_SPACE_API_KEY,
            "language": "eng",
            "isOverlayRequired": False,
        },
    )
    return result.json()

# Streamlit UI
st.set_page_config(page_title="OCR Tag Extractor", layout="wide")
st.title("📄 OCR Tag Extractor (WH-XXXX-XX-XX-FSLXX)")

uploaded_file = st.file_uploader("Upload PDF/Image", type=["pdf", "jpg", "jpeg", "png"])

if uploaded_file:
    file_ext = uploaded_file.name.split(".")[-1].lower()

    if file_ext == "pdf":
        doc = pdf_open(stream=uploaded_file.read(), filetype="pdf")
        images = []
        for page in doc:
            pix = page.get_pixmap(dpi=300)  # Higher DPI = better clarity
            img = Image.open(BytesIO(pix.tobytes("png")))
            images.append(img)

        selected_page = st.slider("Select page", 1, len(images), 1)
        image_to_ocr = images[selected_page - 1]

    else:
        image_to_ocr = Image.open(uploaded_file)

    st.image(image_to_ocr, caption="🖼️ Image sent to OCR", use_column_width=True)

    if st.button("🔍 Run OCR"):
        processed_image = preprocess_for_ocr(image_to_ocr)

        buf = BytesIO()
        processed_image.save(buf, format="PNG")
        buf.seek(0)

        result = ocr_space_file(buf)

        # Debug: show full API response
        st.subheader("🧪 Raw OCR JSON")
        st.json(result)

        parsed_text = result.get("ParsedResults", [{}])[0].get("ParsedText", "")
        tags = extract_tags_from_ocr_text(parsed_text)

        st.subheader("🔍 Extracted Tags")
        st.write(tags if tags else "No matching tags found.")

        with st.expander("📝 Raw OCR Text"):
            st.text(parsed_text)
