"""
Чтение и парсинг CSV файлов.
"""

import csv
from typing import List
from address import Address

class CSVReader:
    """Читатель CSV файлов"""
    
    @staticmethod
    def read_file(file_path: str) -> List[Address]:
        """
        Читает CSV файл и возвращает список адресов.
        
        Args:
            file_path: Путь к CSV файлу
            
        Returns:
            List[Address]: Список адресов
        """
        addresses = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file, delimiter=';')
                
                for row in reader:
                    address = Address(
                        city=row['city'].strip(),
                        street=row['street'].strip(),
                        house=row['house'].strip(),
                        floor=row['floor'].strip()
                    )
                    addresses.append(address)
                    
        except FileNotFoundError:
            print(f"Файл не найден: {file_path}")
        except Exception as e:
            print(f"Ошибка чтения CSV: {e}")
        
        return addresses