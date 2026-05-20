# Gunicorn production configuration
# Run with: gunicorn -c gunicorn.conf.py app:app

import os

# Workers: 2 × CPU cores + 1 is a good starting point
workers = int(os.getenv("WEB_CONCURRENCY", 3))
worker_class = "sync"
threads = 2

bind = f"0.0.0.0:{os.getenv('PORT', '8080')}"
timeout = 120
keepalive = 5

# Logging
accesslog = "-"       # stdout
errorlog = "-"        # stdout
loglevel = "info"
access_log_format = '%(h)s "%(r)s" %(s)s %(b)s %(D)sµs'

# Security
limit_request_line = 4096
limit_request_fields = 50
limit_request_field_size = 8190
