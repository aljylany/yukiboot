"""
معالج الرسائل النصية
Bot Messages Handler
"""

import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.operations import get_or_create_user, update_user_activity, get_user
from modules import banks, real_estate, theft, stocks, investment, administration, farm, castle
from modules import admin_management, group_settings, entertainment
from utils.states import *
from utils.decorators import user_required, group_only
from config.settings import SYSTEM_MESSAGES

router = Router()


@router.message(F.text)
@user_required
async def handle_text_messages(message: Message, state: FSMContext):
    """معالج الرسائل النصية العامة حسب الحالة"""
    try:
        current_state = await state.get_state()
        
        if current_state is None:
            # رسالة عادية بدون حالة محددة
            await handle_general_message(message, state)
            return
        
        # معالجة الرسائل حسب الحالة
        if current_state.startswith("Banks"):
            await handle_banks_message(message, state, current_state)
        elif current_state.startswith("Property"):
            await handle_property_message(message, state, current_state)
        elif current_state.startswith("Theft"):
            await handle_theft_message(message, state, current_state)
        elif current_state.startswith("Stocks"):
            await handle_stocks_message(message, state, current_state)
        elif current_state.startswith("Investment"):
            await handle_investment_message(message, state, current_state)
        elif current_state.startswith("Farm"):
            await handle_farm_message(message, state, current_state)
        elif current_state.startswith("Castle"):
            await handle_castle_message(message, state, current_state)
        elif current_state.startswith("Admin"):
            await handle_admin_message(message, state, current_state)
        else:
            await handle_general_message(message, state)
            
    except Exception as e:
        logging.error(f"خطأ في معالجة الرسالة: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])
        await state.clear()


async def handle_transfer_command(message: Message):
    """معالج أمر التحويل عبر الرد على الرسائل"""
    try:
        # استخراج المبلغ من النص
        text_parts = message.text.split()
        if len(text_parts) < 2:
            await message.reply(
                "❌ استخدم الصيغة الصحيحة:\n"
                "رد على رسالة اللاعب واكتب: تحويل [المبلغ]\n\n"
                "مثال: تحويل 500"
            )
            return
        
        try:
            amount = int(text_parts[1])
        except ValueError:
            await message.reply("❌ يرجى كتابة مبلغ صحيح\n\nمثال: تحويل 500")
            return
        
        if amount <= 0:
            await message.reply("❌ يجب أن يكون المبلغ أكبر من صفر")
            return
        
        # الحصول على معلومات المرسل والمستقبل
        sender_id = message.from_user.id
        receiver_id = message.reply_to_message.from_user.id
        
        if sender_id == receiver_id:
            await message.reply("❌ لا يمكنك تحويل المال لنفسك!")
            return
        
        # التحقق من وجود المرسل
        from database.operations import get_user
        sender = await get_user(sender_id)
        if not sender:
            await message.reply("❌ لم تقم بإنشاء حساب بنكي بعد!\n\nاكتب 'انشاء حساب بنكي' للبدء")
            return
        
        # التحقق من وجود المستقبل
        receiver = await get_user(receiver_id)
        if not receiver:
            await message.reply(
                f"❌ {message.reply_to_message.from_user.first_name} لم ينشئ حساب بنكي بعد!\n"
                f"يجب عليه كتابة 'انشاء حساب بنكي' أولاً"
            )
            return
        
        # التحقق من توفر الرصيد
        if sender['balance'] < amount:
            from utils.helpers import format_number
            await message.reply(
                f"❌ رصيدك غير كافٍ!\n\n"
                f"💰 رصيدك الحالي: {format_number(sender['balance'])}$\n"
                f"💸 المبلغ المطلوب: {format_number(amount)}$"
            )
            return
        
        # تنفيذ عملية التحويل
        from database.operations import update_user_balance, add_transaction
        
        new_sender_balance = sender['balance'] - amount
        new_receiver_balance = receiver['balance'] + amount
        
        await update_user_balance(sender_id, new_sender_balance)
        await update_user_balance(receiver_id, new_receiver_balance)
        
        # تسجيل المعاملات
        await add_transaction(
            sender_id,
            f"تحويل إلى {message.reply_to_message.from_user.first_name}",
            -amount,
            "transfer"
        )
        await add_transaction(
            receiver_id,
            f"تحويل من {message.from_user.first_name}",
            amount,
            "transfer"
        )
        
        # رسالة التأكيد
        from utils.helpers import format_number
        success_msg = f"""
✅ **تم التحويل بنجاح!**

💸 المرسل: {message.from_user.first_name}
💰 المستقبل: {message.reply_to_message.from_user.first_name}
📊 المبلغ: {format_number(amount)}$

💵 رصيد {message.from_user.first_name}: {format_number(new_sender_balance)}$
💵 رصيد {message.reply_to_message.from_user.first_name}: {format_number(new_receiver_balance)}$
        """
        
        await message.reply(success_msg)
        
    except Exception as e:
        logging.error(f"خطأ في تحويل الأموال: {e}")
        await message.reply("❌ حدث خطأ أثناء التحويل، حاول مرة أخرى")


async def handle_general_message(message: Message, state: FSMContext):
    """معالجة الرسائل العامة - الكلمات المفتاحية فقط"""
    text = message.text.lower() if message.text else ""
    
    # التحقق من طلب إنشاء حساب بنكي
    if any(phrase in text for phrase in ['انشاء حساب بنكي', 'إنشاء حساب بنكي', 'انشئ حساب', 'حساب بنكي جديد']):
        await handle_bank_account_creation(message, state)
        return
    
    # البحث عن كلمات مفتاحية محددة فقط
    if any(word in text for word in ['راتب', 'مرتب', 'راتبي']):
        await banks.collect_daily_salary(message)
    elif text.startswith('تحويل') and message.reply_to_message:
        await handle_transfer_command(message)
    elif any(word in text for word in ['رصيد', 'فلوس', 'مال']):
        await banks.show_balance(message)
    elif any(word in text for word in ['بنك', 'ايداع', 'سحب']):
        await banks.show_bank_menu(message)
    elif any(word in text for word in ['عقار', 'بيت', 'شراء']):
        await real_estate.show_property_menu(message)
    elif any(word in text for word in ['سرقة', 'سرق', 'امان']):
        await theft.show_security_menu(message)
    elif any(word in text for word in ['اسهم', 'استثمار', 'محفظة']):
        await stocks.show_stocks_menu(message)
    elif any(word in text for word in ['مزرعة', 'زراعة', 'حصاد']):
        await farm.show_farm_menu(message)
    elif any(word in text for word in ['قلعة', 'ترقية', 'دفاع']):
        await castle.show_castle_menu(message)
    elif any(word in text for word in ['ترتيب', 'متصدرين', 'رانكنغ']):
        from modules import ranking
        await ranking.show_leaderboard(message)
    
    # === أوامر الإدارة والرفع/التنزيل ===
    elif text.startswith('رفع '):
        await handle_admin_command(message, text)
    elif text.startswith('تنزيل '):
        await handle_admin_command(message, text)
    elif text == 'تنزيل الكل':
        await admin_management.handle_rank_promotion(message, "", "تنزيل الكل")
    
    # === أوامر المسح ===
    elif text.startswith('مسح '):
        await handle_clear_command(message, text)
    
    # === أوامر الطرد والحظر ===
    elif text == 'حظر' or text.startswith('حظر '):
        await admin_management.handle_ban_user(message)
    elif text == 'طرد' or text.startswith('طرد '):
        await admin_management.handle_kick_user(message)
    elif text == 'كتم' or text.startswith('كتم '):
        await admin_management.handle_mute_user(message)
    elif text.startswith('تحذير '):
        await admin_management.handle_warn_user(message)
    
    # === أوامر القفل والفتح ===
    elif text.startswith('قفل '):
        await handle_lock_command(message, text)
    elif text.startswith('فتح '):
        await handle_unlock_command(message, text)
    
    # === أوامر التفعيل والتعطيل ===
    elif text.startswith('تفعيل '):
        await handle_toggle_command(message, text, 'تفعيل')
    elif text.startswith('تعطيل '):
        await handle_toggle_command(message, text, 'تعطيل')
    
    # === أوامر العرض ===
    elif text in ['المالكين الاساسيين', 'المالكين', 'المنشئين', 'المدراء', 'الادمنيه', 'المميزين']:
        await admin_management.show_group_ranks(message, text)
    elif text == 'الاعدادات':
        await group_settings.show_group_settings(message)
    elif text == 'القوانين':
        await group_settings.show_group_rules(message)
    elif text == 'المجموعه':
        await group_settings.show_group_info(message)
    
    # === أوامر التسلية ===
    elif any(rank in text for rank in ['هطف', 'بثر', 'حمار', 'كلب', 'كلبه', 'عتوي', 'عتويه', 'لحجي', 'لحجيه', 'خروف', 'خفيفه', 'خفيف']):
        await handle_entertainment_rank_command(message, text)
    elif text in ['زواج', 'طلاق']:
        await entertainment.handle_marriage(message, text)
    elif text in ['زوجي', 'زوجتي']:
        await entertainment.show_marriage_status(message)
    elif text in ['سيارتي', 'منزلي', 'عمري', 'طولي', 'وزني', 'تحبني', 'تكرهني']:
        await entertainment.handle_entertainment_command(message, text)
    elif text.startswith('نسبه '):
        await entertainment.handle_entertainment_command(message, text)
    
    # إزالة الرد الافتراضي - البوت لن يرد على الرسائل غير المعروفة


# === دوال مساعدة للأوامر الإدارية ===

async def handle_admin_command(message: Message, text: str):
    """معالج أوامر الرفع والتنزيل"""
    try:
        parts = text.split()
        if len(parts) < 2:
            return
            
        action = parts[0]  # رفع أو تنزيل
        rank_text = ' '.join(parts[1:])  # باقي النص
        
        # تحديد نوع الرتبة
        rank_map = {
            'مالك اساسي': 'مالك اساسي',
            'مالك': 'مالك', 
            'منشئ': 'منشئ',
            'مدير': 'مدير',
            'ادمن': 'ادمن',
            'مشرف': 'مشرف',
            'مميز': 'مميز'
        }
        
        rank_type = None
        for key, value in rank_map.items():
            if key in rank_text:
                rank_type = value
                break
        
        if rank_type:
            await admin_management.handle_rank_promotion(message, rank_type, action)
            
    except Exception as e:
        logging.error(f"خطأ في معالجة الأمر الإداري: {e}")


async def handle_clear_command(message: Message, text: str):
    """معالج أوامر المسح"""
    try:
        clear_text = text.replace('مسح ', '').strip()
        
        if clear_text == 'الكل':
            await admin_management.handle_clear_ranks(message, 'الكل')
        elif clear_text == 'المالكين':
            await admin_management.handle_clear_ranks(message, 'مالك')
        elif clear_text == 'المنشئين':
            await admin_management.handle_clear_ranks(message, 'منشئ')
        elif clear_text == 'المدراء':
            await admin_management.handle_clear_ranks(message, 'مدير')
        elif clear_text == 'الادمنيه':
            await admin_management.handle_clear_ranks(message, 'ادمن')
        elif clear_text == 'المميزين':
            await admin_management.handle_clear_ranks(message, 'مميز')
        elif clear_text.isdigit():
            # مسح عدد من الرسائل
            count = int(clear_text)
            await group_settings.handle_delete_messages(message, count)
        elif clear_text == 'بالرد' and message.reply_to_message:
            # مسح رسالة واحدة بالرد
            await group_settings.handle_delete_messages(message, 1)
            
    except Exception as e:
        logging.error(f"خطأ في معالجة أمر المسح: {e}")


async def handle_lock_command(message: Message, text: str):
    """معالج أوامر القفل"""
    try:
        setting = text.replace('قفل ', '').strip()
        await group_settings.handle_lock_command(message, setting, 'قفل')
    except Exception as e:
        logging.error(f"خطأ في معالجة أمر القفل: {e}")


async def handle_unlock_command(message: Message, text: str):
    """معالج أوامر الفتح"""
    try:
        setting = text.replace('فتح ', '').strip()
        await group_settings.handle_lock_command(message, setting, 'فتح')
    except Exception as e:
        logging.error(f"خطأ في معالجة أمر الفتح: {e}")


async def handle_toggle_command(message: Message, text: str, action: str):
    """معالج أوامر التفعيل والتعطيل"""
    try:
        setting = text.replace(f'{action} ', '').strip()
        await group_settings.handle_toggle_command(message, setting, action)
    except Exception as e:
        logging.error(f"خطأ في معالجة أمر {action}: {e}")


async def handle_entertainment_rank_command(message: Message, text: str):
    """معالج أوامر رتب التسلية"""
    try:
        # تحديد الرتبة والعمل
        entertainment_ranks = ['هطف', 'بثر', 'حمار', 'كلب', 'كلبه', 'عتوي', 'عتويه', 'لحجي', 'لحجيه', 'خروف', 'خفيفه', 'خفيف']
        
        rank_type = None
        action = None
        
        # البحث عن نوع الرتبة
        for rank in entertainment_ranks:
            if rank in text:
                rank_type = rank
                break
        
        # تحديد العمل (رفع أو تنزيل)
        if text.startswith('رفع '):
            action = 'رفع'
        elif text.startswith('تنزيل '):
            action = 'تنزيل'
        
        if rank_type and action:
            await entertainment.handle_entertainment_rank(message, rank_type, action)
        elif rank_type and not action:
            # عرض قائمة الرتبة
            await entertainment.show_entertainment_ranks(message, rank_type)
            
    except Exception as e:
        logging.error(f"خطأ في معالجة رتب التسلية: {e}")


async def handle_bank_account_creation(message: Message, state: FSMContext):
    """معالج إنشاء الحساب البنكي"""
    try:
        # التحقق من أن المحادثة في مجموعة
        if message.chat.type == 'private':
            await message.reply(
                "🚫 يجب إنشاء الحساب البنكي في المجموعة فقط!\n\n"
                "➕ أضف البوت لمجموعتك واكتب 'انشاء حساب بنكي' هناك"
            )
            return
            
        # التحقق من وجود المستخدم مسبقاً
        user = await get_user(message.from_user.id)
        if user:
            await message.reply(
                f"✅ أهلاً بعودتك {message.from_user.first_name}!\n\n"
                f"لديك حساب بنكي بالفعل برصيد: {user['balance']}$\n"
                f"اكتب 'رصيد' لعرض تفاصيل حسابك"
            )
            return
        
        # إنشاء حساب جديد مع نظام اختيار البنك
        await banks.start_bank_selection(message)
        
        # تعيين الحالة لانتظار اختيار البنك
        await state.set_state(BanksStates.waiting_bank_selection)
        
    except Exception as e:
        logging.error(f"خطأ في إنشاء الحساب البنكي: {e}")
        await message.reply("❌ حدث خطأ أثناء إنشاء حسابك، حاول مرة أخرى")


async def handle_banks_message(message: Message, state: FSMContext, current_state: str):
    """معالجة رسائل البنوك"""
    if current_state == BanksStates.waiting_bank_selection.state:
        await banks.process_bank_selection(message, state)
    elif current_state == BanksStates.waiting_deposit_amount.state:
        await banks.process_deposit_amount(message, state)
    elif current_state == BanksStates.waiting_withdraw_amount.state:
        await banks.process_withdraw_amount(message, state)
    elif current_state == BanksStates.waiting_transfer_user.state:
        await banks.process_transfer_user(message, state)
    elif current_state == BanksStates.waiting_transfer_amount.state:
        await banks.process_transfer_amount(message, state)


async def handle_property_message(message: Message, state: FSMContext, current_state: str):
    """معالجة رسائل العقارات"""
    if current_state == PropertyStates.waiting_property_choice.state:
        await real_estate.process_property_choice(message, state)
    elif current_state == PropertyStates.waiting_sell_confirmation.state:
        await real_estate.process_sell_confirmation(message, state)


async def handle_theft_message(message: Message, state: FSMContext, current_state: str):
    """معالجة رسائل السرقة"""
    if current_state == TheftStates.waiting_target_user.state:
        await theft.process_target_user(message, state)


async def handle_stocks_message(message: Message, state: FSMContext, current_state: str):
    """معالجة رسائل الأسهم"""
    if current_state == StocksStates.waiting_stock_symbol.state:
        await stocks.process_stock_symbol(message, state)
    elif current_state == StocksStates.waiting_buy_quantity.state:
        await stocks.process_buy_quantity(message, state)
    elif current_state == StocksStates.waiting_sell_quantity.state:
        await stocks.process_sell_quantity(message, state)


async def handle_investment_message(message: Message, state: FSMContext, current_state: str):
    """معالجة رسائل الاستثمار"""
    if current_state == InvestmentStates.waiting_investment_amount.state:
        await investment.process_investment_amount(message, state)
    elif current_state == InvestmentStates.waiting_investment_duration.state:
        await investment.process_investment_duration(message, state)


async def handle_farm_message(message: Message, state: FSMContext, current_state: str):
    """معالجة رسائل المزرعة"""
    if current_state == FarmStates.waiting_crop_quantity.state:
        await farm.process_crop_quantity(message, state)


async def handle_castle_message(message: Message, state: FSMContext, current_state: str):
    """معالجة رسائل القلعة"""
    if current_state == CastleStates.waiting_upgrade_confirmation.state:
        await castle.process_upgrade_confirmation(message, state)


async def handle_admin_message(message: Message, state: FSMContext, current_state: str):
    """معالجة رسائل الإدارة"""
    if current_state == AdminStates.waiting_broadcast_message.state:
        await administration.process_broadcast_message(message, state)
    elif current_state == AdminStates.waiting_user_id_action.state:
        await administration.process_user_id_action(message, state)


# معالج الصور والملفات
@router.message(F.photo | F.document | F.video | F.audio)
@user_required
async def handle_media_messages(message: Message):
    """معالج الرسائل المتعددة الوسائط"""
    await message.reply(
        "📷 تم استلام الملف!\n\n"
        "حالياً لا يدعم البوت معالجة الملفات، "
        "لكن يمكنك استخدام الأوامر النصية للتفاعل مع البوت."
    )


# معالج الملصقات
@router.message(F.sticker)
@user_required
async def handle_sticker_messages(message: Message):
    """معالج الملصقات"""
    stickers = [
        "🎮", "💰", "🏦", "🏠", "🔓", "📈", "🌾", "🏰", "⭐"
    ]
    import random
    
    await message.reply(
        f"{random.choice(stickers)} ملصق جميل!\n\n"
        "استخدم /help لعرض الأوامر المتاحة."
    )


# معالج جهات الاتصال
@router.message(F.contact)
@user_required
async def handle_contact_messages(message: Message):
    """معالج جهات الاتصال"""
    await message.reply(
        "📞 شكراً لمشاركة جهة الاتصال!\n\n"
        "حالياً لا نحتاج لهذه المعلومات، "
        "يمكنك استخدام الأوامر العادية للتفاعل مع البوت."
    )


# معالج المواقع الجغرافية
@router.message(F.location)
@user_required
async def handle_location_messages(message: Message):
    """معالج المواقع الجغرافية"""
    await message.reply(
        "📍 تم استلام موقعك الجغرافي!\n\n"
        "في المستقبل قد نضيف ميزات تعتمد على الموقع، "
        "لكن حالياً يمكنك استخدام الأوامر العادية."
    )
