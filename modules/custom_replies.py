"""
وحدة إدارة الردود المخصصة والكلمات المفتاحية
Custom Replies Management Module
"""

import logging
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from database.operations import execute_query
from utils.states import CustomReplyStates
from config.hierarchy import MASTERS, is_group_owner, is_moderator


async def start_add_custom_reply(message: Message, state: FSMContext):
    """بدء عملية إضافة رد مخصص"""
    try:
        if not message.from_user:
            await message.reply("❌ خطأ في معرف المستخدم")
            return
        
        user_id = message.from_user.id
        group_id = message.chat.id
        
        # التحقق من الصلاحيات
        if not (user_id in MASTERS or await is_group_owner(user_id, group_id) or await is_moderator(user_id, group_id)):
            await message.reply("❌ هذا الأمر متاح للمشرفين ومالكي المجموعات والسادة فقط")
            return
        
        # حفظ معلومات المستخدم في الحالة
        await state.update_data(user_id=user_id, group_id=group_id)
        await state.set_state(CustomReplyStates.waiting_for_keyword)
        
        await message.reply("📝 **إضافة رد مخصص**\n\n🔤 يرجى إرسال الكلمة المفتاحية التي تريد إضافة رد لها:")
        
    except Exception as e:
        logging.error(f"خطأ في بدء إضافة الرد المخصص: {e}")
        await message.reply("❌ حدث خطأ في إضافة الرد المخصص")


async def handle_keyword_input(message: Message, state: FSMContext):
    """معالجة إدخال الكلمة المفتاحية"""
    try:
        if not message.text:
            await message.reply("❌ يرجى إرسال كلمة مفتاحية صحيحة")
            return
        
        keyword = message.text.strip()
        
        if len(keyword) < 2:
            await message.reply("❌ الكلمة المفتاحية يجب أن تكون أطول من حرفين")
            return
        
        if len(keyword) > 50:
            await message.reply("❌ الكلمة المفتاحية طويلة جداً (الحد الأقصى 50 حرف)")
            return
        
        # حفظ الكلمة المفتاحية في الحالة
        await state.update_data(keyword=keyword)
        await state.set_state(CustomReplyStates.waiting_for_response)
        
        await message.reply(f"✅ تم حفظ الكلمة المفتاحية: **{keyword}**\n\n📝 الآن يرجى إرسال الرد الذي تريد أن يظهر عند كتابة هذه الكلمة:")
        
    except Exception as e:
        logging.error(f"خطأ في معالجة الكلمة المفتاحية: {e}")
        await message.reply("❌ حدث خطأ في معالجة الكلمة المفتاحية")


async def handle_response_input(message: Message, state: FSMContext):
    """معالجة إدخال الرد"""
    try:
        if not message.text:
            await message.reply("❌ يرجى إرسال رد صحيح")
            return
        
        response = message.text.strip()
        
        if len(response) < 1:
            await message.reply("❌ الرد لا يمكن أن يكون فارغاً")
            return
        
        if len(response) > 1000:
            await message.reply("❌ الرد طويل جداً (الحد الأقصى 1000 حرف)")
            return
        
        # الحصول على البيانات المحفوظة
        data = await state.get_data()
        keyword = data.get('keyword')
        user_id = data.get('user_id')
        group_id = data.get('group_id')
        
        # حفظ الرد في الحالة
        await state.update_data(response=response)
        
        # التحقق إذا كان المستخدم سيد لإظهار خيارات النطاق
        if user_id in MASTERS:
            await state.set_state(CustomReplyStates.waiting_for_scope)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 هذه المجموعة فقط", callback_data="scope_group")],
                [InlineKeyboardButton(text="🌐 كامل البوت", callback_data="scope_global")],
                [InlineKeyboardButton(text="❌ إلغاء", callback_data="scope_cancel")]
            ])
            
            await message.reply(
                f"✅ تم حفظ الرد: **{response[:50]}{'...' if len(response) > 50 else ''}**\n\n"
                f"🎯 **اختر نطاق التطبيق:**\n"
                f"🏠 **هذه المجموعة فقط**: سيعمل الرد في هذه المجموعة فقط\n"
                f"🌐 **كامل البوت**: سيعمل الرد في جميع المجموعات",
                reply_markup=keyboard
            )
        else:
            # المستخدم ليس سيد، حفظ للمجموعة الحالية فقط
            await save_custom_reply(keyword, response, user_id, group_id, message)
            await state.clear()
        
    except Exception as e:
        logging.error(f"خطأ في معالجة الرد: {e}")
        await message.reply("❌ حدث خطأ في معالجة الرد")


