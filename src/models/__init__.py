"""
ملف تجميع النماذج لمتجر سوقي الإلكتروني
يقوم بتجميع جميع نماذج قاعدة البيانات في مكان واحد
"""

from .user import db, User
from .address import Address
from .notification import Notification
from .product import Category, Product, ProductImage
from .order import CartItem, Order, OrderItem, OrderStatusHistory
from .review import Review

# تصدير جميع النماذج لسهولة الاستيراد
__all__ = [
    'db',
    'User',
    'Address',
    'Notification',
    'Category',
    'Product',
    'ProductImage',
    'CartItem',
    'Order',
    'OrderItem',
    'OrderStatusHistory',
    'Review'
]
