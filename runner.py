import os
import subprocess
import threading

import uvicorn
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def health():
    return {"status": "ok"}


def start_worker(queue_name):
    cmd = [
        "celery",
        "-A",
        "src.workers.celery_app",
        "worker",
        "-Q",
        queue_name,
        "-l",
        "info",
        "-n",
        f"{queue_name}@%h",
    ]
    subprocess.run(cmd)


def start_beat():
    cmd = [
        "celery",
        "-A",
        "src.workers.celery_app",
        "beat",
        "-l",
        "info",
    ]
    subprocess.run(cmd)


if __name__ == "__main__":
    service_type = os.getenv("SERVICE_TYPE")

    if service_type == "watcher" or service_type == "processor":
        threading.Thread(
            target=start_worker,
            args=(os.getenv("QUEUE_NAME"),),
            daemon=True,
        ).start()

    elif service_type == "beat":
        threading.Thread(target=start_beat, daemon=True).start()

    # 🔥 THIS IS WHAT CLOUD RUN NEEDS
    uvicorn.run(app, host="0.0.0.0", port=8080)
