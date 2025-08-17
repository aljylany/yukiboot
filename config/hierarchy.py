"""
نظام الهرم الإداري للبوت
Administrative Hierarchy System
"""

import logging
from typing import List, Dict, Optional
from enum import Enum

class AdminLevel(Enum):
    """مستويات الإدارة"""
    MEMBER = 0          # عضو عادي
    MODERATOR = 1       # مشرف
    GROUP_OWNER = 2     # مالك المجموعة
    MASTER = 3          # السيد - صلاحيات مطلقة

# الأسياد - صلاحيات مطلقة في جميع المجموعات
MASTERS = [6524680126, 8278493069]

# مالكي المجموعات (يتم إدارتهم ديناميكياً)
GROUP_OWNERS: Dict[int, List[int]] = {}  # {group_id: [owner_ids]}

# المشرفين (يتم إدارتهم ديناميكياً)
MODERATORS: Dict[int, List[int]] = {}  # {group_id: [moderator_ids]}


def get_user_admin_level(user_id: int, group_id: int = None) -> AdminLevel:
    """
    الحصول على مستوى الإدارة للمستخدم في المجموعة المحددة
    
    Args:
        user_id: معرف المستخدم
        group_id: معرف المجموعة (اختياري)
        
    Returns:
        مستوى الإدارة
    """
    try:
        # فحص الأسياد أولاً - لهم صلاحيات مطلقة
        if user_id in MASTERS:
            return AdminLevel.MASTER
        
        # إذا لم يتم تحديد المجموعة، عضو عادي
        if not group_id:
            return AdminLevel.MEMBER
        
        # فحص مالكي المجموعات
        if group_id in GROUP_OWNERS and user_id in GROUP_OWNERS[group_id]:
            return AdminLevel.GROUP_OWNER
        
        # فحص المشرفين
        if group_id in MODERATORS and user_id in MODERATORS[group_id]:
            return AdminLevel.MODERATOR
        
        return AdminLevel.MEMBER
        
    except Exception as e:
        logging.error(f"خطأ في get_user_admin_level: {e}")
        return AdminLevel.MEMBER


def is_master(user_id: int) -> bool:
    """التحقق من كون المستخدم سيد"""
    return user_id in MASTERS


def is_group_owner(user_id: int, group_id: int) -> bool:
    """التحقق من كون المستخدم مالك للمجموعة"""
    return group_id in GROUP_OWNERS and user_id in GROUP_OWNERS[group_id]


def is_moderator(user_id: int, group_id: int) -> bool:
    """التحقق من كون المستخدم مشرف في المجموعة"""
    return group_id in MODERATORS and user_id in MODERATORS[group_id]


def has_permission(user_id: int, required_level: AdminLevel, group_id: int = None) -> bool:
    """
    التحقق من امتلاك المستخدم للصلاحية المطلوبة
    
    Args:
        user_id: معرف المستخدم
        required_level: المستوى المطلوب
        group_id: معرف المجموعة
        
    Returns:
        True إذا كان لديه الصلاحية
    """
    user_level = get_user_admin_level(user_id, group_id)
    return user_level.value >= required_level.value


def add_group_owner(group_id: int, user_id: int) -> bool:
    """إضافة مالك جديد للمجموعة"""
    try:
        if group_id not in GROUP_OWNERS:
            GROUP_OWNERS[group_id] = []
        
        if user_id not in GROUP_OWNERS[group_id]:
            GROUP_OWNERS[group_id].append(user_id)
            logging.info(f"تم إضافة مالك جديد {user_id} للمجموعة {group_id}")
            return True
        return False
    except Exception as e:
        logging.error(f"خطأ في add_group_owner: {e}")
        return False


def remove_group_owner(group_id: int, user_id: int) -> bool:
    """إزالة مالك من المجموعة"""
    try:
        if group_id in GROUP_OWNERS and user_id in GROUP_OWNERS[group_id]:
            GROUP_OWNERS[group_id].remove(user_id)
            if not GROUP_OWNERS[group_id]:
                del GROUP_OWNERS[group_id]
            logging.info(f"تم إزالة المالك {user_id} من المجموعة {group_id}")
            return True
        return False
    except Exception as e:
        logging.error(f"خطأ في remove_group_owner: {e}")
        return False


def add_moderator(group_id: int, user_id: int) -> bool:
    """إضافة مشرف جديد للمجموعة"""
    try:
        if group_id not in MODERATORS:
            MODERATORS[group_id] = []
        
        if user_id not in MODERATORS[group_id]:
            MODERATORS[group_id].append(user_id)
            logging.info(f"تم إضافة مشرف جديد {user_id} للمجموعة {group_id}")
            return True
        return False
    except Exception as e:
        logging.error(f"خطأ في add_moderator: {e}")
        return False


def remove_moderator(group_id: int, user_id: int) -> bool:
    """إزالة مشرف من المجموعة"""
    try:
        if group_id in MODERATORS and user_id in MODERATORS[group_id]:
            MODERATORS[group_id].remove(user_id)
            if not MODERATORS[group_id]:
                del MODERATORS[group_id]
            logging.info(f"تم إزالة المشرف {user_id} من المجموعة {group_id}")
            return True
        return False
    except Exception as e:
        logging.error(f"خطأ في remove_moderator: {e}")
        return False


def get_group_admins(group_id: int) -> Dict[str, List[int]]:
    """الحصول على جميع المديرين في المجموعة"""
    return {
        "masters": MASTERS,
        "owners": GROUP_OWNERS.get(group_id, []),
        "moderators": MODERATORS.get(group_id, [])
    }


def get_admin_level_name(level: AdminLevel) -> str:
    """الحصول على اسم المستوى بالعربية"""
    names = {
        AdminLevel.MEMBER: "عضو عادي",
        AdminLevel.MODERATOR: "مشرف", 
        AdminLevel.GROUP_OWNER: "مالك المجموعة",
        AdminLevel.MASTER: "السيد"
    }
    return names.get(level, "غير محدد")


def get_user_permissions(user_id: int, group_id: int = None) -> List[str]:
    """الحصول على قائمة بصلاحيات المستخدم"""
    level = get_user_admin_level(user_id, group_id)
    
    permissions = ["استخدام الأوامر العادية"]
    
    if level.value >= AdminLevel.MODERATOR.value:
        permissions.extend([
            "إدارة المجموعة الأساسية",
            "كتم وإلغاء كتم الأعضاء",
            "تحذير الأعضاء"
        ])
    
    if level.value >= AdminLevel.GROUP_OWNER.value:
        permissions.extend([
            "حظر وإلغاء حظر الأعضاء",
            "إضافة وإزالة المشرفين",
            "إدارة إعدادات المجموعة",
            "مسح الرسائل"
        ])
    
    if level.value >= AdminLevel.MASTER.value:
        permissions.extend([
            "🔴 أوامر السيد المطلقة:",
            "إعادة تشغيل البوت",
            "التدمير الذاتي للمجموعة", 
            "مغادرة المجموعات",
            "إدارة مالكي المجموعات",
            "الوصول لجميع الأوامر الإدارية"
        ])
    
    return permissions