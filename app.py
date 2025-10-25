"""
Food Advisor – Streamlit app using Gemini 2.5 Pro model (text + image input)
Improved for stable image upload, clean JSON parsing, and Gemini 2.5 Pro compatibility.
"""

import os
from dotenv import load_dotenv
import streamlit as st
from PIL import Image
import io
import json

# ------------------- Load API key -------------------
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    st.error("Please set GOOGLE_API_KEY in .env file.")
    raise RuntimeError("Missing GOOGLE_API_KEY")

# ------------------- Import Gemini SDK -------------------
try:
    import google.generativeai as genai
except ImportError:
    st.error("Please install `google-generativeai` package (pip install google-generativeai).")
    raise

genai.configure(api_key=GOOGLE_API_KEY)


# ------------------- Helper: Build Prompt -------------------
def build_prompt(dish_name: str, extra_user_info: dict):
    user_context = (
        f"User: {extra_user_info.get('age','?')} yrs, "
        f"{extra_user_info.get('gender','unspecified')}, "
        f"height {extra_user_info.get('height_cm','?')} cm, "
        f"weight {extra_user_info.get('weight_kg','?')} kg, "
        f"activity: {extra_user_info.get('activity_level','unspecified')}, "
        f"dietary_preferences: {extra_user_info.get('dietary_pref','none')}, "
        f"allergies: {extra_user_info.get('allergies','none')}."
    )

    prompt = f"""
You are a nutrition expert. Analyze the dish "{dish_name}" and return **valid JSON only**.

The JSON must follow exactly this format:
{{
  "dish_name": string,
  "ingredients": [string],
  "estimated_serving_g": number,
  "calories_kcal": number,
  "macros": {{
    "carbs_g": number,
    "protein_g": number,
    "fat_g": number,
    "fiber_g": number
  }},
  "micros": {{
    "vitamin_a_ug": number,
    "vitamin_c_mg": number,
    "calcium_mg": number,
    "iron_mg": number,
    "sodium_mg": number
  }},
  "allergens": [string],
  "confidence": {{
    "overall": number,
    "calories": number,
    "ingredients": number
  }},
  "portion_recommendation": {{
    "amount_g": number,
    "frequency": string
  }},
  "healthiness_verdict": {{
    "rating": string,
    "explanation": string
  }},
  "advice": [string]
}}

User context:
{user_context}

Dish context: include nutrition, portion, allergens, and health advice.
Return only valid JSON — no markdown, no code fences, no explanation outside JSON.
"""
    return prompt.strip()


# ------------------- Helper: Safe Image Prep -------------------
def prepare_image(uploaded_file):
    try:
        image = Image.open(uploaded_file).convert("RGB")
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        image_bytes = buf.getvalue()
        return {"mime_type": "image/png", "data": image_bytes}
    except Exception as e:
        st.warning(f"⚠️ Could not process image: {e}")
        return None


# ------------------- Helper: Call Gemini -------------------
def call_gemini(prompt, image_part=None):
    model = genai.GenerativeModel("gemini-2.5-pro")
    inputs = [prompt]
    if image_part:
        inputs.append(image_part)

    response = model.generate_content(inputs)
    text = getattr(response, "text", str(response))
    return text


# ------------------- Helper: Parse JSON Safely -------------------
def safe_json_parse(raw_text):
    try:
        raw_text = raw_text.strip()
        raw_text = raw_text.replace("```json", "").replace("```", "")
        first = raw_text.find("{")
        last = raw_text.rfind("}")
        if first != -1 and last != -1:
            return json.loads(raw_text[first:last + 1])
        else:
            raise ValueError("JSON structure not found in model output.")
    except Exception as e:
        st.warning(f"⚠️ JSON parsing failed: {e}")
        return None


# ------------------- Streamlit UI -------------------
st.set_page_config(page_title="🍽 Food Advisor", page_icon="🍔", layout="wide")
st.markdown(
    "<style>.big-font { font-size:28px !important; font-weight:700;} .muted { color: #6c757d; }</style>",
    unsafe_allow_html=True
)
st.markdown('<div class="big-font">🍔 Food Advisor </div>', unsafe_allow_html=True)
st.write("Estimate nutrition, macros, vitamins, and health verdict from image or dish name")

