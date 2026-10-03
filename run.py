import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    debug = os.getenv("APP_ENV", "development").lower() == "development"
    app.run(debug=debug)
