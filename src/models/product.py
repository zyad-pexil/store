"""
نموذج المنتجات لمتجر سوقي الإلكتروني
يتضمن تعريف جدول المنتجات وصورها وفئاتها
"""

from datetime import datetime
from .user import db, User

class Category(db.Model):
    """
    نموذج فئات المنتجات - يمثل جدول فئات المنتجات في قاعدة البيانات
    يستخدم لتصنيف المنتجات وتسهيل البحث والتصفية
    """
    __tablename__ = 'categories'
    
    # الحقول الأساسية
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image_path = db.Column(db.String(255))
    
    # الفئة الأم (للفئات الفرعية)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    
    # طوابع زمنية
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات مع الجداول الأخرى
    products = db.relationship('Product', back_populates='category')
    
    # العلاقة مع الفئات الفرعية
    subcategories = db.relationship('Category', 
                                   backref=db.backref('parent', remote_side=[id]),
                                   cascade='all, delete-orphan')
    
    def to_dict(self):
        """
        تحويل بيانات الفئة إلى قاموس
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'image_path': self.image_path,
            'parent_id': self.parent_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Category {self.name}>'


class Product(db.Model):
    """
    نموذج المنتجات - يمثل جدول المنتجات في قاعدة البيانات
    """
    __tablename__ = 'products'
    
    # الحقول الأساسية
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock_quantity = db.Column(db.Integer, default=0)
    
    # العلاقات مع الجداول الأخرى
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # حالة المنتج
    is_active = db.Column(db.Boolean, default=True)
    
    # طوابع زمنية
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات مع الجداول الأخرى
    category = db.relationship('Category', back_populates='products')
    created_by_user = db.relationship('User', back_populates='products', foreign_keys=[created_by])
    images = db.relationship('ProductImage', back_populates='product', cascade='all, delete-orphan')
    cart_items = db.relationship('CartItem', back_populates='product', cascade='all, delete-orphan')
    order_items = db.relationship('OrderItem', back_populates='product')
    reviews = db.relationship('Review', back_populates='product', cascade='all, delete-orphan')
    
    def to_dict(self):
        """
        تحويل بيانات المنتج إلى قاموس
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'stock_quantity': self.stock_quantity,
            'category_id': self.category_id,
            'created_by': self.created_by,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'images': [image.to_dict() for image in self.images] if self.images else []
        }
    
    def __repr__(self):
        return f'<Product {self.name}>'


class ProductImage(db.Model):
    """
    نموذج صور المنتجات - يمثل جدول صور المنتجات في قاعدة البيانات
    """
    __tablename__ = 'product_images'
    
    # الحقول الأساسية
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    
    # طوابع زمنية
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات مع الجداول الأخرى
    product = db.relationship('Product', back_populates='images')
    
    def to_dict(self):
        """
        تحويل بيانات صورة المنتج إلى قاموس
        """
        return {
            'id': self.id,
            'product_id': self.product_id,
            'image_path': self.image_path,
            'is_primary': self.is_primary,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<ProductImage {self.id} for Product {self.product_id}>'
