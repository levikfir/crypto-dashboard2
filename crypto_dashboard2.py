import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import io
from plyer import notification
import time
from twilio.rest import Client
import os

# התקנת הספריות החסרות
try:
    import plotly.express as px
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "plotly"])
    import plotly.express as px

try:
    import openpyxl
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "openpyxl"])
    import openpyxl

# פונקציה לקבלת מחירי מטבעות בזמן אמת
API_URL = "https://api.coingecko.com/api/v3/simple/price"
def get_crypto_price(symbol, currency="usd"):
    try:
        response = requests.get(API_URL, params={"ids": symbol, "vs_currencies": currency})
        data = response.json()
        return data.get(symbol, {}).get(currency, None)
    except Exception as e:
        st.error(f"שגיאה בשליפת מחירי מטבעות: {e}")
        return None

# טעינת הנתונים מגוגל שיטס עם ניקוי נתונים
sheet_id = "1d71M2zrAM8ju1dKuGnWYEavIABYT30_4"
sheet_name = "חישובים"
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

def load_data():
    try:
        response = requests.get(url)
        response.encoding = "utf-8"
        data = response.text
        df = pd.read_csv(io.StringIO(data), skip_blank_lines=True)

        # הפיכת השורה הראשונה לכותרות אם היא לא נלקחה נכון
        df.columns = df.iloc[0]
        df = df[1:].reset_index(drop=True)

        # הסרת עמודות ושורות ריקות
        df = df.dropna(axis=1, how='all')
        df = df.dropna(axis=0, how='all')

        # המרת עמודות למספרים במידת הצורך
        for col in df.columns[1:]:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        return df
    except Exception as e:
        st.error(f"❌ שגיאה בטעינת הנתונים מגוגל שיטס: {e}")
        st.stop()

df = load_data()

# הגדרת מבנה הדאשבורד
st.set_page_config(page_title="Crypto Dashboard", layout="wide")
st.title("📊 Crypto Investment Dashboard")

# בחירת מטבע לתצוגה
coin_options = df.iloc[:, 0].dropna().astype(str).unique()
selected_coin = st.selectbox("בחר מטבע:", coin_options)

# סינון הנתונים לפי המטבע הנבחר
coin_data = df[df.iloc[:, 0].astype(str) == selected_coin]

# קבלת מחיר השוק בזמן אמת
current_market_price = get_crypto_price(selected_coin.lower())
if current_market_price is not None:
    st.metric(label="💲 מחיר שוק בזמן אמת (USD)", value=f"${current_market_price:,.2f}")

# יצירת גרף רק אם יש נתונים תקינים
df_clean = df.dropna(subset=[df.columns[1]])

if not df_clean.empty and df_clean.shape[1] > 1:
    try:
        fig = px.pie(df_clean, names=df_clean[df_clean.columns[0]].astype(str), values=pd.to_numeric(df_clean.iloc[:, 1], errors='coerce'),
                     title="התפלגות השקעות")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"⚠️ שגיאה ביצירת גרף: {e}")
else:
    st.warning("⚠️ אין מספיק נתונים להצגת גרף התפלגות השקעות.")

# הצגת טבלת נתונים
st.dataframe(df, use_container_width=True)
