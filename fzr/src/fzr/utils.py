from __future__ import annotations
import hashlib, json, os, uuid, time
from pathlib import Path
from contextlib import contextmanager

def sha1(obj):
    if isinstance(obj, (dict, list, tuple)):
        payload = json.dumps(obj, sort_keys=True, default=str).encode()
    elif isinstance(obj, bytes):
        payload = obj
    else:
        payload = str(obj).encode()
    return hashlib.sha1(payload).hexdigest()

@contextmanager
def file_lock(lock_path: Path):
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            break
        except FileExistsError:
            time.sleep(0.05)
    try:
        os.write(fd, str(uuid.uuid4()).encode())
        yield
    finally:
        try:
            os.close(fd)
        finally:
            try:
                os.remove(lock_path)
            except FileNotFoundError:
                pass
