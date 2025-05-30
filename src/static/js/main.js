/**
 * وظائف JavaScript الرئيسية لمتجر سوقي الإلكتروني
 * تدعم التفاعلية والتصميم المتجاوب
 */

// التأكد من تحميل المستند بالكامل
document.addEventListener('DOMContentLoaded', function() {
    // تفعيل القائمة المتنقلة للأجهزة الصغيرة
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');
    
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', function() {
            navLinks.classList.toggle('active');
        });
    }
    
    // إخفاء رسائل التنبيه تلقائياً بعد فترة
    const alerts = document.querySelectorAll('.alert');
    if (alerts.length > 0) {
        alerts.forEach(alert => {
            setTimeout(() => {
                alert.style.opacity = '0';
                setTimeout(() => {
                    alert.style.display = 'none';
                }, 500);
            }, 5000);
        });
    }
    
    // تفعيل التحقق من صحة النماذج
    const forms = document.querySelectorAll('form');
    if (forms.length > 0) {
        forms.forEach(form => {
            form.addEventListener('submit', validateForm);
        });
    }
    
    // تفعيل أزرار الكمية في سلة التسوق
    setupQuantityButtons();
    
    // تفعيل نظام التقييمات
    setupRatingSystem();
    
    // تفعيل البحث المباشر
    setupLiveSearch();
});

/**
 * التحقق من صحة النماذج
 */
function validateForm(event) {
    const form = event.target;
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            isValid = false;
            showFieldError(field, 'هذا الحقل مطلوب');
        } else {
            clearFieldError(field);
            
            // التحقق من صحة البريد الإلكتروني
            if (field.type === 'email' && !validateEmail(field.value)) {
                isValid = false;
                showFieldError(field, 'يرجى إدخال بريد إلكتروني صحيح');
            }
            
            // التحقق من تطابق كلمات المرور
            if (field.id === 'confirm_password') {
                const password = form.querySelector('#password');
                if (password && field.value !== password.value) {
                    isValid = false;
                    showFieldError(field, 'كلمات المرور غير متطابقة');
                }
            }
        }
    });
    
    if (!isValid) {
        event.preventDefault();
    }
}

/**
 * عرض رسالة خطأ للحقل
 */
function showFieldError(field, message) {
    // إزالة أي رسائل خطأ سابقة
    clearFieldError(field);
    
    // إنشاء عنصر رسالة الخطأ
    const errorMessage = document.createElement('div');
    errorMessage.className = 'field-error';
    errorMessage.textContent = message;
    errorMessage.style.color = 'var(--danger-color)';
    errorMessage.style.fontSize = '14px';
    errorMessage.style.marginTop = '5px';
    
    // إضافة حدود حمراء للحقل
    field.style.borderColor = 'var(--danger-color)';
    
    // إضافة رسالة الخطأ بعد الحقل
    field.parentNode.appendChild(errorMessage);
}

/**
 * إزالة رسالة الخطأ من الحقل
 */
function clearFieldError(field) {
    // إعادة لون الحدود الافتراضي
    field.style.borderColor = '';
    
    // إزالة رسالة الخطأ إن وجدت
    const errorMessage = field.parentNode.querySelector('.field-error');
    if (errorMessage) {
        errorMessage.remove();
    }
}

/**
 * التحقق من صحة البريد الإلكتروني
 */
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * إعداد أزرار الكمية في سلة التسوق
 */
function setupQuantityButtons() {
    const decrementButtons = document.querySelectorAll('.quantity-decrement');
    const incrementButtons = document.querySelectorAll('.quantity-increment');
    
    if (decrementButtons.length > 0) {
        decrementButtons.forEach(button => {
            button.addEventListener('click', function() {
                const input = this.parentNode.querySelector('input');
                const currentValue = parseInt(input.value);
                if (currentValue > 1) {
                    input.value = currentValue - 1;
                    // تحديث السعر الإجمالي إن وجد
                    updateItemTotal(input);
                }
            });
        });
    }
    
    if (incrementButtons.length > 0) {
        incrementButtons.forEach(button => {
            button.addEventListener('click', function() {
                const input = this.parentNode.querySelector('input');
                const currentValue = parseInt(input.value);
                const maxStock = parseInt(input.getAttribute('data-max-stock') || '100');
                if (currentValue < maxStock) {
                    input.value = currentValue + 1;
                    // تحديث السعر الإجمالي إن وجد
                    updateItemTotal(input);
                }
            });
        });
    }
}

/**
 * تحديث السعر الإجمالي للمنتج في سلة التسوق
 */
function updateItemTotal(input) {
    const quantity = parseInt(input.value);
    const price = parseFloat(input.getAttribute('data-price'));
    const totalElement = input.closest('.cart-item').querySelector('.item-total');
    
    if (totalElement && !isNaN(quantity) && !isNaN(price)) {
        const total = quantity * price;
        totalElement.textContent = total.toFixed(2);
        
        // تحديث المجموع الكلي للسلة
        updateCartTotal();
    }
}

