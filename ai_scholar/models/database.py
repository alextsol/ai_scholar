from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    history_cleared_at = db.Column(db.DateTime)
    
    searches = db.relationship('SearchHistory', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def clear_search_history(self):
        db.session.query(SearchHistory).filter_by(user_id=self.id).delete()
        self.history_cleared_at = datetime.utcnow()
        db.session.commit()
    
    def get_recent_searches(self, limit=10):
        return db.session.query(SearchHistory).filter_by(user_id=self.id)\
            .order_by(SearchHistory.created_at.desc())\
            .limit(limit).all()
    
    def __repr__(self):
        return f'<User {self.username}>'

class SearchHistory(db.Model):
    __tablename__ = 'search_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    query = db.Column(db.String(500), nullable=False)
    backend = db.Column(db.String(50), nullable=False)
    mode = db.Column(db.String(20), default='single')
    results_count = db.Column(db.Integer, default=0)
    search_params = db.Column(db.Text)
    results_html = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'query': self.query,
            'backend': self.backend,
            'mode': self.mode,
            'results_count': self.results_count,
            'created_at': self.created_at.isoformat(),
            'search_params': self.search_params,
            'results_html': self.results_html
        }
    
    def __repr__(self):
        return f'<SearchHistory {self.query} by User {self.user_id}>'
