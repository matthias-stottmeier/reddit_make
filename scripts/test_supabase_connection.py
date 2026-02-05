"""
Test Supabase connection
Usage: SUPABASE_URL="your-connection-string" python scripts/test_supabase_connection.py
"""
import os
import sys
from urllib.parse import urlparse

SUPABASE_URL = os.getenv("SUPABASE_URL")

if not SUPABASE_URL:
    print("❌ Error: SUPABASE_URL environment variable not set!")
    sys.exit(1)

# Parse and validate URL
parsed = urlparse(SUPABASE_URL)
print(f"📋 Connection details:")
print(f"   Host: {parsed.hostname}")
print(f"   Port: {parsed.port}")
print(f"   Database: {parsed.path.lstrip('/')}")
print(f"   User: {parsed.username}")
print(f"   Password: {'*' * len(parsed.password) if parsed.password else 'NOT SET'}")

# Test DNS resolution
import socket
print(f"\n🔍 Testing DNS resolution for {parsed.hostname}...")
try:
    ip = socket.gethostbyname(parsed.hostname)
    print(f"   ✅ Resolved to: {ip}")
except socket.gaierror as e:
    print(f"   ❌ DNS resolution failed: {e}")
    print("\n💡 Possible causes:")
    print("   1. Typo in project reference ID")
    print("   2. Project was just created - wait a few minutes")
    print("   3. Project is paused in Supabase dashboard")
    print("   4. Network/firewall blocking DNS")
    print("\n📝 Check your Supabase dashboard at https://supabase.com/dashboard")
    print("   Go to: Project Settings → Database → Connection string")
    sys.exit(1)

# Test database connection
print("\n🔌 Testing database connection...")
try:
    from sqlalchemy import create_engine, text
    engine = create_engine(SUPABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("   ✅ Connected successfully!")

        # Check if tables exist
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """))
        tables = [row[0] for row in result]
        if tables:
            print(f"   📦 Existing tables: {', '.join(tables)}")
        else:
            print("   📦 No tables yet (fresh database)")

except Exception as e:
    print(f"   ❌ Connection failed: {e}")
    sys.exit(1)

print("\n✅ All tests passed! Ready for migration.")
