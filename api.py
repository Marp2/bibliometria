"""Punto de entrada local:  python api.py   ->  http://127.0.0.1:8000/"""
import os

from src.api import app

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "0") == "1"
    print("Servidor local: http://127.0.0.1:%d/" % port)
    app.run(debug=debug, host=host, port=port, use_reloader=False)
