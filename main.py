from app import create_app
from ai_scholar.config import AppConfig

app = create_app()

if __name__ == '__main__':
    app.run(debug=AppConfig.DEBUG, host=AppConfig.HOST, port=AppConfig.PORT)
