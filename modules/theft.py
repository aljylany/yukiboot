"""
وحدة السرقة والأمان
Theft and Security Module
"""

import logging
import random
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.operations import get_user, update_user_balance, execute_query, add_transaction
from utils.states import TheftStates
from utils.helpers import format_number, parse_user_mention
from config.settings import GAME_SETTINGS

# أنواع الحماية وتكاليفها
SECURITY_LEVELS = {
    1: {"name": "أساسي", "protection": 10, "cost": 0, "emoji": "🛡"},
    2: {"name": "متوسط", "protection": 30, "cost": 5000, "emoji": "🛡"},
    3: {"name": "قوي", "protection": 50, "cost": 15000, "emoji": "🛡"},
    4: {"name": "فائق", "protection": 70, "cost": 40000, "emoji": "🛡"},
    5: {"name": "أسطوري", "protection": 90, "cost": 100000, "emoji": "🛡"}
}


async def show_security_menu(message: Message):
    """عرض قائمة الأمان"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        security_level = user.get('security_level', 1)
        security_info = SECURITY_LEVELS[security_level]
        
        # الحصول على إحصائيات السرقة
        theft_stats = await get_theft_stats(message.from_user.id)
        
        security_text = f"""
🛡 **نظام الأمان والسرقة**

🔒 **مستوى الأمان الحالي:**
{security_info['emoji']} {security_info['name']} ({security_level}/5)
🛡 نسبة الحماية: {security_info['protection']}%

💰 **أموالك:**
💵 النقد (قابل للسرقة): {format_number(user['balance'])}$
🏦 البنك (محمي): {format_number(user['bank_balance'])}$

📊 **إحصائيات السرقة:**
✅ سرقات ناجحة: {theft_stats['successful_thefts']}
❌ سرقات فاشلة: {theft_stats['failed_thefts']}
🔒 مرات تم سرقتك: {theft_stats['times_stolen']}

💡 نصيحة: ضع أموالك في البنك لحمايتها!

