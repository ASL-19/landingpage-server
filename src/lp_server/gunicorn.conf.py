import os
import time


def post_worker_init(worker):
    path = "/metrics/"
    now = time.time()
    cleanup_delay = int(os.environ.get('CLEANUP_DELAY', default=7))

    for f in os.listdir(path):
        f = os.path.join(path, f)
        if os.path.getmtime(f) < now - cleanup_delay * 86400:
            os.remove(f)
