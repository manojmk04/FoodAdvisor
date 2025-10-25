# 🍽️ FoodAdvisor AI App

**FoodAdvisor AI** is an AI-powered web app built with **Streamlit** and **Google Gemini 2.5 Pro**.  
It analyzes **food images** or **dish names** and provides detailed nutritional insights, including **calories, macronutrients, vitamins, allergens, and personalized eating advice**.

---

## 🚀 Features

- Upload **food images** or enter **dish names**
- Detailed breakdown: **calories, protein, carbs, fats, fiber**
- Key **vitamins and minerals** analysis
- AI-generated **health verdict** and **portion recommendations**
- **Clean, user-friendly Streamlit UI**

---

## 🧠 Powered By

- **Google Gemini 2.5 Pro** (AI reasoning and nutrition analysis)  
- **Streamlit** (web app UI)  
- **Python** (backend and scripting)  

---

## 🛠️ Installation & Run

```bash
# Create and activate a virtual environment

# Windows:
python -m venv venv
venv\Scripts\activate

# macOS/Linux:
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Add your Google API Key in a .env file
GOOGLE_API_KEY=your_api_key_here

# Run the app
streamlit run app.py