📝 **الأوامر المتاحة:**
🔓 للسرقة: رد على رسالة الشخص واكتب "سرقة" أو "سرف"
🛡 لترقية الأمان: اكتب "ترقية امان"
📊 لرؤية الإحصائيات: اكتب "احصائيات سرقة"
🏆 لرؤية أفضل اللصوص: اكتب "افضل لصوص"
        """
        
        await message.reply(security_text)
        
    except Exception as e:
        logging.error(f"خطأ في قائمة الأمان: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة الأمان")


async def start_steal(message: Message, state: FSMContext):
    """بدء عملية السرقة"""
    try:
        await state.set_state(TheftStates.waiting_target_user)
        await message.reply(
            "🔓 **سرقة لاعب**\n\n"
            "من تريد أن تسرق؟\n"
            "💡 يمكنك كتابة:\n"
            "- @username\n"
            "- معرف المستخدم (رقم)\n"
            "- الرد على رسالة الشخص\n\n"
            "⚠️ تذكر أن السرقة محفوفة بالمخاطر!\n"
            "❌ اكتب 'إلغاء' للإلغاء"
        )
        
    except Exception as e:
        logging.error(f"خطأ في بدء السرقة: {e}")
        await message.reply("❌ حدث خطأ في عملية السرقة")


async def process_target_user(message: Message, state: FSMContext):
    """معالجة اختيار الهدف للسرقة"""
    try:
        text = message.text.strip()
        
        if text.lower() in ['إلغاء', 'cancel']:
            await state.clear()
            await message.reply("❌ تم إلغاء عملية السرقة")
            return
        
        # استخراج معرف المستخدم
        target_user_id = await parse_user_mention(text, message)
        
        if not target_user_id:
            await message.reply("❌ لم أتمكن من العثور على هذا المستخدم. حاول مرة أخرى.")
            return
        
        if target_user_id == message.from_user.id:
            await message.reply("❌ لا يمكنك سرقة نفسك! 🤔")
            return
        
        # محاولة السرقة
        await attempt_steal(message, target_user_id)
        await state.clear()
        
    except Exception as e:
        logging.error(f"خطأ في معالجة هدف السرقة: {e}")
        await message.reply("❌ حدث خطأ، يرجى المحاولة مرة أخرى")
        await state.clear()


async def attempt_steal(message: Message, target_user_id: int):
    """محاولة سرقة مستخدم"""
    try:
        # الحصول على بيانات كلا المستخدمين
        thief = await get_user(message.from_user.id)
        target = await get_user(target_user_id)
        
        if not target:
            await message.reply("❌ المستخدم المستهدف غير مسجل في البوت")
            return
        
        # التحقق من أن الهدف لديه أموال للسرقة
        if target['balance'] <= 0:
            await message.reply("😅 المستخدم المستهدف لا يملك أموال نقدية للسرقة!")
            return
        
        # حساب احتمالية النجاح
        thief_skill = random.randint(1, 100)
        target_security = SECURITY_LEVELS[target.get('security_level', 1)]['protection']
        
        success_chance = max(10, 80 - target_security)  # احتمالية أساسية مع تعديل حسب الأمان
        
        if thief_skill <= success_chance:
            # السرقة نجحت
            await handle_successful_theft(message, thief, target, target_user_id)
        else:
            # السرقة فشلت
            await handle_failed_theft(message, thief, target, target_user_id)
        
    except Exception as e:
        logging.error(f"خطأ في محاولة السرقة: {e}")
        await message.reply("❌ حدث خطأ في عملية السرقة")


async def handle_successful_theft(message: Message, thief: dict, target: dict, target_user_id: int):
    """معالجة السرقة الناجحة"""
    try:
        # حساب المبلغ المسروق (10-30% من النقد المتاح)
        max_steal = min(target['balance'], GAME_SETTINGS['max_theft_amount'])
        stolen_amount = random.randint(int(max_steal * 0.1), int(max_steal * 0.3))
        stolen_amount = max(1, stolen_amount)  # على الأقل 1$
        
        # تحديث الأرصدة
        new_thief_balance = thief['balance'] + stolen_amount
        new_target_balance = target['balance'] - stolen_amount
        
        await update_user_balance(message.from_user.id, new_thief_balance)
        await update_user_balance(target_user_id, new_target_balance)
        
        # إضافة معاملة
        await add_transaction(
            from_user_id=target_user_id,
            to_user_id=message.from_user.id,
            transaction_type="theft_success",
            amount=stolen_amount,
            description=f"سرقة ناجحة من {target.get('username', 'مجهول')}"
        )
        
        # رسائل التهنئة المتنوعة
        success_messages = [
            "🎉 نجحت في السرقة!",
            "💰 عملية ناجحة!",
            "🔓 سرقة محترفة!",
            "⭐ مهمة مكتملة!",
            "🏆 لص ماهر!"
        ]
        
        success_msg = random.choice(success_messages)
        
        await message.reply(
            f"{success_msg}\n\n"
            f"💰 المبلغ المسروق: {format_number(stolen_amount)}$\n"
            f"👤 من: {target.get('username', 'مستخدم')}\n"
            f"💵 رصيدك الجديد: {format_number(new_thief_balance)}$\n\n"
            f"🎭 كن حذراً... قد يكتشف أمرك!"
        )
        
        # إشعار الضحية
        try:
            await message.bot.send_message(
                target_user_id,
                f"🚨 **تم سرقتك!**\n\n"
                f"💸 المبلغ المسروق: {format_number(stolen_amount)}$\n"
                f"👤 بواسطة: {message.from_user.username or 'لص مجهول'}\n"
                f"💰 رصيدك الجديد: {format_number(new_target_balance)}$\n\n"
                f"🛡 نصيحة: قم بترقية أمانك أو ضع أموالك في البنك!"
            )
        except:
            pass  # في حالة فشل إرسال الإشعار
        
        # إحصائيات
        await update_theft_stats(message.from_user.id, "successful_theft")
        await update_theft_stats(target_user_id, "times_stolen")
        
    except Exception as e:
        logging.error(f"خطأ في معالجة السرقة الناجحة: {e}")


async def handle_failed_theft(message: Message, thief: dict, target: dict, target_user_id: int):
    """معالجة السرقة الفاشلة"""
    try:
        # غرامة فشل السرقة (5-15% من رصيد اللص)
        penalty = random.randint(int(thief['balance'] * 0.05), int(thief['balance'] * 0.15))
        penalty = min(penalty, thief['balance'])  # لا تتجاوز الرصيد المتاح
        penalty = max(10, penalty)  # على الأقل 10$
        
        new_thief_balance = thief['balance'] - penalty
        
        await update_user_balance(message.from_user.id, new_thief_balance)
        
        # إضافة معاملة
        await add_transaction(
            from_user_id=message.from_user.id,
            to_user_id=0,  # النظام
            transaction_type="theft_failed",
            amount=penalty,
            description="غرامة فشل السرقة"
        )
        
        # رسائل الفشل المتنوعة
        failure_messages = [
            "😅 تم اكتشافك!",
            "🚨 فشلت العملية!",
            "❌ لص فاشل!",
            "🔒 الهدف محمي جيداً!",
            "⚠️ تم القبض عليك!"
        ]
        
        failure_msg = random.choice(failure_messages)
        
        await message.reply(
            f"{failure_msg}\n\n"
            f"💸 الغرامة: {format_number(penalty)}$\n"
            f"💰 رصيدك الجديد: {format_number(new_thief_balance)}$\n\n"
            f"💡 حاول تحسين مهاراتك في السرقة!"
        )
        
        # إشعار الهدف بمحاولة السرقة
        try:
            await message.bot.send_message(
                target_user_id,
                f"🛡 **أحبطت محاولة سرقة!**\n\n"
                f"👤 المحاول: {message.from_user.username or 'لص مجهول'}\n"
                f"🔒 نظام الأمان الخاص بك عمل بكفاءة!\n\n"
                f"💡 تأكد من ترقية أمانك باستمرار."
            )
        except:
            pass
        
        # إحصائيات
        await update_theft_stats(message.from_user.id, "failed_theft")
        
    except Exception as e:
        logging.error(f"خطأ في معالجة السرقة الفاشلة: {e}")


async def upgrade_security(message: Message, new_level: int):
    """ترقية مستوى الأمان"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        current_level = user.get('security_level', 1)
        
        if new_level <= current_level:
            await message.reply("❌ لديك هذا المستوى أو أعلى بالفعل")
            return
        
        if new_level not in SECURITY_LEVELS:
            await message.reply("❌ مستوى أمان غير صحيح")
            return
        
        upgrade_cost = SECURITY_LEVELS[new_level]['cost']
        
        if user['balance'] < upgrade_cost:
            await message.reply(
                f"❌ رصيد غير كافٍ!\n\n"
                f"🛡 تكلفة الترقية: {format_number(upgrade_cost)}$\n"
                f"💰 رصيدك الحالي: {format_number(user['balance'])}$\n"
                f"💸 تحتاج إلى: {format_number(upgrade_cost - user['balance'])}$ إضافية"
            )
            return
        
        # تنفيذ الترقية
        new_balance = user['balance'] - upgrade_cost
        await update_user_balance(message.from_user.id, new_balance)
        
        # تحديث مستوى الأمان
        await execute_query(
            "UPDATE users SET security_level = ? WHERE user_id = ?",
            (new_level, message.from_user.id)
        )
        
        security_info = SECURITY_LEVELS[new_level]
        
        await message.reply(
            f"🎉 **تم ترقية الأمان بنجاح!**\n\n"
            f"🛡 المستوى الجديد: {security_info['name']} ({new_level}/5)\n"
            f"🔒 نسبة الحماية: {security_info['protection']}%\n"
            f"💰 التكلفة: {format_number(upgrade_cost)}$\n"
            f"💵 رصيدك الجديد: {format_number(new_balance)}$\n\n"
            f"🛡 أموالك أكثر أماناً الآن!"
        )
        
    except Exception as e:
        logging.error(f"خطأ في ترقية الأمان: {e}")
        await message.reply("❌ حدث خطأ في ترقية الأمان")


