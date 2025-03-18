from flask import Flask
from endpoints import bp as main_bp

app = Flask(__name__)
app.secret_key = "SECRET_KEY"  # Use your secret key from config
app.register_blueprint(main_bp)

if __name__ == '__main__':
    app.run(debug=True)
