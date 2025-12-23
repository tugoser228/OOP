"""
Вычисление статистики по адресам.
"""

from typing import List, Dict, Tuple
from collections import defaultdict
from address import Address

class StatisticsCalculator:
    """Калькулятор статистики"""
    
    @staticmethod
    def find_duplicates(addresses: List[Address]) -> Dict[str, int]:
        """
        Находит дубликаты адресов.
        
        Args:
            addresses: Список адресов
            
        Returns:
            Dict[str, int]: Словарь {ключ_адреса: количество_повторений}
        """
        building_counts = defaultdict(int)
        
        for address in addresses:
            key = address.to_key()
            building_counts[key] += 1
        
        # Возвращаем только дубликаты (count > 1)
        return {key: count for key, count in building_counts.items() if count > 1}
    
    @staticmethod
    def calculate_floor_stats(addresses: List[Address]) -> Dict[str, Dict[str, int]]:
        """
        Вычисляет статистику по этажам для каждого города.
        
        Args:
            addresses: Список адресов
            
        Returns:
            Dict[str, Dict[str, int]]: {город: {этаж: количество}}
        """
        floor_stats = defaultdict(lambda: defaultdict(int))
        
        for address in addresses:
            floor_stats[address.city][address.floor] += 1
        
        return floor_stats
    
    @staticmethod
    def print_duplicates(duplicates: Dict[str, int]):
        """Выводит дубликаты на экран"""
        print("\n" + "=" * 70)
        print("ДУБЛИРУЮЩИЕСЯ ЗАПИСИ")
        print("=" * 70)
        
        if not duplicates:
            print("Дубликатов не найдено.")
            return
        
        for key, count in duplicates.items():
            address = Address.from_key(key)
            print(f"Город: {address.city:<20} Улица: {address.street:<30} "
                  f"Дом: {address.house:<5} Этаж: {address.floor:<2} "
                  f"- повторяется {count} раз(а)")
    
    @staticmethod
    def print_floor_stats(floor_stats: Dict[str, Dict[str, int]]):
        """Выводит статистику по этажам"""
        print("\n" + "=" * 70)
        print("СТАТИСТИКА ЭТАЖЕЙ ПО ГОРОДАМ")
        print("=" * 70)
        
        if not floor_stats:
            print("Нет данных для отображения.")
            return
        
        for city, floors in sorted(floor_stats.items()):
            print(f"\nГород: {city}")
            print("-" * 40)
            
            for floor_num in range(1, 6):
                floor_str = str(floor_num)
                count = floors.get(floor_str, 0)
                print(f"{floor_num}-этажных зданий: {count}")