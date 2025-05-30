"""
نموذج المستخدم لمتجر سوقي الإلكتروني
يتضمن تعريف جدول المستخدمين مع الأدوار المختلفة (عميل/مدير)
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship

db = SQLAlchemy()

class User(db.Model):
    """
    نموذج المستخدم - يمثل جدول المستخدمين في قاعدة البيانات
    يدعم أدوار مختلفة (عميل/مدير) مع تشفير كلمة المرور
    """
    __tablename__ = 'users'
    
    # الحقول الأساسية
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='customer')  # 'customer' أو 'admin'
    
    # معلومات المستخدم
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    
    # طوابع زمنية
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات مع الجداول الأخرى
    addresses = relationship('Address', back_populates='user', cascade='all, delete-orphan')
    orders = relationship('Order', back_populates='user', cascade='all, delete-orphan')
    cart_items = relationship('CartItem', back_populates='user', cascade='all, delete-orphan')
    reviews = relationship('Review', back_populates='user', cascade='all, delete-orphan')
    notifications = relationship('Notification', back_populates='user', cascade='all, delete-orphan')
    
    # المنتجات التي أضافها المستخدم (للمديرين فقط)
    products = relationship('Product', back_populates='created_by_user', foreign_keys='Product.created_by')
    
    # تحديثات حالة الطلبات التي قام بها المستخدم (للمديرين فقط)
    order_status_updates = relationship('OrderStatusHistory', back_populates='updated_by_user', foreign_keys='OrderStatusHistory.updated_by')
    
    @property
    def password(self):
        """
        منع الوصول المباشر لكلمة المرور
        """
        raise AttributeError('لا يمكن قراءة كلمة المرور مباشرة')
    
    @password.setter
    def password(self, password):
        """
        تعيين كلمة المرور مع التشفير
        """
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        """
        التحقق من صحة كلمة المرور
        """
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """
        التحقق مما إذا كان المستخدم مديرًا
        """
        return self.role == 'admin'
    
    def is_customer(self):
        """
        التحقق مما إذا كان المستخدم عميلًا
        """
        return self.role == 'customer'
    
    def to_dict(self):
        """
        تحويل بيانات المستخدم إلى قاموس (مع إخفاء كلمة المرور)
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'
