"""
سكريبت لتحديث قاعدة البيانات وإضافة الحقول الجديدة
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.main import app, db

def update_database():
    """تحديث هيكل قاعدة البيانات"""
    with app.app_context():
        db.create_all()
        print("تم تحديث قاعدة البيانات بنجاح!")

if __name__ == "__main__":
    update_database()
