from waitress import serve
from payment_api.wsgi import application  # import your Django WSGI application

if __name__ == "__main__":
    serve(application, host="0.0.0.0", port=8000)