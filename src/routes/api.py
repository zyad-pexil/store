"""
مسارات واجهة برمجة التطبيقات (API) لمتجر سوقي الإلكتروني
يتضمن نقاط نهاية API للمنتجات، سلة التسوق، الطلبات، والإشعارات
"""

from flask import Blueprint, jsonify, request, session
from src.models import db, User, Product, Category, CartItem, Order, OrderItem, Review, Notification
from src.routes.auth import login_required, admin_required, customer_required
from functools import wraps
import json

# إنشاء مخطط المسارات
api_bp = Blueprint('api', __name__)

# وظيفة مساعدة للتحقق من API
def api_login_required(f):
    """
    مُزين للتحقق من تسجيل دخول المستخدم لطلبات API
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'يجب تسجيل الدخول للوصول إلى هذه الخدمة'}), 401
        return f(*args, **kwargs)
    return decorated_function

# نقاط نهاية API للمنتجات

@api_bp.route('/products', methods=['GET'])
def get_products():
    """
    الحصول على قائمة المنتجات
    """
    # البحث والتصفية
    search_query = request.args.get('search', '')
    category_id = request.args.get('category', '')
    sort_by = request.args.get('sort_by', 'newest')
    
    # بناء الاستعلام
    query = Product.query.filter(Product.is_active == True)
    
    # تطبيق البحث
    if search_query:
        query = query.filter(Product.name.ilike(f'%{search_query}%') | 
                            Product.description.ilike(f'%{search_query}%'))
    
    # تطبيق التصفية حسب الفئة
    if category_id and category_id.isdigit():
        query = query.filter(Product.category_id == int(category_id))
    
    # تطبيق الترتيب
    if sort_by == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort_by == 'price_high':
        query = query.order_by(Product.price.desc())
    else:  # 'newest' هو الافتراضي
        query = query.order_by(Product.created_at.desc())
    
    # تنفيذ الاستعلام
    products = query.all()
    
    # تحويل النتائج إلى JSON
    result = []
    for product in products:
        product_data = product.to_dict()
        result.append(product_data)
    
    return jsonify(result)

@api_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """
    الحصول على تفاصيل منتج محدد
    """
    product = Product.query.get_or_404(product_id)
    
    # الحصول على التقييمات المعتمدة فقط
    reviews = Review.query.filter_by(product_id=product_id, is_approved=True).all()
    
    # حساب متوسط التقييم
    avg_rating = 0
    if reviews:
        avg_rating = sum(review.rating for review in reviews) / len(reviews)
    
    # تحويل البيانات إلى JSON
    product_data = product.to_dict()
    product_data['avg_rating'] = avg_rating
    product_data['reviews'] = [review.to_dict() for review in reviews]
    
    return jsonify(product_data)

# نقاط نهاية API لسلة التسوق

@api_bp.route('/cart', methods=['GET'])
@api_login_required
def get_cart():
    """
    الحصول على محتويات سلة التسوق
    """
    user_id = session.get('user_id')
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    
    # تحويل البيانات إلى JSON
    result = []
    for item in cart_items:
        item_data = item.to_dict()
        result.append(item_data)
    
    # حساب المجموع
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    return jsonify({
        'items': result,
        'total': total
    })

@api_bp.route('/cart/add', methods=['POST'])
@api_login_required
def add_to_cart_api():
    """
    إضافة منتج إلى سلة التسوق
    """
    user_id = session.get('user_id')
    data = request.get_json()
    
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    if not product_id:
        return jsonify({'error': 'معرف المنتج مطلوب'}), 400
    
    product = Product.query.get_or_404(product_id)
    
    # التحقق من توفر المنتج
    if not product.is_active:
        return jsonify({'error': 'هذا المنتج غير متوفر حالياً'}), 400
    
    # التحقق من الكمية المطلوبة
    if quantity <= 0:
        return jsonify({'error': 'يجب أن تكون الكمية أكبر من صفر'}), 400
    
    if quantity > product.stock_quantity:
        return jsonify({'error': f'الكمية المطلوبة غير متوفرة. المتاح حالياً: {product.stock_quantity}'}), 400
    
    # التحقق مما إذا كان المنتج موجوداً بالفعل في السلة
    cart_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
    
    if cart_item:
        # تحديث الكمية
        cart_item.quantity += quantity
        if cart_item.quantity > product.stock_quantity:
            cart_item.quantity = product.stock_quantity
    else:
        # إضافة منتج جديد إلى السلة
        cart_item = CartItem(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity
        )
        db.session.add(cart_item)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'تمت إضافة المنتج إلى سلة التسوق'})

@api_bp.route('/cart/update', methods=['PUT'])
@api_login_required
def update_cart_api():
    """
    تحديث كمية منتج في سلة التسوق
    """
    user_id = session.get('user_id')
    data = request.get_json()
    
    cart_item_id = data.get('cart_item_id')
    quantity = data.get('quantity', 1)
    
    if not cart_item_id:
        return jsonify({'error': 'معرف عنصر السلة مطلوب'}), 400
    
    cart_item = CartItem.query.filter_by(id=cart_item_id, user_id=user_id).first_or_404()
    
    # التحقق من الكمية المطلوبة
    if quantity <= 0:
        # حذف العنصر من السلة
        db.session.delete(cart_item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'تم حذف المنتج من سلة التسوق'})
    else:
        # التحقق من توفر الكمية
        if quantity > cart_item.product.stock_quantity:
            quantity = cart_item.product.stock_quantity
        
        # تحديث الكمية
        cart_item.quantity = quantity
        db.session.commit()
        return jsonify({'success': True, 'message': 'تم تحديث سلة التسوق'})

@api_bp.route('/cart/remove', methods=['DELETE'])
@api_login_required
def remove_from_cart_api():
    """
    حذف منتج من سلة التسوق
    """
    user_id = session.get('user_id')
    data = request.get_json()
    
    cart_item_id = data.get('cart_item_id')
    
    if not cart_item_id:
        return jsonify({'error': 'معرف عنصر السلة مطلوب'}), 400
    
    cart_item = CartItem.query.filter_by(id=cart_item_id, user_id=user_id).first_or_404()
    
    db.session.delete(cart_item)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'تم حذف المنتج من سلة التسوق'})

# نقاط نهاية API للطلبات

@api_bp.route('/orders', methods=['GET'])
@api_login_required
def get_orders():
    """
    الحصول على قائمة طلبات المستخدم
    """
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    # التحقق من دور المستخدم
    if user.is_admin():
        # المدير يمكنه رؤية جميع الطلبات
        orders = Order.query.order_by(Order.created_at.desc()).all()
    else:
        # العميل يمكنه رؤية طلباته فقط
        orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    
    # تحويل البيانات إلى JSON
    result = []
    for order in orders:
        order_data = order.to_dict()
        result.append(order_data)
    
    return jsonify(result)

@api_bp.route('/orders/<int:order_id>', methods=['GET'])
@api_login_required
def get_order(order_id):
    """
    الحصول على تفاصيل طلب محدد
    """
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    # التحقق من دور المستخدم
    if user.is_admin():
        # المدير يمكنه رؤية أي طلب
        order = Order.query.get_or_404(order_id)
    else:
        # العميل يمكنه رؤية طلباته فقط
        order = Order.query.filter_by(id=order_id, user_id=user_id).first_or_404()
    
    # تحويل البيانات إلى JSON
    order_data = order.to_dict()
    
    return jsonify(order_data)

# نقاط نهاية API للإشعارات

@api_bp.route('/notifications', methods=['GET'])
@api_login_required
def get_notifications():
    """
    الحصول على إشعارات المستخدم
    """
    user_id = session.get('user_id')
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
    
    # تحويل البيانات إلى JSON
    result = []
    for notification in notifications:
        notification_data = notification.to_dict()
        result.append(notification_data)
    
    return jsonify(result)

@api_bp.route('/notifications/mark-read', methods=['POST'])
@api_login_required
def mark_notification_read():
    """
    تعليم الإشعار كمقروء
    """
    user_id = session.get('user_id')
    data = request.get_json()
    
    notification_id = data.get('notification_id')
    
    if not notification_id:
        return jsonify({'error': 'معرف الإشعار مطلوب'}), 400
    
    notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first_or_404()
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'تم تعليم الإشعار كمقروء'})

@api_bp.route('/notifications/mark-all-read', methods=['POST'])
@api_login_required
def mark_all_notifications_read():
    """
    تعليم جميع الإشعارات كمقروءة
    """
    user_id = session.get('user_id')
    
    Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'تم تعليم جميع الإشعارات كمقروءة'})
