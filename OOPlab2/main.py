"""
Главный модуль программы для анализа CSV/XML файлов с адресами.
"""

import time
from file_analyzer import FileAnalyzer

class Application:
    """Основной класс приложения"""
    
    def run(self):
        """Основной цикл программы"""
        print("=" * 70)
        print("АНАЛИЗАТОР ФАЙЛОВ С АДРЕСАМИ")
        print("=" * 70)
        print("Поддерживаемые форматы: CSV (.csv) и XML (.xml)")
        print("Для выхода введите 'exit' или 'quit'")
        print("=" * 70)
        
        while True:
            try:
                # Получаем путь к файлу
                file_path = input("\nВведите путь к файлу (или 'exit' для выхода): ").strip()
                
                # Проверка на выход
                if file_path.lower() in ['exit', 'quit', 'выход']:
                    print("\nЗавершение работы программы...")
                    break
                
                if not file_path:
                    print("Путь не может быть пустым!")
                    continue
                
                # Измеряем время выполнения
                start_time = time.time()
                
                # Анализируем файл
                success = FileAnalyzer.analyze_file(file_path)
                
                end_time = time.time()
                
                if success:
                    elapsed_ms = (end_time - start_time) * 1000  # в миллисекундах
                    print(f"\nВремя обработки: {elapsed_ms:.2f} миллисекунд")
                
            except KeyboardInterrupt:
                print("\n\nПрограмма завершена пользователем.")
                break
            except Exception as e:
                print(f"\nНепредвиденная ошибка: {e}")

def main():
    """Точка входа в программу"""
    app = Application()
    app.run()

if __name__ == "__main__":
    main()