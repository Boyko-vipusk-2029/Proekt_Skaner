import streamlit as st
import pytesseract
import re
import numpy as np
from PIL import Image
 
st.set_page_config(page_title="🛡️ Скенер за съставки", layout="centered")
 
INGREDIENT_DATABASE = {
    "E120": "Кармин/Кошенил - силен алерген от насекоми.",
    "E316": "Натриев ериторбат - антиоксидант.",
    "E407A": "Преработени морски водорасли Euchema - стабилизатор.",
    "E412": "Гума гуар - сгъстител.",
    "МАЛТОДЕКСТРИН": "Малтодекстрин - въглехидрат с много висок гликемичен индекс.",
    "ПАЛМОВО": "Палмово масло/мазнина - високо съдържание на наситени мазнини.",
    "ХИДРОГЕНИРАНИ": "Хидрогенирани мазнини - източник на транс-мазнини.",
    "ЗАХАР": "Внимание: Съдържа захар.",
    "ГЛУТАМАТ": "Мононатриев глутамат - овкусител.",
}
 
def normalize_to_cyrillic(text):
    caps = {
        'A': 'А', 'B': 'В', 'E': 'Е', 'K': 'К', 'M': 'М', 'H': 'Н',
        'O': 'О', 'P': 'Р', 'C': 'С', 'T': 'Т', 'X': 'Х', 'Y': 'У'
    }
    for lat, cyr in caps.items():
        text = text.replace(lat, cyr)
    return text
 
def process_text_and_find_ingredients(raw_text):
    raw_text = raw_text.upper()
    text_for_e = raw_text.replace("Е", "E").replace("€", "E").replace("I", "1").replace("O", "0")
    text_for_words = normalize_to_cyrillic(raw_text)
    text_no_spaces = text_for_words.replace(" ", "")
 
    found_results = {}
 
    e_pattern = re.compile(r'E\s*(\d+)([A-ZА-Я]?)')
    for match in e_pattern.findall(text_for_e):
        code = "E" + match[0] + match[1]
        if code in INGREDIENT_DATABASE:
            found_results[code] = INGREDIENT_DATABASE[code]
 
    for key, desc in INGREDIENT_DATABASE.items():
        if not key.startswith("E"):
            if key in text_for_words or key in text_no_spaces:
                found_results[key] = desc
 
    return found_results, text_for_words
 
st.title("🛡️ Професионален скенер за етикети")
 
uploaded_file = st.file_uploader("Качете снимка на етикета...", type=["jpg", "jpeg", "png"])
 
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, use_container_width=True)
 
    with st.spinner('Анализирам всяка дума...'):
        raw_text = pytesseract.image_to_string(image, lang='bul+eng')
        found, debug_text = process_text_and_find_ingredients(raw_text)
 
        with st.expander("Виж разпознатия текст (пречистен)"):
            st.write(debug_text)
 
        st.divider()
 
        if found:
            st.warning("⚠️ Открити съставки:")
            for item, desc in found.items():
                st.write(f"- **{item}**: {desc}")
        else:
            st.success("✅ Не бяха открити критични съставки.")
