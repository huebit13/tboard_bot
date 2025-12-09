from database.connection import engine, SessionLocal
from database.models import User, Game, Referral
from sqlalchemy import text

def test_connection():
    """Проверка подключения к БД"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            print("✅ PostgreSQL Connection successful!")
            print(f"Version: {result.fetchone()[0]}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")

def test_tables():
    """Проверка существования таблиц"""
    try:
        db = SessionLocal()
        
        # Проверка таблиц
        users_count = db.query(User).count()
        games_count = db.query(Game).count()
        referrals_count = db.query(Referral).count()
        
        print(f"\n✅ Tables exist!")
        print(f"Users: {users_count}")
        print(f"Games: {games_count}")
        print(f"Referrals: {referrals_count}")
        
        db.close()
    except Exception as e:
        print(f"❌ Tables check failed: {e}")

if __name__ == "__main__":
    test_connection()
    test_tables()