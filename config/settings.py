"""
إعدادات البوت الأساسية
Bot Basic Settings and Configuration
"""

import os
from typing import List

# إعدادات البوت الأساسية
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN غير محدد في متغيرات البيئة")

# معرفات المديرين
ADMIN_IDS: List[int] = [
    int(admin_id) for admin_id in os.getenv("ADMIN_IDS", "").split(",") 
    if admin_id.strip().isdigit()
]

# إعدادات قاعدة البيانات
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///bot_database.db")

# إعدادات اللعبة
GAME_SETTINGS = {
    "initial_balance": 1000,  # الرصيد الأولي للاعبين الجدد
    "daily_bonus": 100,       # المكافأة اليومية
    "max_theft_amount": 500,  # الحد الأقصى للسرقة
    "investment_min": 100,    # الحد الأدنى للاستثمار
    "bank_interest_rate": 0.05,  # معدل فائدة البنك
}

# إعدادات الدفع
PAYMENT_SETTINGS = {
    "provider_token": os.getenv("PAYMENT_PROVIDER_TOKEN", ""),
    "currency": "USD",
    "webhook_url": os.getenv("PAYMENT_WEBHOOK_URL", ""),
}

# إعدادات API الخارجية
API_SETTINGS = {
    "stocks_api_key": os.getenv("STOCKS_API_KEY", ""),
    "crypto_api_key": os.getenv("CRYPTO_API_KEY", ""),
}

# إعدادات التسجيل
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "bot.log")

# إعدادات الكاش
CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))  # 5 دقائق افتراضياً

# رسائل النظام
SYSTEM_MESSAGES = {
    "welcome": "🎮 مرحباً بك في بوت الألعاب الاقتصادية!\n\nاستخدم /help لعرض الأوامر المتاحة.",
    "help": """
🎮 **أوامر البوت المتاحة:**

💰 **الاقتصاد:**
/balance - عرض رصيدك
/daily - المكافأة اليومية
/transfer - تحويل أموال

🏦 **البنوك:**
/bank - إدارة البنك
/deposit - إيداع أموال
/withdraw - سحب أموال

🏠 **العقارات:**
/property - إدارة العقارات
/buy_property - شراء عقار
/sell_property - بيع عقار

🔓 **السرقة:**
/steal - سرقة لاعب آخر
/security - تحسين الأمان

📈 **الأسهم والاستثمار:**
/stocks - عرض الأسهم
/invest - استثمار
/portfolio - محفظة الاستثمارات

🏆 **الترتيب:**
/ranking - عرض الترتيب
/leaderboard - قائمة المتصدرين

🌾 **المزرعة:**
/farm - إدارة المزرعة
/plant - زراعة المحاصيل
/harvest - حصاد المحاصيل

🏰 **القلعة:**
/castle - إدارة القلعة
/upgrade - ترقية المباني
/defend - الدفاع عن القلعة

⚙️ **الإدارة (للمديرين فقط):**
/admin - لوحة تحكم الإدارة
/stats - إحصائيات البوت
/broadcast - رسالة جماعية
""",
    "unauthorized": "❌ غير مصرح لك بتنفيذ هذا الأمر.",
    "error": "❌ حدث خطأ، يرجى المحاولة مرة أخرى لاحقاً.",
    "maintenance": "🔧 البوت تحت الصيانة، يرجى المحاولة لاحقاً.",
}
