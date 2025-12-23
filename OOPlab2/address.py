"""
Класс для представления адреса.
"""

from dataclasses import dataclass

@dataclass(frozen=True, eq=True)
class Address:
    """Неизменяемый класс адреса (для использования в словарях)"""
    city: str
    street: str
    house: str
    floor: str
    
    def to_key(self) -> str:
        """Создает ключ для группировки"""
        return f"{self.city}|{self.street}|{self.house}|{self.floor}"
    
    @classmethod
    def from_key(cls, key: str) -> 'Address':
        """Создает Address из ключа"""
        parts = key.split('|')
        return cls(
            city=parts[0],
            street=parts[1],
            house=parts[2],
            floor=parts[3]
        )
    
    def __str__(self) -> str:
        return f"{self.city}, {self.street}, д.{self.house}, эт.{self.floor}"