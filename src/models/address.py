"""
نموذج العناوين لمتجر سوقي الإلكتروني
يتضمن تعريف جدول العناوين المرتبط بالمستخدمين
"""

from datetime import datetime
from .user import db, User

class Address(db.Model):
    """
    نموذج العنوان - يمثل جدول عناوين المستخدمين في قاعدة البيانات
    يستخدم للتوصيل وإتمام الطلبات
    """
    __tablename__ = 'addresses'
    
    # الحقول الأساسية
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # تفاصيل العنوان
    address_line1 = db.Column(db.String(255), nullable=False)
    address_line2 = db.Column(db.String(255))
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    
    # هل هو العنوان الافتراضي
    is_default = db.Column(db.Boolean, default=False)
    
    # طوابع زمنية
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات مع الجداول الأخرى
    user = db.relationship('User', back_populates='addresses')
    orders = db.relationship('Order', back_populates='address')
    
    def to_dict(self):
        """
        تحويل بيانات العنوان إلى قاموس
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'address_line1': self.address_line1,
            'address_line2': self.address_line2,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'country': self.country,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Address {self.id} for User {self.user_id}>'
