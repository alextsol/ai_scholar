from app import create_app
from ai_scholar.models import db
from sqlalchemy import text

def migrate_database():
    app = create_app()
    
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE users ADD COLUMN last_login DATETIME'))
                conn.commit()
        except Exception as e:
            pass
        
        try:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE users ADD COLUMN history_cleared_at DATETIME'))
                conn.commit()
        except Exception as e:
            pass
        
        try:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE search_history ADD COLUMN mode VARCHAR(20) DEFAULT "single"'))
                conn.commit()
        except Exception as e:
            pass
        
        try:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE search_history ADD COLUMN search_params TEXT'))
                conn.commit()
        except Exception as e:
            pass
        
        try:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE search_history ADD COLUMN results_html TEXT'))
                conn.commit()
        except Exception as e:
            pass

if __name__ == '__main__':
    migrate_database()