with st.sidebar:
    st.header("Your Profile")
    age = st.number_input("Age", 1, 120, 25)
    gender = st.selectbox("Gender", ["unspecified", "male", "female", "other"])
    height_cm = st.number_input("Height (cm)", 50, 250, 170)
    weight_kg = st.number_input("Weight (kg)", 20, 300, 70)
    activity = st.selectbox("Activity level", ["sedentary", "light", "moderate", "active", "very active"])
    diet_pref = st.selectbox("Diet preference", ["none", "vegetarian", "vegan", "pescatarian", "keto", "high-protein", "gluten-free"])
    allergies = st.text_input("Allergies (comma separated)", "")
    st.markdown("---")
    st.caption("⚠️ Estimates only. Consult a dietitian for clinical advice.")

col1, col2 = st.columns([1, 1.4])

with col1:
    st.subheader("Input")
    uploaded_file = st.file_uploader("Upload image (optional)", type=["jpg", "jpeg", "png"])
    st.write("OR")
    dish_name = st.text_input("Dish name", placeholder="e.g., chicken biryani with raita")
    notes = st.text_area("Extra details", height=80)
    analyze = st.button("Analyze")

with col2:
    st.subheader("Preview of the Image")
    if uploaded_file:
        try:
            st.image(uploaded_file, caption="Uploaded image", use_container_width=True)
        except Exception:
            st.warning("⚠️ Could not preview image.")

# ------------------- Run Analysis -------------------
if analyze:
    if not (dish_name or uploaded_file):
        st.warning("Please provide a dish name or upload an image.")
    else:
        user_info = {
            "age": age,
            "gender": gender,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "activity_level": activity,
            "dietary_pref": diet_pref,
            "allergies": allergies
        }

        prompt = build_prompt(dish_name, user_info)
        if notes.strip():
            prompt += f"\nAdditional context: {notes.strip()}"

        image_part = prepare_image(uploaded_file) if uploaded_file else None

        with st.spinner("Analyzing... please wait ⏳"):
            try:
                response_text = call_gemini(prompt, image_part)
                parsed_json = safe_json_parse(response_text)

                if parsed_json:
                    st.subheader("✅ Nutrition Summary (Estimated)")
                    # ------------------- Pretty Display -------------------
                    st.markdown(f"### 🍽️ Dish: **{parsed_json.get('dish_name', 'Unknown')}**")

                    st.markdown("#### 🧂 Ingredients")
                    st.write(", ".join(parsed_json.get("ingredients", [])))

                    col_a, col_b = st.columns(2)

                    with col_a:
                        st.markdown("#### ⚖️ Serving & Calories")
                        st.metric("Estimated Serving", f"{parsed_json.get('estimated_serving_g', 0)} g")
                        st.metric("Calories", f"{parsed_json.get('calories_kcal', 0)} kcal")

                        st.markdown("#### 💪 Macros (per serving)")
                        macros = parsed_json.get("macros", {})
                        for k, v in macros.items():
                            st.write(f"**{k.replace('_g','').capitalize()}**: {v} g")

                    with col_b:
                        st.markdown("#### 🧬 Micronutrients")
                        micros = parsed_json.get("micros", {})
                        for k, v in micros.items():
                            unit = "mg" if "mg" in k else "µg"
                            label = k.replace("_mg","").replace("_ug","").replace("_"," ").capitalize()
                            st.write(f"**{label}**: {v} {unit}")

                    st.markdown("#### ⚠️ Allergens")
                    if parsed_json.get("allergens"):
                        st.warning(", ".join(parsed_json["allergens"]))
                    else:
                        st.write("None")

                    st.markdown("#### 📊 Confidence")
                    conf = parsed_json.get("confidence", {})
                    st.progress(conf.get("overall", 0.0))
                    st.caption(f"Calories confidence: {conf.get('calories',0.0)*100:.0f}% | Ingredients confidence: {conf.get('ingredients',0.0)*100:.0f}%")

                    st.markdown("#### 🕒 Portion Recommendation")
                    portion = parsed_json.get("portion_recommendation", {})
                    st.info(f"**{portion.get('amount_g', '?')} g** — {portion.get('frequency', 'No suggestion')}")

                    st.markdown("#### ❤️ Healthiness Verdict")
                    verdict = parsed_json.get("healthiness_verdict", {})
                    st.success(f"**{verdict.get('rating','-')}** — {verdict.get('explanation','')}")

                    st.markdown("#### 💡 Advice")
                    for tip in parsed_json.get("advice", []):
                        st.write(f"- {tip}")


                    verdict = parsed_json.get("healthiness_verdict", {})
                    if verdict:
                        st.info(f"**Verdict: {verdict.get('rating','—').upper()}** — {verdict.get('explanation','')}")

                else:
                    st.warning("Could not parse JSON. Displaying full output:")
                    st.write(response_text)

            except Exception as e:
                st.error(f"❌ Error: {e}")

st.markdown("---")
st.caption("Model-based estimates only — verify with trusted nutrition.")