async def show_upgrade_options(message: Message):
    """عرض خيارات ترقية الأمان"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        current_level = user.get('security_level', 1)
        
        keyboard_buttons = []
        upgrade_text = f"🛡 **ترقية نظام الأمان**\n\n"
        upgrade_text += f"🔒 مستواك الحالي: {SECURITY_LEVELS[current_level]['name']} ({current_level}/5)\n"
        upgrade_text += f"💰 رصيدك: {format_number(user['balance'])}$\n\n"
        
        for level, info in SECURITY_LEVELS.items():
            if level > current_level:
                affordable = "✅" if user['balance'] >= info['cost'] else "❌"
                upgrade_text += f"{affordable} {info['emoji']} **{info['name']}** (المستوى {level})\n"
                upgrade_text += f"   🔒 حماية: {info['protection']}%\n"
                upgrade_text += f"   💰 التكلفة: {format_number(info['cost'])}$\n\n"
                
                if user['balance'] >= info['cost']:
                    keyboard_buttons.append([InlineKeyboardButton(
                        text=f"{info['emoji']} ترقية إلى {info['name']} - {format_number(info['cost'])}$",
                        callback_data=f"theft_upgrade_security_{level}"
                    )])
        
        if not keyboard_buttons:
            await message.reply("🏆 لديك أقصى مستوى أمان! أنت محمي بالكامل.")
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        await message.reply(upgrade_text, reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"خطأ في عرض خيارات الترقية: {e}")
        await message.reply("❌ حدث خطأ في عرض خيارات الترقية")


async def get_theft_stats(user_id: int):
    """الحصول على إحصائيات السرقة للمستخدم"""
    try:
        # حساب السرقات الناجحة
        successful = await execute_query(
            "SELECT COUNT(*) as count FROM transactions WHERE user_id = ? AND transaction_type = 'theft_success'",
            (user_id,),
            fetch_one=True
        )
        
        # حساب السرقات الفاشلة
        failed = await execute_query(
            "SELECT COUNT(*) as count FROM transactions WHERE user_id = ? AND transaction_type = 'theft_failed'",
            (user_id,),
            fetch_one=True
        )
        
        # حساب مرات التعرض للسرقة (عندما يكون هذا المستخدم ضحية)
        stolen = await execute_query(
            "SELECT COUNT(*) as count FROM transactions WHERE description LIKE ? AND transaction_type = 'theft_success'",
            (f'%سرقة من {user_id}%',),
            fetch_one=True
        )
        
        return {
            'successful_thefts': successful['count'] if successful else 0,
            'failed_thefts': failed['count'] if failed else 0,
            'times_stolen': stolen['count'] if stolen else 0
        }
        
    except Exception as e:
        logging.error(f"خطأ في الحصول على إحصائيات السرقة: {e}")
        return {
            'successful_thefts': 0,
            'failed_thefts': 0,
            'times_stolen': 0
        }


async def update_theft_stats(user_id: int, stat_type: str):
    """تحديث إحصائيات السرقة"""
    try:
        await execute_query(
            "INSERT INTO stats (user_id, action_type, action_data) VALUES (?, ?, ?)",
            (user_id, stat_type, "")
        )
    except Exception as e:
        logging.error(f"خطأ في تحديث إحصائيات السرقة: {e}")


async def show_security_upgrade(message: Message):
    """عرض خيارات ترقية الأمان (نسخة نصية)"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        current_level = user.get('security_level', 1)
        
        # التحقق من أن المستخدم لا يملك أقصى مستوى
        if current_level >= 5:
            await message.reply("🏆 لديك أقصى مستوى أمان! أنت محمي بالكامل.")
            return
        
        upgrade_text = f"""
🛡 **ترقية نظام الأمان**

🔒 **مستواك الحالي:** {SECURITY_LEVELS[current_level]['name']} ({current_level}/5)
🛡 نسبة الحماية: {SECURITY_LEVELS[current_level]['protection']}%

💰 **رصيدك الحالي:** {format_number(user['balance'])}$

🔧 **الترقيات المتاحة:**
"""
        
        # إضافة خيارات الترقية
        next_level = current_level + 1
        if next_level <= 5:
            info = SECURITY_LEVELS[next_level]
            upgrade_text += f"\n{info['emoji']} **المستوى التالي:** {info['name']}"
            upgrade_text += f"\n💵 **التكلفة:** {format_number(info['cost'])}$"
            upgrade_text += f"\n🛡 **الحماية:** {info['protection']}%"
            
            if user['balance'] >= info['cost']:
                upgrade_text += f"\n\n✅ **يمكنك الترقية!**"
                upgrade_text += f"\n📝 **للترقية:** اكتب 'ترقية امان تأكيد'"
            else:
                needed = info['cost'] - user['balance']
                upgrade_text += f"\n\n❌ **رصيد غير كافٍ**"
                upgrade_text += f"\n💸 **تحتاج:** {format_number(needed)}$ إضافية"
        
        # عرض كل المستويات للمراجعة
        upgrade_text += f"\n\n📊 **جميع المستويات:**"
        for level in range(1, 6):
            info = SECURITY_LEVELS[level]
            status = "✅ (حالي)" if level == current_level else "🔒" if level > current_level else "✅"
            upgrade_text += f"\n{info['emoji']} {info['name']} - {format_number(info['cost'])}$ - {info['protection']}% {status}"
        
        await message.reply(upgrade_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض خيارات الترقية: {e}")
        await message.reply("❌ حدث خطأ في عرض خيارات الترقية")


async def upgrade_security_level(message: Message):
    """ترقية مستوى الأمان للمستخدم"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        current_level = user.get('security_level', 1)
        
        if current_level >= 5:
            await message.reply("🏆 لديك أقصى مستوى أمان بالفعل!")
            return
        
        next_level = current_level + 1
        upgrade_info = SECURITY_LEVELS[next_level]
        upgrade_cost = upgrade_info['cost']
        
        # التحقق من توفر الرصيد
        if user['balance'] < upgrade_cost:
            needed = upgrade_cost - user['balance']
            await message.reply(
                f"❌ رصيد غير كافٍ لترقية الأمان!\n\n"
                f"💵 التكلفة: {format_number(upgrade_cost)}$\n"
                f"💰 رصيدك: {format_number(user['balance'])}$\n"
                f"💸 تحتاج: {format_number(needed)}$ إضافية"
            )
            return
        
        # تنفيذ الترقية
        new_balance = user['balance'] - upgrade_cost
        
        await execute_query(
            "UPDATE users SET security_level = ?, balance = ? WHERE user_id = ?",
            (next_level, new_balance, message.from_user.id)
        )
        
        # إضافة معاملة
        await add_transaction(
            message.from_user.id,
            f"ترقية الأمان إلى {upgrade_info['name']}",
            -upgrade_cost,
            "security_upgrade"
        )
        
        await message.reply(
            f"🎉 **تم ترقية الأمان بنجاح!**\n\n"
            f"🔒 **المستوى الجديد:** {upgrade_info['emoji']} {upgrade_info['name']} ({next_level}/5)\n"
            f"🛡 **نسبة الحماية:** {upgrade_info['protection']}%\n"
            f"💵 **التكلفة:** {format_number(upgrade_cost)}$\n"
            f"💰 **رصيدك الجديد:** {format_number(new_balance)}$\n\n"
            f"🔐 أنت الآن محمي أكثر من السرقة!"
        )
        
    except Exception as e:
        logging.error(f"خطأ في ترقية الأمان: {e}")
        await message.reply("❌ حدث خطأ في ترقية الأمان")


async def show_theft_stats(message: Message):
    """عرض إحصائيات السرقة المفصلة"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        stats = await get_theft_stats(message.from_user.id)
        
        stats_text = f"""
📊 **إحصائياتك في السرقة**

👤 **اللاعب:** {message.from_user.first_name}

🔓 **كلص:**
✅ سرقات ناجحة: {stats['successful_thefts']}
❌ سرقات فاشلة: {stats['failed_thefts']}
📈 معدل النجاح: {(stats['successful_thefts'] / max(1, stats['successful_thefts'] + stats['failed_thefts']) * 100):.1f}%

🎯 **كضحية:**
🔒 مرات تم سرقتك: {stats['times_stolen']}

🛡 **الأمان:**
🔒 مستوى الأمان: {user.get('security_level', 1)}/5
🛡 نسبة الحماية: {SECURITY_LEVELS[user.get('security_level', 1)]['protection']}%

💡 **نصائح:**
• ضع أموالك في البنك لحمايتها
• ارفع مستوى الأمان لتقليل السرقة
• اسرق بذكاء واحذر من الفشل
        """
        
        await message.reply(stats_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض إحصائيات السرقة: {e}")
        await message.reply("❌ حدث خطأ في عرض الإحصائيات")


async def show_top_thieves(message: Message):
    """عرض أفضل اللصوص"""
    try:
        # الحصول على أفضل اللصوص من المعاملات
        top_thieves = await execute_query(
            """
            SELECT users.username, users.first_name, COUNT(*) as thefts
            FROM transactions 
            JOIN users ON transactions.user_id = users.user_id
            WHERE transactions.transaction_type = 'theft_success'
            GROUP BY transactions.user_id
            ORDER BY thefts DESC
            LIMIT 10
            """,
            (),
            fetch_all=True
        )
        
        leaderboard_text = "🏆 **أفضل اللصوص**\n\n"
        
        if not top_thieves:
            leaderboard_text += "🤷‍♂️ لا توجد سرقات ناجحة بعد!\n\nكن أول لص محترف!"
        else:
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            
            for i, thief in enumerate(top_thieves):
                medal = medals[i] if i < len(medals) else f"{i+1}️⃣"
                name = thief['first_name'] or thief['username'] or "مجهول"
                leaderboard_text += f"{medal} **{name}** - {thief['thefts']} سرقة ناجحة\n"
            
        leaderboard_text += f"\n💡 **تلميح:** كلما زادت سرقاتك الناجحة، كلما ارتفعت في التصنيف!"
        
        await message.reply(leaderboard_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض أفضل اللصوص: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة أفضل اللصوص")
