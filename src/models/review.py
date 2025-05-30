"""
نموذج التقييمات لمتجر سوقي الإلكتروني
يتضمن تعريف جدول تقييمات المنتجات من قبل العملاء
"""

from datetime import datetime
from .user import db, User
from .product import Product

class Review(db.Model):
    """
    نموذج التقييمات - يمثل جدول تقييمات المنتجات في قاعدة البيانات
    """
    __tablename__ = 'reviews'
    
    # الحقول الأساسية
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # تقييم من 1 إلى 5
    comment = db.Column(db.Text)
    
    # حالة الموافقة
    is_approved = db.Column(db.Boolean, default=False)
    
    # طوابع زمنية
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات مع الجداول الأخرى
    product = db.relationship('Product', back_populates='reviews')
    user = db.relationship('User', back_populates='reviews')
    
    def to_dict(self):
        """
        تحويل بيانات التقييم إلى قاموس
        """
        return {
            'id': self.id,
            'product_id': self.product_id,
            'user_id': self.user_id,
            'rating': self.rating,
            'comment': self.comment,
            'is_approved': self.is_approved,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user_name': f"{self.user.first_name} {self.user.last_name}" if self.user else "مستخدم مجهول"
        }
    
    def __repr__(self):
        return f'<Review {self.id} for Product {self.product_id}>'
