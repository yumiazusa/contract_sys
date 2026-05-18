import os


bind = os.getenv('GUNICORN_BIND', '0.0.0.0:5600')
workers = int(os.getenv('GUNICORN_WORKERS', '2'))
threads = int(os.getenv('GUNICORN_THREADS', '2'))
worker_class = 'gthread'
timeout = int(os.getenv('GUNICORN_TIMEOUT', '120'))
graceful_timeout = int(os.getenv('GUNICORN_GRACEFUL_TIMEOUT', '30'))
keepalive = int(os.getenv('GUNICORN_KEEPALIVE', '5'))
max_requests = int(os.getenv('GUNICORN_MAX_REQUESTS', '600'))
max_requests_jitter = int(os.getenv('GUNICORN_MAX_REQUESTS_JITTER', '60'))
preload_app = False
accesslog = '-'
errorlog = '-'
capture_output = True
