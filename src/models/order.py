"""
نماذج سلة التسوق والطلبات لمتجر سوقي الإلكتروني
يتضمن تعريف جداول سلة التسوق، الطلبات، تفاصيل الطلبات، وتحديثات حالة الطلب
"""

from datetime import datetime
from .user import db, User
from .address import Address
from .product import Product

class CartItem(db.Model):
    """
    نموذج عناصر سلة التسوق - يمثل جدول عناصر سلة التسوق في قاعدة البيانات
    """
    __tablename__ = 'cart_items'
    
    # الحقول الأساسية
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    
    # طوابع زمنية
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات مع الجداول الأخرى
    user = db.relationship('User', back_populates='cart_items')
    product = db.relationship('Product', back_populates='cart_items')
    
    def to_dict(self):
        """
        تحويل بيانات عنصر سلة التسوق إلى قاموس
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'product': self.product.to_dict() if self.product else None
        }
    
    def __repr__(self):
        return f'<CartItem {self.id} for User {self.user_id}>'


class Order(db.Model):
    """
    نموذج الطلبات - يمثل جدول الطلبات في قاعدة البيانات
    """
    __tablename__ = 'orders'
    
    # الحقول الأساسية
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    
    # حالة الطلب والدفع
    status = db.Column(db.String(50), nullable=False, default='processing')  # 'processing', 'shipped', 'delivered', 'cancelled'
    payment_status = db.Column(db.String(50), nullable=False, default='pending')  # 'pending', 'paid', 'failed', 'refunded'
    payment_method = db.Column(db.String(50))
    
    # ملاحظات إضافية
    notes = db.Column(db.Text)
    
    # طوابع زمنية
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات مع الجداول الأخرى
    user = db.relationship('User', back_populates='orders')
    address = db.relationship('Address', back_populates='orders')
    order_items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    status_history = db.relationship('OrderStatusHistory', back_populates='order', cascade='all, delete-orphan')
    
    def to_dict(self):
        """
        تحويل بيانات الطلب إلى قاموس
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'address_id': self.address_id,
            'total_amount': self.total_amount,
            'status': self.status,
            'payment_status': self.payment_status,
            'payment_method': self.payment_method,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'items': [item.to_dict() for item in self.order_items] if self.order_items else []
        }
    
    def __repr__(self):
        return f'<Order {self.id} for User {self.user_id}>'


class OrderItem(db.Model):
    """
    نموذج عناصر الطلب - يمثل جدول عناصر الطلب في قاعدة البيانات
    """
    __tablename__ = 'order_items'
    
    # الحقول الأساسية
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)  # سعر المنتج وقت الطلب
    
    # طوابع زمنية
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات مع الجداول الأخرى
    order = db.relationship('Order', back_populates='order_items')
    product = db.relationship('Product', back_populates='order_items')
    
    def to_dict(self):
        """
        تحويل بيانات عنصر الطلب إلى قاموس
        """
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'price': self.price,
            'subtotal': self.price * self.quantity,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'product': self.product.to_dict() if self.product else None
        }
    
    def __repr__(self):
        return f'<OrderItem {self.id} for Order {self.order_id}>'


class OrderStatusHistory(db.Model):
    """
    نموذج تاريخ حالة الطلب - يمثل جدول تاريخ حالة الطلب في قاعدة البيانات
    """
    __tablename__ = 'order_status_history'
    
    # الحقول الأساسية
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # طوابع زمنية
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقات مع الجداول الأخرى
    order = db.relationship('Order', back_populates='status_history')
    updated_by_user = db.relationship('User', back_populates='order_status_updates', foreign_keys=[updated_by])
    
    def to_dict(self):
        """
        تحويل بيانات تاريخ حالة الطلب إلى قاموس
        """
        return {
            'id': self.id,
            'order_id': self.order_id,
            'status': self.status,
            'notes': self.notes,
            'updated_by': self.updated_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<OrderStatusHistory {self.id} for Order {self.order_id}>'
