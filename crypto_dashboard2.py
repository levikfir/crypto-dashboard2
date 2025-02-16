import streamlit as st
import pandas as pd
import requests
import io
import time

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

# טעינת הנתונים מגוגל שיטס
sheet_id = "1d71M2zrAM8ju1dKuGnWYEavIABYT30_4"
sheet_name = "חישובים"
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

def load_data():
    try:
        response = requests.get(url)
        response.encoding = "utf-8"
        data = response.text
        df = pd.read_csv(io.StringIO(data), skip_blank_lines=True)
        df.columns = df.iloc[0]  # הפיכת השורה הראשונה לכותרות
        df = df[1:].reset_index(drop=True)
        df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')  # הסרת עמודות ושורות ריקות
        for col in df.columns[1:]:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except Exception as e:
        st.error(f"❌ שגיאה בטעינת הנתונים מגוגל שיטס: {e}")
        st.stop()

df = load_data()

# הגדרת מבנה הדאשבורד
st.set_page_config(page_title="Crypto Dashboard", layout="wide")
st.title("📊 טבלת מחירים והתראות")

# הוספת עמודה ידנית של מחיר יעד
if "מחיר יעד" not in df.columns:
    df["מחיר יעד"] = None

# קבלת מחירי שוק
df["מחיר שוק"] = df.iloc[:, 0].apply(lambda x: get_crypto_price(str(x).lower()))

# בדיקת התראות אם מחיר השוק בטווח 10% ממחיר היעד
def check_alerts(row):
    if pd.notna(row["מחיר שוק"]) and pd.notna(row["מחיר יעד"]):
        threshold = row["מחיר יעד"] * 0.9
        if row["מחיר שוק"] >= threshold:
            return "🔔 התראה: קרוב למחיר היעד!"
    return ""

df["התראה"] = df.apply(check_alerts, axis=1)

# הצגת הטבלה
st.dataframe(df[[df.columns[0], "מחיר שוק", "מחיר יעד", "התראה"]], use_container_width=True)
