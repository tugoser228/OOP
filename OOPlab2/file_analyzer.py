"""
Основной класс для анализа файлов.
"""

from typing import List, Optional
import time
from address import Address
from csv_reader import CSVReader
from xml_reader import XMLReader
from stats_calc import StatisticsCalculator

class FileAnalyzer:
    """Анализатор файлов с адресами"""
    
    @staticmethod
    def analyze_file(file_path: str) -> bool:
        """
        Анализирует файл (CSV или XML) и выводит статистику.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            bool: Успешно ли выполнен анализ
        """
        addresses: Optional[List[Address]] = None
        
        try:
            if file_path.lower().endswith('.csv'):
                print("\n" + "=" * 70)
                print("СЧИТЫВАНИЕ CSV ФАЙЛА")
                print("=" * 70)
                addresses = CSVReader.read_file(file_path)
                
            elif file_path.lower().endswith('.xml'):
                print("\n" + "=" * 70)
                print("СЧИТЫВАНИЕ XML ФАЙЛА")
                print("=" * 70)
                addresses = XMLReader.read_file(file_path)
                
            else:
                print(f"\nНеподдерживаемый формат файла: {file_path}")
                print("Поддерживаются только .csv и .xml файлы.")
                return False
            
            if not addresses:
                print("Файл пуст или не содержит корректных данных.")
                return False
            
            # Вычисляем статистику
            duplicates = StatisticsCalculator.find_duplicates(addresses)
            floor_stats = StatisticsCalculator.calculate_floor_stats(addresses)
            
            # Выводим результаты
            StatisticsCalculator.print_duplicates(duplicates)
            StatisticsCalculator.print_floor_stats(floor_stats)
            
            print(f"\nВсего записей в файле: {len(addresses)}")
            
            return True
            
        except Exception as e:
            print(f"\nОшибка при анализе файла: {e}")
            return False