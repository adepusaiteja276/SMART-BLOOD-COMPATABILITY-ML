from CODE.app import app  # import your Flask app

def handler(request):
    return app(request)
