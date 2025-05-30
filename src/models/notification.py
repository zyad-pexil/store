"""
نموذج الإشعارات لمتجر سوقي الإلكتروني
يتضمن تعريف جدول الإشعارات المرسلة للمستخدمين
"""

from datetime import datetime
from .user import db, User

class Notification(db.Model):
    """
    نموذج الإشعارات - يمثل جدول إشعارات المستخدمين في قاعدة البيانات
    يستخدم لإرسال تنبيهات للمستخدمين عن حالة الطلبات والتحديثات
    """
    __tablename__ = 'notifications'
    
    # الحقول الأساسية
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # نوع الإشعار ومحتواه
    type = db.Column(db.String(50), nullable=False)  # مثل 'new_order', 'status_update', 'review_approved'
    content = db.Column(db.Text, nullable=False)
    related_id = db.Column(db.Integer)  # معرف العنصر المرتبط (مثل معرف الطلب)
    
    # حالة الإشعار
    is_read = db.Column(db.Boolean, default=False)
    
    # طوابع زمنية
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات مع الجداول الأخرى
    user = db.relationship('User', back_populates='notifications')
    
    def to_dict(self):
        """
        تحويل بيانات الإشعار إلى قاموس
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'content': self.content,
            'related_id': self.related_id,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Notification {self.id} for User {self.user_id}>'
