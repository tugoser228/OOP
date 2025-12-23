#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
КОМПЛЕКТНАЯ ПРОГРАММА ДЛЯ ПОИСКА В ВИКИПЕДИИ
Все классы в одном файле для простого запуска
"""

import json
import urllib.parse
import urllib.request
import webbrowser
import re
from dataclasses import dataclass
from typing import List, Optional

# ========== DTO класс ==========
@dataclass
class SearchResult:
    """Класс для представления результата поиска"""
    title: str
    snippet: str
    pageid: int
    
    def get_url(self) -> str:
        """Генерирует URL статьи по pageid"""
        return f"https://ru.wikipedia.org/w/index.php?curid={self.pageid}"

# ========== QueryBuilder ==========
class QueryBuilder:
    """Строитель запросов к API Википедии"""
    
    BASE_URL = "https://ru.wikipedia.org/w/api.php"
    
    @staticmethod
    def build_search_url(query: str) -> str:
        """Строит URL для поискового запроса"""
        encoded_query = urllib.parse.quote(query, encoding='utf-8')
        params = {
            'action': 'query',
            'list': 'search',
            'srsearch': encoded_query,
            'format': 'json',
            'utf8': ''
        }
        query_string = '&'.join(f"{k}={v}" for k, v in params.items() if v != '')
        return f"{QueryBuilder.BASE_URL}?{query_string}"
    
    @staticmethod
    def build_article_url(pageid: int) -> str:
        """Строит URL статьи по её pageid"""
        return f"https://ru.wikipedia.org/w/index.php?curid={pageid}"

# ========== ApiClient ==========
class ApiClient:
    """Клиент для выполнения HTTP-запросов"""
    
    @staticmethod
    def execute_request(url: str) -> Optional[dict]:
        """Выполняет GET-запрос и возвращает JSON-данные"""
        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'WikipediaSearch/1.0'}
            )
            
            with urllib.request.urlopen(req) as response:
                if response.status == 200:
                    data = response.read()
                    return json.loads(data.decode('utf-8'))
                else:
                    print(f"Ошибка HTTP: {response.status}")
                    
        except urllib.error.URLError as e:
            print(f"Ошибка сети: {e.reason}")
        except Exception as e:
            print(f"Ошибка при запросе: {e}")
            
        return None

# ========== ResultParser ==========
class ResultParser:
    """Парсер JSON-ответов от API Википедии"""
    
    @staticmethod
    def parse_search_results(json_data: dict) -> List[SearchResult]:
        """Парсит JSON с результатами поиска"""
        results = []
        
        try:
            if not json_data or 'query' not in json_data:
                print("Некорректный ответ от API")
                return results
            
            query_data = json_data['query']
            if 'search' not in query_data:
                print("Результаты поиска отсутствуют")
                return results
            
            search_items = query_data['search']
            
            print(f"\n--- Результаты поиска ---")
            print(f"Найдено статей: {len(search_items)}")
            
            for index, item in enumerate(search_items, 1):
                title = item.get('title', 'Без названия')
                snippet = item.get('snippet', 'Без описания')
                pageid = item.get('pageid', 0)
                
                # Очистка HTML-тегов из snippet
                snippet_clean = re.sub(r'<[^>]+>', '', snippet)
                
                result = SearchResult(title, snippet_clean, pageid)
                results.append(result)
                
                print(f"\n{index}. Заголовок: {title}")
                print(f"   ID: {pageid}")
                print(f"   Описание: {snippet_clean[:150]}...")
                
        except Exception as e:
            print(f"Ошибка при обработке результатов: {e}")
        
        return results

# ========== BrowserOpener ==========
class BrowserOpener:
    """Класс для открытия URL в браузере"""
    
    @staticmethod
    def open_in_browser(url: str) -> bool:
        """Открывает URL в браузере по умолчанию"""
        try:
            webbrowser.open(url)
            return True
        except Exception as e:
            print(f"Не удалось открыть браузер: {e}")
            return False

# ========== WikipediaSearcher (главный класс) ==========
class WikipediaSearcher:
    """Основной класс приложения для поиска в Википедии"""
    
    def __init__(self):
        """Инициализация компонентов"""
        self.query_builder = QueryBuilder()
        self.api_client = ApiClient()
        self.result_parser = ResultParser()
        self.browser_opener = BrowserOpener()
    
    def run(self):
        """Основной цикл программы"""
        print("=" * 50)
        print("ПОИСК В ВИКИПЕДИИ")
        print("=" * 50)
        
        while True:
            try:
                # Шаг 1: Получение поискового запроса
                search_query = self._get_search_query()
                if not search_query:
                    continue
                
                # Шаг 2: Построение и выполнение запроса
                api_url = self.query_builder.build_search_url(search_query)
                print(f"\nЗапрос к Wikipedia:\n{api_url}")
                
                json_data = self.api_client.execute_request(api_url)
                if not json_data:
                    print("Не удалось получить данные.")
                    continue
                
                # Шаг 3: Парсинг и отображение результатов
                search_results = self.result_parser.parse_search_results(json_data)
                
                if not search_results:
                    print("Статьи не найдены.")
                    continue
                
                # Шаг 4: Выбор статьи
                self._handle_article_selection(search_results)
                
                # Новый поиск или выход
                if not self._ask_for_continue():
                    break
                    
            except KeyboardInterrupt:
                print("\n\nПрограмма завершена пользователем.")
                break
            except Exception as e:
                print(f"\nПроизошла ошибка: {e}")
                if not self._ask_for_continue():
                    break
    
    def _get_search_query(self) -> str:
        """Получает поисковый запрос от пользователя"""
        print("\n" + "-" * 50)
        query = input("Введите поисковый запрос (или 'exit' для выхода): ").strip()
        
        if query.lower() == 'exit':
            raise KeyboardInterrupt
        
        if not query:
            print("Запрос не может быть пустым!")
            return ""
        
        return query
    
    def _handle_article_selection(self, search_results):
        """Обрабатывает выбор статьи пользователем"""
        while True:
            try:
                print(f"\nВыберите номер статьи для открытия (1-{len(search_results)})")
                print("Или введите 0 для нового поиска")
                
                choice = input("Ваш выбор: ").strip()
                
                if choice == '0':
                    return
                
                if not choice.isdigit():
                    print("Пожалуйста, введите число.")
                    continue
                
                index = int(choice) - 1
                
                if 0 <= index < len(search_results):
                    result = search_results[index]
                    print(f"\nОткрываю статью: {result.title}")
                    self.browser_opener.open_in_browser(result.get_url())
                    
                    # Спросить, хочет ли пользователь открыть другую статью
                    if not self._ask_for_another_article():
                        return
                else:
                    print(f"Пожалуйста, введите число от 1 до {len(search_results)} или 0.")
                    
            except ValueError:
                print("Некорректный ввод. Попробуйте снова.")
    
    def _ask_for_continue(self) -> bool:
        """Спрашивает, хочет ли пользователь продолжить"""
        response = input("\nХотите выполнить новый поиск? (y/n): ").strip().lower()
        return response in ['y', 'yes', 'да', 'д']
    
    def _ask_for_another_article(self) -> bool:
        """Спрашивает, хочет ли пользователь открыть другую статью"""
        response = input("\nОткрыть другую статью из результатов? (y/n): ").strip().lower()
        return response in ['y', 'yes', 'да', 'д']

# ========== Точка входа ==========
def main():
    """Основная функция программы"""
    searcher = WikipediaSearcher()
    searcher.run()

if __name__ == "__main__":
    main()