import asyncio
import uvicorn
import multiprocessing
import subprocess
import sys
import os
from admin.main import app as admin_app
from bot import run as run_bot

def run_admin():
    """Запускает FastAPI админ-сервер"""
    uvicorn.run(admin_app, host="0.0.0.0", port=8000)

def run_frontend():
    """Запускает React фронтенд"""
    os.chdir('admin-frontend')
    subprocess.run(['npm', 'start'], check=True)

def main():
    # Запускаем админ-сервер в отдельном процессе
    admin_process = multiprocessing.Process(target=run_admin)
    admin_process.start()

    # Запускаем фронтенд в отдельном процессе
    frontend_process = multiprocessing.Process(target=run_frontend)
    frontend_process.start()

    try:
        # Запускаем бота в основном процессе
        if sys.platform != "win32":
            import uvloop
            uvloop.install()
        run_bot()
    except KeyboardInterrupt:
        print("\nЗавершение работы...")
    finally:
        # Завершаем все процессы
        admin_process.terminate()
        frontend_process.terminate()
        admin_process.join()
        frontend_process.join()

if __name__ == "__main__":
    main() 