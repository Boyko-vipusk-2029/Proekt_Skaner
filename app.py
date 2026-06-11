import streamlit as st
import pytesseract
import re
from PIL import Image

st.set_page_config(page_title="🛡️ Скенер за съставки", layout="centered")

INGREDIENT_DATABASE = {
    # === E-NUMBERS found on this label ===
    "E202": "Калиев сорбат - консервант, може да причини алергични реакции при чувствителни хора.",
    "E282": "Калциев пропионат - консервант, свързан с поведенчески проблеми при деца в някои изследвания.",
    "E401": "Натриев алгинат - желиращ агент от водорасли, общо безопасен но може да причини храносмилателен дискомфорт.",
    "E412": "Гума гуар - сгъстител/стабилизатор.",
    "E415": "Ксантанова гума - стабилизатор, може да причини подуване при чувствителни хора.",
    "E471": "Моно- и диглицериди на мастните киселини - емулгатори, преработени мастни производни.",
    "E481": "Натриев стеароил лактилат - емулгатор, преработена хранителна добавка.",
    "E120": "Кармин/Кошенил - силен алерген от насекоми.",
    "E316": "Натриев ериторбат - антиоксидант.",
    "E407A": "Преработени морски водорасли Euchema - стабилизатор.",

    # === KEYWORDS for word-based detection ===
    "МАЛТОДЕКСТРИН": "Малтодекстрин - въглехидрат с много висок гликемичен индекс.",
    "ПАЛМОВО": "Палмово масло/мазнина - съдържа много наситени мазнини; свързано със сърдечно-съдови рискове.",
    "ХИДРОГЕНИРАНИ": "Хидрогенирани мазнини - могат да съдържат транс-мазнини, вредни за сърцето.",
    "ЧАСТИЧНО ХИДРОГЕНИРАНИ": "Частично хидрогенирани масла - основен източник на транс-мазнини.",
    "ЗАХАР": "Захар - висок гликемичен индекс; прекомерната употреба води до затлъстяване и диабет тип 2.",
    "ГЛУТАМАТ": "Мононатриев глутамат (MSG) - овкусител, може да причини главоболие при чувствителни хора.",
    "МОДИФИЦИРАНО НИШЕСТЕ": "Модифицирано нишесте - силно преработен въглехидрат с висок гликемичен индекс.",
    "МОДИФИЦИРАН": "Модифицирано нишесте - силно преработен въглехидрат.",
    "КАКАО НА ПРАХ": "Какао на прах - само 1.3%; нискорискова съставка в това количество.",
    "СУХО ОБЕЗМАСЛЕНО МЛЯКО": "Сухо обезмаслено мляко - преработен млечен продукт; алерген за непоносими към лактоза.",
    "ЯЙЧЕН ПРАХ": "Яйчен прах - преработен алерген; по-малко хранителна стойност от пресни яйца.",
    "РАСТИТЕЛНА МАЗНИНА": "Растителни мазнини - могат да съдържат наситени мазнини в зависимост от произхода.",
    "СОЛ": "Сол - високото съдържание на натрий е свързано с повишено кръвно налягане.",
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


# ─── Severity helper ───────────────────────────────────────────────────────────
HIGH_RISK = {"E282", "ХИДРОГЕНИРАНИ", "ЧАСТИЧНО ХИДРОГЕНИРАНИ", "ПАЛМОВО",
             "ЗАХАР", "МАЛТОДЕКСТРИН", "МОДИФИЦИРАНО НИШЕСТЕ", "МОДИФИЦИРАН"}
MEDIUM_RISK = {"E202", "E471", "E481", "E471", "E412", "E415",
               "РАСТИТЕЛНА МАЗНИНА", "СУХО ОБЕЗМАСЛЕНО МЛЯКО",
               "ЯЙЧЕН ПРАХ", "СОЛ"}


def severity_icon(key):
    if key in HIGH_RISK:
        return "🔴"
    elif key in MEDIUM_RISK:
        return "🟡"
    return "🟢"


# ─── UI ────────────────────────────────────────────────────────────────────────
st.title("🛡️ Професионален скенер за етикети")
st.caption("Качете снимка на съставките — приложението открива потенциално вредни вещества.")

try:
    pytesseract.get_tesseract_version()
except pytesseract.TesseractNotFoundError:
    st.error(
        "❌ Tesseract не е инсталиран на сървъра.\n\n"
        "Моля, добавете файл `packages.txt` в корена на GitHub репото си със съдържание:\n\n"
        "```\ntesseract-ocr\ntesseract-ocr-bul\ntesseract-ocr-eng\n```\n\n"
        "След това направете redeploy на приложението."
    )
    st.stop()

uploaded_file = st.file_uploader("Качете снимка на етикета...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, use_container_width=True)

    with st.spinner("Анализирам всяка дума..."):
        try:
            raw_text = pytesseract.image_to_string(image, lang="bul+eng")
        except pytesseract.TesseractError:
            raw_text = pytesseract.image_to_string(image, lang="eng")

        found, debug_text = process_text_and_find_ingredients(raw_text)

        with st.expander("Виж разпознатия текст (пречистен)"):
            st.write(debug_text)

        st.divider()

        if found:
            high = {k: v for k, v in found.items() if k in HIGH_RISK}
            medium = {k: v for k, v in found.items() if k in MEDIUM_RISK}
            other = {k: v for k, v in found.items() if k not in HIGH_RISK and k not in MEDIUM_RISK}

            st.warning(f"⚠️ Открити са **{len(found)}** потенциално нежелани съставки:")

            if high:
                st.error("🔴 Висок риск")
                for item, desc in high.items():
                    st.write(f"- **{item}**: {desc}")

            if medium:
                st.warning("🟡 Умерен риск")
                for item, desc in medium.items():
                    st.write(f"- **{item}**: {desc}")

            if other:
                st.info("🟢 Нисък / информационен риск")
                for item, desc in other.items():
                    st.write(f"- **{item}**: {desc}")
        else:
            st.success("✅ Не бяха открити критични съставки.")