/**
 * تحديث المجموع الكلي لسلة التسوق
 */
function updateCartTotal() {
    const itemTotals = document.querySelectorAll('.item-total');
    let cartTotal = 0;
    
    itemTotals.forEach(item => {
        cartTotal += parseFloat(item.textContent);
    });
    
    const cartTotalElement = document.querySelector('.cart-total');
    if (cartTotalElement) {
        cartTotalElement.textContent = cartTotal.toFixed(2);
    }
}

/**
 * إعداد نظام التقييمات
 */
function setupRatingSystem() {
    const ratingInputs = document.querySelectorAll('.rating-input');
    const ratingStars = document.querySelectorAll('.rating-star');
    
    if (ratingStars.length > 0) {
        ratingStars.forEach(star => {
            star.addEventListener('click', function() {
                const value = this.getAttribute('data-value');
                const ratingInput = this.closest('.rating-container').querySelector('.rating-input');
                
                if (ratingInput) {
                    ratingInput.value = value;
                    
                    // تحديث العرض المرئي للنجوم
                    const stars = this.closest('.rating-container').querySelectorAll('.rating-star');
                    stars.forEach(s => {
                        if (parseInt(s.getAttribute('data-value')) <= parseInt(value)) {
                            s.classList.add('active');
                        } else {
                            s.classList.remove('active');
                        }
                    });
                }
            });
        });
    }
}

/**
 * إعداد البحث المباشر
 */
function setupLiveSearch() {
    const searchInput = document.querySelector('.search-input');
    const searchResults = document.querySelector('.search-results');
    
    if (searchInput && searchResults) {
        searchInput.addEventListener('input', debounce(function() {
            const query = this.value.trim();
            
            if (query.length < 2) {
                searchResults.innerHTML = '';
                searchResults.style.display = 'none';
                return;
            }
            
            // إرسال طلب البحث إلى الخادم
            fetch(`/api/products?search=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.length > 0) {
                        searchResults.innerHTML = '';
                        
                        // عرض أول 5 نتائج فقط
                        const maxResults = Math.min(data.length, 5);
                        for (let i = 0; i < maxResults; i++) {
                            const product = data[i];
                            const resultItem = document.createElement('div');
                            resultItem.className = 'search-result-item';
                            resultItem.innerHTML = `
                                <a href="/customer/products/${product.id}">
                                    <div class="search-result-image">
                                        <img src="${product.images.length > 0 ? product.images[0].image_path : '/static/img/no-image.jpg'}" alt="${product.name}">
                                    </div>
                                    <div class="search-result-info">
                                        <div class="search-result-name">${product.name}</div>
                                        <div class="search-result-price">${product.price} ريال</div>
                                    </div>
                                </a>
                            `;
                            searchResults.appendChild(resultItem);
                        }
                        
                        searchResults.style.display = 'block';
                    } else {
                        searchResults.innerHTML = '<div class="no-results">لا توجد نتائج</div>';
                        searchResults.style.display = 'block';
                    }
                })
                .catch(error => {
                    console.error('خطأ في البحث:', error);
                });
        }, 300));
        
        // إخفاء نتائج البحث عند النقر خارجها
        document.addEventListener('click', function(event) {
            if (!searchInput.contains(event.target) && !searchResults.contains(event.target)) {
                searchResults.style.display = 'none';
            }
        });
    }
}

/**
 * دالة لتأخير تنفيذ الوظائف (مفيدة للبحث المباشر)
 */
function debounce(func, delay) {
    let timeout;
    return function() {
        const context = this;
        const args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), delay);
    };
}

/**
 * عرض صورة المنتج المختارة في صفحة تفاصيل المنتج
 */
function showProductImage(imageUrl) {
    const mainImage = document.querySelector('.product-main-image img');
    if (mainImage) {
        mainImage.src = imageUrl;
    }
}

/**
 * تبديل بين علامات التبويب
 */
function switchTab(tabId, element) {
    // إخفاء جميع محتويات علامات التبويب
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => {
        content.style.display = 'none';
    });
    
    // إزالة الفئة النشطة من جميع علامات التبويب
    const tabLinks = document.querySelectorAll('.tab-link');
    tabLinks.forEach(link => {
        link.classList.remove('active');
    });
    
    // عرض المحتوى المطلوب وتنشيط علامة التبويب
    document.getElementById(tabId).style.display = 'block';
    element.classList.add('active');
}

/**
 * تأكيد الإجراءات الحساسة
 */
function confirmAction(message, formId) {
    if (confirm(message)) {
        document.getElementById(formId).submit();
    }
    return false;
}