async def handle_scope_callback(callback_query, state: FSMContext):
    """معالجة اختيار نطاق التطبيق"""
    try:
        data = await state.get_data()
        keyword = data.get('keyword')
        response = data.get('response')
        user_id = data.get('user_id')
        group_id = data.get('group_id')
        
        if callback_query.data == "scope_cancel":
            await state.clear()
            await callback_query.message.edit_text("❌ تم إلغاء إضافة الرد المخصص")
            return
        
        # تحديد نطاق التطبيق
        if callback_query.data == "scope_global":
            scope_group_id = None  # كامل البوت
            scope_text = "🌐 كامل البوت"
        else:  # scope_group
            scope_group_id = group_id  # المجموعة الحالية فقط
            scope_text = "🏠 هذه المجموعة فقط"
        
        await save_custom_reply(keyword, response, user_id, scope_group_id, callback_query.message)
        await state.clear()
        
        await callback_query.message.edit_text(
            f"✅ **تم إضافة الرد المخصص بنجاح!**\n\n"
            f"🔤 **الكلمة المفتاحية:** {keyword}\n"
            f"📝 **الرد:** {response[:100]}{'...' if len(response) > 100 else ''}\n"
            f"🎯 **النطاق:** {scope_text}\n"
            f"👤 **أضافه:** {callback_query.from_user.first_name}"
        )
        
    except Exception as e:
        logging.error(f"خطأ في معالجة نطاق التطبيق: {e}")
        await callback_query.message.edit_text("❌ حدث خطأ في حفظ الرد المخصص")


async def save_custom_reply(keyword, response, user_id, group_id, message):
    """حفظ الرد المخصص في قاعدة البيانات"""
    try:
        # التحقق من وجود الكلمة المفتاحية مسبقاً
        check_query = "SELECT id FROM custom_replies WHERE trigger_word = ? AND chat_id = ?"
        existing = await execute_query(check_query, (keyword, group_id), fetch_one=True)
        
        if existing:
            # تحديث الرد الموجود
            update_query = """
                UPDATE custom_replies 
                SET reply_text = ?, created_by = ?, created_at = datetime('now')
                WHERE trigger_word = ? AND chat_id = ?
            """
            await execute_query(update_query, (response, user_id, keyword, group_id))
            action = "تحديث"
        else:
            # إضافة رد جديد
            insert_query = """
                INSERT INTO custom_replies (trigger_word, reply_text, chat_id, created_by, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            """
            await execute_query(insert_query, (keyword, response, group_id, user_id))
            action = "إضافة"
        
        scope_text = "كامل البوت" if group_id is None else "هذه المجموعة"
        
        await message.reply(
            f"✅ **تم {action} الرد المخصص بنجاح!**\n\n"
            f"🔤 **الكلمة المفتاحية:** {keyword}\n"
            f"📝 **الرد:** {response[:100]}{'...' if len(response) > 100 else ''}\n"
            f"🎯 **النطاق:** {scope_text}"
        )
        
    except Exception as e:
        logging.error(f"خطأ في حفظ الرد المخصص: {e}")
        await message.reply("❌ حدث خطأ في حفظ الرد المخصص")


async def check_for_custom_replies(message: Message):
    """فحص الرسائل للكلمات المفتاحية المخصصة"""
    try:
        if not message.text or not message.chat:
            return False
        
        text = message.text.lower().strip()
        group_id = message.chat.id
        
        logging.info(f"فحص رد مخصص للنص: '{text}' في المجموعة: {group_id}")
        
        # استيراد مباشر لتجنب مشاكل الاستيراد
        import aiosqlite
        
        # البحث في ردود المجموعة الحالية مباشرة
        try:
            async with aiosqlite.connect("bot_database.db") as db:
                db.row_factory = aiosqlite.Row
                
                # البحث في ردود المجموعة الحالية
                async with db.execute(
                    "SELECT reply_text FROM custom_replies WHERE trigger_word = ? AND chat_id = ?",
                    (text, group_id)
                ) as cursor:
                    group_result = await cursor.fetchone()
                    
                logging.info(f"نتيجة البحث في المجموعة: {group_result}")
                
                if group_result:
                    await message.reply(group_result[0])
                    logging.info(f"تم العثور على رد مخصص في المجموعة: {group_result[0]}")
                    return True
                
                # البحث في الردود العامة (كامل البوت)
                async with db.execute(
                    "SELECT reply_text FROM custom_replies WHERE trigger_word = ? AND chat_id IS NULL",
                    (text,)
                ) as cursor:
                    global_result = await cursor.fetchone()
                    
                logging.info(f"نتيجة البحث العامة: {global_result}")
                
                if global_result:
                    await message.reply(global_result[0])
                    logging.info(f"تم العثور على رد مخصص عام: {global_result[0]}")
                    return True
                
                logging.info("لم يتم العثور على رد مخصص")
                return False
                
        except Exception as db_error:
            logging.error(f"خطأ في قاعدة البيانات: {db_error}")
            return False
        
    except Exception as e:
        logging.error(f"خطأ في فحص الردود المخصصة: {e}")
        import traceback
        logging.error(f"تفاصيل الخطأ: {traceback.format_exc()}")
        return False