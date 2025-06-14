# filepath: backend/run.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Bind to 0.0.0.0 to make the app accessible on the LAN
    app.run(host='0.0.0.0', port=5000, debug=False)