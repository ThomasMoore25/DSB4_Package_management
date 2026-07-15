#!/usr/bin/env python3
"""
librarian.py — Chapter VI, Exercise 02 (the program)

Цель:
- Проверить, что скрипт запущен в виртуальном окружении 'venv'.
- Установить beautifulsoup4 и pytest через временный requirements.txt.
- Вывести все пакеты в формате 'name==version'.
- Сохранить в requirements.txt.
- Создать архив окружения, если should_archive=True.
"""

import sys
import os
import subprocess
import tempfile
import tarfile


def get_venv_name():
    """Возвращает имя текущего виртуального окружения на основе пути к интерпретатору."""
    venv_root = os.path.dirname(os.path.dirname(sys.executable))
    return os.path.basename(venv_root)


def check_correct_env(expected_name):
    """
    Проверяет, что текущее виртуальное окружение имеет ожидаемое имя.
    
    Аргументы:
        expected_name (str): Ожидаемое имя окружения.
    
    Выбрасывает:
        RuntimeError — если имя не совпадает.
    """
    actual = get_venv_name()
    if actual != expected_name:
        raise RuntimeError(
            f"This script must be run inside virtual environment '{expected_name}', "
            f"but current environment is '{actual}'"
        )


def install_libraries():
    """Устанавливает beautifulsoup4 и pytest через временный requirements.txt."""
    req_content = "beautifulsoup4\npytest\n"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(req_content)
        req_path = f.name

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "-r", req_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Installation failed: {e.stderr.strip()}") from e
    finally:
        os.unlink(req_path)


def list_packages():
    """Возвращает список установленных пакетов в формате 'name==version'."""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list", "--format=freeze"],
        capture_output=True,
        text=True,
        check=True
    )
    packages = [line.strip() for line in result.stdout.splitlines() if '==' in line]
    return sorted(packages)


def save_requirements(packages):
    """Сохраняет список пакетов в requirements.txt."""
    with open("requirements.txt", "w") as f:
        for p in packages:
            f.write(p + "\n")


def archive_venv(should_archive=False):
    """
    Создаёт архив текущего виртуального окружения.
    
    Аргументы:
        should_archive (bool): Если True — создаётся archive.tar.gz в текущей директории.
    """
    if not should_archive:
        return

    venv_path = os.path.dirname(os.path.dirname(sys.executable))
    archive_name = "archive.tar.gz"

    print(f"Creating archive: {archive_name}", file=sys.stderr)
    with tarfile.open(archive_name, "w:gz") as tar:
        tar.add(venv_path, arcname="venv")


def main():
    """Основная точка входа скрипта."""
    try:
        # Проверка окружения с явно заданным именем
        check_correct_env("venv")
        
        # Установка библиотек
        install_libraries()
        
        # Получение и вывод списка пакетов
        packages = list_packages()
        for p in packages:
            print(p)
        
        # Сохранение зависимостей
        save_requirements(packages)
        
        # Архивация окружения (включено явно)
        archive_venv(should_archive=True)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()