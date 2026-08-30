import os
import shutil
import subprocess
import sys


SOURCE_DB = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "APS-01.db"
)

TARGET_DIR = "/var/data"
TARGET_DB = os.path.join(
    TARGET_DIR,
    "APS-01.db"
)


def initialize_database():
    os.makedirs(TARGET_DIR, exist_ok=True)

    if not os.path.exists(TARGET_DB):
        print("Initializing persistent SQLite database...")

        if not os.path.exists(SOURCE_DB):
            raise FileNotFoundError(
                f"Source database not found: {SOURCE_DB}"
            )

        shutil.copy2(
            SOURCE_DB,
            TARGET_DB
        )

        print(
            f"Database copied to {TARGET_DB}"
        )

    else:
        print(
            f"Persistent database already exists: {TARGET_DB}"
        )


if __name__ == "__main__":
    initialize_database()

    print("Starting FastAPI...")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            os.environ.get("PORT", "8000")
        ],
        check=True
    )