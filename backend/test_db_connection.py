"""
Test database connection to PostgreSQL
"""

import os
import sys
from sqlalchemy import create_engine, text

# Test connection
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:1q2w3e4r98476309Jr*@10.110.0.3:5432/postgres')

try:
    print("🔄 Testing PostgreSQL connection...")
    print(f"Database URL: {DATABASE_URL.replace('1q2w3e4r98476309Jr*', '***')}")
    
    engine = create_engine(DATABASE_URL, echo=False)
    
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print(f"✅ PostgreSQL connection successful!")
        print(f"Database version: {version}")
        
    print("🎯 Database connection test completed successfully!")
    
except Exception as e:
    print(f"❌ Database connection failed: {str(e)}")
    sys.exit(1)