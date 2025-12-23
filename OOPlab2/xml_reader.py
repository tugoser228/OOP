"""
Чтение и парсинг XML файлов.
"""

import xml.etree.ElementTree as ET
from typing import List
from address import Address

class XMLReader:
    """Читатель XML файлов"""
    
    @staticmethod
    def read_file(file_path: str) -> List[Address]:
        """
        Читает XML файл и возвращает список адресов.
        
        Args:
            file_path: Путь к XML файлу
            
        Returns:
            List[Address]: Список адресов
        """
        addresses = []
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            for item in root.findall('item'):
                address = Address(
                    city=item.get('city', '').strip(),
                    street=item.get('street', '').strip(),
                    house=item.get('house', '').strip(),
                    floor=item.get('floor', '').strip()
                )
                addresses.append(address)
                
        except FileNotFoundError:
            print(f"Файл не найден: {file_path}")
        except ET.ParseError as e:
            print(f"Ошибка парсинга XML: {e}")
        except Exception as e:
            print(f"Ошибка чтения XML: {e}")
        
        return addresses