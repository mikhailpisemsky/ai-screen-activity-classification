import os
import sys
import platform
import subprocess
import shutil
import zipfile
import tarfile
from pathlib import Path
import urllib.request
import tempfile
import stat

class TesseractInstaller:
    
    def __init__(self, vendor_dir: str = None):
        if vendor_dir is None:
            # Определяем путь относительно текущего файла
            current_dir = Path(__file__).parent
            self.vendor_dir = current_dir.parent / 'vendor' / 'tesseract'
        else:
            self.vendor_dir = Path(vendor_dir)
        
        self.os_name = platform.system().lower()
        self.arch = platform.machine().lower()
        
        # URL для загрузки Tesseract
        self.download_urls = {
            'windows': {
                'x86_64': 'https://github.com/UB-Mannheim/tesseract/wiki',
                'alternative': 'https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.1.20230401.exe'
            },
            'linux': {
                'instructions': 'https://github.com/tesseract-ocr/tesseract',
                'packages': {
                    'apt': ['tesseract-ocr', 'tesseract-ocr-rus', 'tesseract-ocr-eng'],
                    'yum': ['tesseract', 'tesseract-langpack-rus', 'tesseract-langpack-eng']
                }
            }
        }
        
        print(f"ОС: {self.os_name}")
        print(f"Архитектура: {self.arch}")
        print(f"Каталог установки: {self.vendor_dir}")
    
    def install_windows(self) -> bool:
        print("\n=== Установка Tesseract для Windows ===")
        
        # Создаем каталоги
        windows_dir = self.vendor_dir / 'windows'
        windows_dir.mkdir(parents=True, exist_ok=True)
        
        print("1. Проверка существующей установки...")
        
        # Проверяем, есть ли уже установленный Tesseract в системе
        system_tesseract = self._find_system_tesseract_windows()
        if system_tesseract:
            print(f"   Найден системный Tesseract: {system_tesseract}")
            choice = input("   Использовать системный Tesseract? (y/n): ").lower()
            if choice == 'y':
                return self._copy_system_tesseract_windows(system_tesseract, windows_dir)
        
        print("2. Загрузка установщика...")
        print(f"   Для Windows необходимо скачать Tesseract с официального сайта:")
        print(f"   {self.download_urls['windows']['alternative']}")
        print("   или с GitHub: https://github.com/UB-Mannheim/tesseract/wiki")
        print("\n3. Инструкция по установке:")
        print("   а) Скачайте установщик tesseract-ocr-w64-setup-*.exe")
        print("   б) Запустите установщик")
        print("   в) Выберите путь установки: {}".format(windows_dir))
        print("   г) Отметьте установку русского и английского языков")
        print("   д) Завершите установку")
        
        # Проверяем, установлен ли Tesseract
        tesseract_exe = windows_dir / 'tesseract.exe'
        if tesseract_exe.exists():
            print(f"\n✓ Tesseract найден в {tesseract_exe}")
            return True
        else:
            print("\n✗ Tesseract не найден. Установите его вручную.")
            print(f"   Ожидаемый путь: {tesseract_exe}")
            return False
    
    def install_linux(self) -> bool:
        print("\n=== Установка Tesseract для Linux ===")
        
        # Создаем каталоги
        linux_dir = self.vendor_dir / 'linux'
        linux_dir.mkdir(parents=True, exist_ok=True)
        
        print("1. Проверка существующего Tesseract...")
        
        # Проверяем, установлен ли Tesseract в системе
        try:
            result = subprocess.run(['which', 'tesseract'], 
                                   capture_output=True, text=True)
            if result.returncode == 0:
                system_path = result.stdout.strip()
                print(f"   Найден системный Tesseract: {system_path}")
                
                # Копируем бинарные файлы
                return self._setup_linux_from_system(linux_dir)
        except Exception as e:
            print(f"   Ошибка при проверке системного Tesseract: {e}")
        
        print("2. Установка через пакетный менеджер...")
        print("   Определяем менеджер пакетов...")
        
        # Определяем менеджер пакетов
        package_manager = self._detect_package_manager()
        
        if package_manager == 'apt':
            return self._install_with_apt(linux_dir)
        elif package_manager == 'yum' or package_manager == 'dnf':
            return self._install_with_yum(linux_dir)
        else:
            print("   Неизвестный менеджер пакетов")
            return self._install_from_source(linux_dir)
    
    def _find_system_tesseract_windows(self) -> str:
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            os.path.join(os.environ.get('PROGRAMFILES', ''), 'Tesseract-OCR', 'tesseract.exe'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Tesseract-OCR', 'tesseract.exe'),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Проверяем PATH
        try:
            result = subprocess.run(['where', 'tesseract'], 
                                   capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except:
            pass
        
        return ''
    
    def _copy_system_tesseract_windows(self, source_path: str, target_dir: Path) -> bool:
        try:
            print(f"   Копирование из {source_path} в {target_dir}")
            
            # Создаем целевой каталог
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Определяем корневую директорию Tesseract
            source_dir = Path(source_path).parent
            
            # Копируем основные файлы
            for item in source_dir.iterdir():
                if item.is_file():
                    shutil.copy2(item, target_dir / item.name)
                    print(f"     Скопирован: {item.name}")
                elif item.is_dir() and item.name != 'tessdata':
                    # Копируем поддиректории (кроме tessdata, которую скопируем отдельно)
                    target_subdir = target_dir / item.name
                    shutil.copytree(item, target_subdir, dirs_exist_ok=True)
                    print(f"     Скопирована директория: {item.name}")
            
            # Копируем tessdata
            tessdata_source = source_dir / 'tessdata'
            tessdata_target = target_dir / 'tessdata'
            if tessdata_source.exists():
                shutil.copytree(tessdata_source, tessdata_target, dirs_exist_ok=True)
                print(f"     Скопирована tessdata")
            
            # Проверяем успешность
            tesseract_exe = target_dir / 'tesseract.exe'
            if tesseract_exe.exists():
                print(f"\n✓ Tesseract успешно скопирован в {target_dir}")
                return True
            else:
                print(f"\n✗ Ошибка: tesseract.exe не найден после копирования")
                return False
                
        except Exception as e:
            print(f"\n✗ Ошибка при копировании: {e}")
            return False
    
    def _detect_package_manager(self) -> str:
        """Определение менеджера пакетов"""
        try:
            # Проверяем apt (Debian/Ubuntu/Astra Linux)
            result = subprocess.run(['which', 'apt-get'], 
                                   capture_output=True, text=True)
            if result.returncode == 0:
                return 'apt'
            
            # Проверяем yum (RHEL/CentOS)
            result = subprocess.run(['which', 'yum'], 
                                   capture_output=True, text=True)
            if result.returncode == 0:
                return 'yum'
            
            # Проверяем dnf (Fedora)
            result = subprocess.run(['which', 'dnf'], 
                                   capture_output=True, text=True)
            if result.returncode == 0:
                return 'dnf'
        except:
            pass
        
        return 'unknown'
    
    def _setup_linux_from_system(self, target_dir: Path) -> bool:
        try:
            # Создаем структуру каталогов
            bin_dir = target_dir / 'bin'
            lib_dir = target_dir / 'lib'
            bin_dir.mkdir(parents=True, exist_ok=True)
            lib_dir.mkdir(parents=True, exist_ok=True)
            
            # Получаем путь к Tesseract
            tesseract_path = subprocess.run(['which', 'tesseract'], 
                                          capture_output=True, text=True).stdout.strip()
            
            if not tesseract_path:
                print("   Tesseract не найден в системе")
                return False
            
            # Создаем симлинк на бинарник
            target_bin = bin_dir / 'tesseract'
            if target_bin.exists() or target_bin.is_symlink():
                target_bin.unlink()
            
            os.symlink(tesseract_path, target_bin)
            print(f"   Создан симлинк: {target_bin} -> {tesseract_path}")
            
            # Получаем библиотеки Tesseract
            ldd_result = subprocess.run(['ldd', tesseract_path], 
                                      capture_output=True, text=True)
            
            if ldd_result.returncode == 0:
                # Анализируем вывод ldd для поиска библиотек Tesseract
                for line in ldd_result.stdout.split('\n'):
                    if 'libtesseract' in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            lib_path = parts[2]
                            if os.path.exists(lib_path):
                                lib_name = os.path.basename(lib_path)
                                target_lib = lib_dir / lib_name
                                
                                if target_lib.exists() or target_lib.is_symlink():
                                    target_lib.unlink()
                                
                                os.symlink(lib_path, target_lib)
                                print(f"   Создан симлинк библиотеки: {target_lib}")
            
            # Создаем скрипт-обертку для настройки LD_LIBRARY_PATH
            wrapper_script = target_dir / 'run_tesseract.sh'
            with open(wrapper_script, 'w') as f:
                f.write(f"""#!/bin/bash
export LD_LIBRARY_PATH="{lib_dir.absolute()}:$LD_LIBRARY_PATH"
exec "{bin_dir.absolute()}/tesseract" "$@"
""")
            
            # Делаем скрипт исполняемым
            wrapper_script.chmod(wrapper_script.stat().st_mode | stat.S_IEXEC)
            
            print(f"   Создан скрипт-обертка: {wrapper_script}")
            print(f"\n✓ Настройка завершена. Используйте: {wrapper_script}")
            return True
            
        except Exception as e:
            print(f"\n✗ Ошибка при настройке: {e}")
            return False
    
    def _install_with_apt(self, target_dir: Path) -> bool:
        print("   Используем apt для установки Tesseract")
        
        try:
            # Обновляем список пакетов
            print("   Обновление списка пакетов...")
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            
            # Устанавливаем Tesseract и языковые пакеты
            packages = self.download_urls['linux']['packages']['apt']
            print(f"   Установка пакетов: {', '.join(packages)}")
            
            subprocess.run(['sudo', 'apt-get', 'install', '-y'] + packages, check=True)
            
            # После установки настраиваем симлинки
            return self._setup_linux_from_system(target_dir)
            
        except subprocess.CalledProcessError as e:
            print(f"   Ошибка при установке через apt: {e}")
            return False
        except Exception as e:
            print(f"   Неожиданная ошибка: {e}")
            return False
    
    def _install_with_yum(self, target_dir: Path) -> bool:
        package_manager = 'yum' if shutil.which('yum') else 'dnf'
        print(f"   Используем {package_manager} для установки Tesseract")
        
        try:
            packages = self.download_urls['linux']['packages']['yum']
            print(f"   Установка пакетов: {', '.join(packages)}")
            
            subprocess.run(['sudo', package_manager, 'install', '-y'] + packages, check=True)
            
            # После установки настраиваем симлинки
            return self._setup_linux_from_system(target_dir)
            
        except subprocess.CalledProcessError as e:
            print(f"   Ошибка при установке через {package_manager}: {e}")
            return False
    
    def _install_from_source(self, target_dir: Path) -> bool:
        print("   Установка из исходного кода...")
        print("   Эта операция требует установленных компиляторов и зависимостей.")
        
        try:
            # Создаем временный каталог для сборки
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                print("   1. Установка зависимостей для сборки...")
                
                # Устанавливаем зависимости для сборки
                try:
                    if shutil.which('apt-get'):
                        deps = [
                            'autoconf', 'automake', 'libtool', 
                            'pkg-config', 'libpng-dev', 'libjpeg-dev', 
                            'libtiff-dev', 'zlib1g-dev', 'g++', 'make'
                        ]
                        subprocess.run(['sudo', 'apt-get', 'install', '-y'] + deps, 
                                     capture_output=True)
                    elif shutil.which('yum') or shutil.which('dnf'):
                        deps = [
                            'autoconf', 'automake', 'libtool', 
                            'pkgconfig', 'libpng-devel', 'libjpeg-devel', 
                            'libtiff-devel', 'zlib-devel', 'gcc-c++', 'make'
                        ]
                        pm = 'yum' if shutil.which('yum') else 'dnf'
                        subprocess.run(['sudo', pm, 'install', '-y'] + deps, 
                                     capture_output=True)
                except:
                    print("     Предупреждение: не удалось установить зависимости")
                
                print("   2. Скачивание и сборка Leptonica...")
                
                # Скачиваем и собираем Leptonica (зависимость Tesseract)
                leptonica_url = "https://github.com/DanBloomberg/leptonica/releases/download/1.83.1/leptonica-1.83.1.tar.gz"
                leptonica_tar = temp_path / "leptonica.tar.gz"
                
                # Скачиваем
                urllib.request.urlretrieve(leptonica_url, leptonica_tar)
                
                # Распаковываем
                with tarfile.open(leptonica_tar, 'r:gz') as tar:
                    tar.extractall(temp_path)
                
                leptonica_dir = temp_path / "leptonica-1.83.1"
                
                # Собираем
                subprocess.run([
                    './configure', f'--prefix={target_dir.absolute()}',
                    '--disable-dependency-tracking'
                ], cwd=leptonica_dir, capture_output=True)
                
                subprocess.run(['make'], cwd=leptonica_dir, capture_output=True)
                subprocess.run(['sudo', 'make', 'install'], cwd=leptonica_dir, capture_output=True)
                
                print("   3. Скачивание и сборка Tesseract...")
                
                # Скачиваем Tesseract
                tesseract_url = "https://github.com/tesseract-ocr/tesseract/archive/refs/tags/5.3.1.tar.gz"
                tesseract_tar = temp_path / "tesseract.tar.gz"
                
                urllib.request.urlretrieve(tesseract_url, tesseract_tar)
                
                # Распаковываем
                with tarfile.open(tesseract_tar, 'r:gz') as tar:
                    tar.extractall(temp_path)
                
                tesseract_dir = temp_path / "tesseract-5.3.1"
                
                # Собираем
                env = os.environ.copy()
                env['LIBLEPT_HEADERSDIR'] = str(target_dir.absolute() / 'include')
                env['PKG_CONFIG_PATH'] = f"{target_dir.absolute()}/lib/pkgconfig"
                
                subprocess.run([
                    './autogen.sh'
                ], cwd=tesseract_dir, env=env, capture_output=True)
                
                subprocess.run([
                    './configure', f'--prefix={target_dir.absolute()}',
                    '--disable-dependency-tracking',
                    '--with-extra-libraries=' + str(target_dir.absolute() / 'lib')
                ], cwd=tesseract_dir, env=env, capture_output=True)
                
                subprocess.run(['make'], cwd=tesseract_dir, env=env, capture_output=True)
                subprocess.run(['sudo', 'make', 'install'], cwd=tesseract_dir, env=env, capture_output=True)
                
                print("   4. Установка языковых данных...")
                
                # Создаем каталог для языковых данных
                tessdata_dir = target_dir / 'share' / 'tessdata'
                tessdata_dir.mkdir(parents=True, exist_ok=True)
                
                # Скачиваем русский и английский языки
                lang_urls = [
                    "https://github.com/tesseract-ocr/tessdata/raw/main/rus.traineddata",
                    "https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata"
                ]
                
                for url in lang_urls:
                    lang_file = url.split('/')[-1]
                    lang_path = tessdata_dir / lang_file
                    urllib.request.urlretrieve(url, lang_path)
                    print(f"     Установлен язык: {lang_file}")
                
                # Создаем скрипт-обертку
                wrapper_script = target_dir / 'run_tesseract.sh'
                with open(wrapper_script, 'w') as f:
                    f.write(f"""#!/bin/bash
export TESSDATA_PREFIX="{tessdata_dir.parent.absolute()}"
export LD_LIBRARY_PATH="{target_dir.absolute()}/lib:$LD_LIBRARY_PATH"
exec "{target_dir.absolute()}/bin/tesseract" "$@"
""")
                
                wrapper_script.chmod(wrapper_script.stat().st_mode | stat.S_IEXEC)
                
                print(f"\n✓ Tesseract успешно установлен из исходного кода")
                print(f"  Используйте: {wrapper_script}")
                return True
                
        except Exception as e:
            print(f"\n✗ Ошибка при установке из исходного кода: {e}")
            return False
    
    def verify_installation(self) -> bool:
        print("\n=== Проверка установки ===")
        
        # Определяем путь к Tesseract в зависимости от ОС
        if self.os_name == 'windows':
            tesseract_path = self.vendor_dir / 'windows' / 'tesseract.exe'
        else:
            tesseract_path = self.vendor_dir / 'linux' / 'bin' / 'tesseract'
        
        if tesseract_path.exists():
            print(f"✓ Tesseract найден: {tesseract_path}")
            
            # Проверяем версию
            try:
                if self.os_name == 'windows':
                    result = subprocess.run([str(tesseract_path), '--version'], 
                                          capture_output=True, text=True, shell=True)
                else:
                    # Для Linux может потребоваться скрипт-обертка
                    run_script = self.vendor_dir / 'linux' / 'run_tesseract.sh'
                    if run_script.exists():
                        result = subprocess.run([str(run_script), '--version'], 
                                              capture_output=True, text=True)
                    else:
                        result = subprocess.run([str(tesseract_path), '--version'], 
                                              capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"  Версия: {result.stdout.split()[1]}")
                    return True
                else:
                    print(f"✗ Не удалось получить версию: {result.stderr}")
                    return False
                    
            except Exception as e:
                print(f"✗ Ошибка при проверке версии: {e}")
                return False
        else:
            print(f"✗ Tesseract не найден по пути: {tesseract_path}")
            
            # Проверяем системный Tesseract
            try:
                result = subprocess.run(['tesseract', '--version'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✓ Найден системный Tesseract: {result.stdout.split()[1]}")
                    print("  Модель будет использовать системный Tesseract")
                    return True
            except:
                pass
            
            return False
    
    def install(self) -> bool:
        print(f"\n{'='*60}")
        print("Установка Tesseract OCR в локальный каталог")
        print(f"{'='*60}")
        
        # Выполняем установку в зависимости от ОС
        if self.os_name == 'windows':
            success = self.install_windows()
        elif self.os_name == 'linux':
            success = self.install_linux()
        else:
            print(f"✗ Неподдерживаемая ОС: {self.os_name}")
            return False
        
        # Проверяем установку
        if success:
            print(f"\n{'='*60}")
            print("Проверка установки...")
            verified = self.verify_installation()
            
            if verified:
                print(f"\n{'='*60}")
                print("✓ Установка Tesseract завершена успешно!")
                print(f"  Каталог: {self.vendor_dir}")
                return True
            else:
                print(f"\n{'='*60}")
                print("⚠ Установка завершена с предупреждениями")
                print("  Модель может использовать системный Tesseract")
                return True
        else:
            print(f"\n{'='*60}")
            print("✗ Установка Tesseract не удалась")
            print("  Установите Tesseract вручную или проверьте системный Tesseract")
            return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Установка Tesseract OCR в локальный каталог')
    parser.add_argument('--vendor-dir', type=str, help='Каталог для установки')
    parser.add_argument('--verify-only', action='store_true', help='Только проверка установки')
    
    args = parser.parse_args()
    
    installer = TesseractInstaller(args.vendor_dir)
    
    if args.verify_only:
        installer.verify_installation()
    else:
        installer.install()

if __name__ == "__main__":
    main()
