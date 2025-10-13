from app import app
from models import init_db

if __name__ == "__main__":
    with app.app_context():
        init_db(app)
