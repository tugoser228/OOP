import requests
import json
from datetime import datetime
from typing import Optional, Dict, List

class LETIScheduleAPI:
    """Класс для работы с API расписания ЛЭТИ"""
    
    BASE_URL = "https://digital.etu.ru/api/mobile"
    
    @staticmethod
    def get_group_schedule(
        group_number: str,
        week_type: Optional[str] = None,
        day: Optional[str] = None
    ) -> Dict:
        """
        Получить расписание группы
        
        Args:
            group_number: номер группы (например '4352')
            week_type: тип недели ('1' - нечетная, '2' - четная)
            day: номер дня (0-понедельник, 1-вторник, ...) или название
        """
        try:
            # 1. Получаем все данные
            url = f"{LETIScheduleAPI.BASE_URL}/schedule"
            response = requests.get(url, timeout=15, verify=False)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Ошибка API: {response.status_code}"
                }
            
            all_data = response.json()
            
            # 2. Ищем нашу группу
            if group_number not in all_data:
                return {
                    "success": False,
                    "error": f"Группа {group_number} не найдена"
                }
            
            group_data = all_data[group_number]
            
            # 3. Извлекаем занятия из структуры days
            all_lessons = []
            days_data = group_data.get("days", {})
            
            # Преобразуем дни из словаря в список
            for day_num, day_info in days_data.items():
                day_name = day_info.get("name", "").strip().lower()
                lessons = day_info.get("lessons", [])
                
                # Добавляем информацию о дне к каждому занятию
                for lesson in lessons:
                    lesson_with_day = lesson.copy()
                    lesson_with_day["day_number"] = day_num
                    lesson_with_day["day_name"] = day_name
                    all_lessons.append(lesson_with_day)
            
            print(f"📊 Всего занятий для группы {group_number}: {len(all_lessons)}")
            
            # 4. Фильтруем по неделе и дню
            filtered_lessons = []
            
            for lesson in all_lessons:
                # Проверяем неделю (week: "1" или "2")
                lesson_week = lesson.get("week", "")
                week_match = True
                
                if week_type:
                    # Приводим к формату API ("1"/"2")
                    if week_type.lower() in ["odd", "нечетная", "odd_week", "1"]:
                        target_week = "1"
                    elif week_type.lower() in ["even", "четная", "even_week", "2"]:
                        target_week = "2"
                    else:
                        target_week = week_type
                    
                    week_match = (lesson_week == target_week)
                
                # Проверяем день
                day_match = True
                if day:
                    # День может быть: числом (0-6), названием на рус/англ
                    lesson_day_num = lesson.get("day_number", "")
                    lesson_day_name = lesson.get("day_name", "")
                    
                    day_str = str(day).lower().strip()
                    
                    # Проверяем совпадение
                    if day_str in ["0", "1", "2", "3", "4", "5", "6"]:
                        # Ищем по номеру дня
                        day_match = (lesson_day_num == day_str)
                    else:
                        # Ищем по названию
                        day_match = (lesson_day_name == day_str)
                
                if week_match and day_match:
                    filtered_lessons.append(lesson)
            
            return {
                "success": True,
                "group": group_number,
                "week_type": week_type,
                "day": day,
                "lessons": filtered_lessons,
                "total_lessons": len(filtered_lessons),
                "all_lessons_count": len(all_lessons)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Ошибка: {str(e)}"
            }
    
    @staticmethod
    def determine_current_week() -> str:
        """
        Определить текущую учебную неделю
        Возвращает: '1' - нечетная неделя, '2' - четная неделя
        """
        # Начало осеннего семестра 2024-2025
        # 2 сентября 2024 - понедельник, НЕЧЕТНАЯ неделя (1)
        SEMESTER_START = datetime(2024, 9, 2)
        
        today = datetime.now()
        
        # Вычисляем разницу в днях
        days_passed = (today - SEMESTER_START).days
        
        # Если сегодня раньше начала семестра (например, тестируем)
        if days_passed < 0:
            # Для тестирования: используем текущую дату
            days_passed = (datetime.now() - datetime(2024, 12, 16)).days
            if days_passed < 0:
                days_passed = 0
        
        # Вычисляем номер недели (начинаем с 1)
        week_number = days_passed // 7 + 1
        
        # Определяем четность: 1,3,5... - нечетные, 2,4,6... - четные
        # В API: "1" = нечетная неделя, "2" = четная неделя
        if week_number % 2 == 1:  # Нечетная неделя
            return "1"
        else:  # Четная неделя
            return "2"
    
    @staticmethod
    def normalize_week_type(week_input: str) -> str:
        """Нормализовать тип недели к формату API ('1' или '2')"""
        if not week_input:
            return ""
        
        week = str(week_input).lower().strip()
        
        # Варианты для нечетной недели
        if week in ["odd", "нечетная", "нечет", "odd_week", "1", "н"]:
            return "1"
        
        # Варианты для четной недели
        if week in ["even", "четная", "чет", "even_week", "2", "ч"]:
            return "2"
        
        # По умолчанию считаем текущей неделей
        return LETIScheduleAPI.determine_current_week()
    
    @staticmethod
    def determine_current_week_for_date(target_date: datetime) -> str:
        """Определить тип недели для конкретной даты"""
        SEMESTER_START = datetime(2024, 9, 2)
        days_passed = (target_date - SEMESTER_START).days
        
        if days_passed < 0:
            days_passed = 0
        
        week_number = days_passed // 7 + 1
        return "1" if week_number % 2 == 1 else "2"
    
    @staticmethod
    def get_current_day_info() -> Dict:
        """Получить текущий день в формате API"""
        today = datetime.now()
        weekday_num = today.weekday()  # 0=понедельник, 6=воскресенье
        
        # Перевод номера дня в русское название
        days_ru = {
            0: "понедельник",
            1: "вторник", 
            2: "среда",
            3: "четверг",
            4: "пятница",
            5: "суббота",
            6: "воскресенье"
        }
        
        return {
            "number": str(weekday_num),
            "name": days_ru[weekday_num],
            "name_upper": days_ru[weekday_num].upper()
        }
    
    @staticmethod
    def normalize_day_name(day_input: str) -> str:
        """
        Привести название дня к формату API (русский, ЗАГЛАВНЫМИ)
        
        Принимает: 'monday', 'tuesday', 'понедельник', 'вторник', '0', '1', '2', ...
        Возвращает: 'ПОНЕДЕЛЬНИК', 'ВТОРНИК', 'СРЕДА', ...
        """
        if not day_input:
            return ""
        
        day = str(day_input).strip().lower()
        
        # 1. Если это номер дня (0-6)
        if day in ['0', '1', '2', '3', '4', '5', '6']:
            days_by_num = {
                '0': 'ПОНЕДЕЛЬНИК',
                '1': 'ВТОРНИК', 
                '2': 'СРЕДА',
                '3': 'ЧЕТВЕРГ',
                '4': 'ПЯТНИЦА',
                '5': 'СУББОТА',
                '6': 'ВОСКРЕСЕНЬЕ'
            }
            return days_by_num.get(day, day.upper())
        
        # 2. Перевод английских дней
        en_to_ru = {
            'monday': 'ПОНЕДЕЛЬНИК',
            'tuesday': 'ВТОРНИК',
            'wednesday': 'СРЕДА',
            'thursday': 'ЧЕТВЕРГ',
            'friday': 'ПЯТНИЦА',
            'saturday': 'СУББОТА',
            'sunday': 'ВОСКРЕСЕНЬЕ'
        }
        
        if day in en_to_ru:
            return en_to_ru[day]
        
        # 3. Перевод русских дней (строчные)
        ru_lower_to_upper = {
            'понедельник': 'ПОНЕДЕЛЬНИК',
            'вторник': 'ВТОРНИК',
            'среда': 'СРЕДА',
            'четверг': 'ЧЕТВЕРГ',
            'пятница': 'ПЯТНИЦА',
            'суббота': 'СУББОТА',
            'воскресенье': 'ВОСКРЕСЕНЬЕ'
        }
        
        if day in ru_lower_to_upper:
            return ru_lower_to_upper[day]
        
        # 4. Если уже в верхнем регистре (но на русском)
        ru_upper_days = ['ПОНЕДЕЛЬНИК', 'ВТОРНИК', 'СРЕДА', 'ЧЕТВЕРГ', 
                        'ПЯТНИЦА', 'СУББОТА', 'ВОСКРЕСЕНЬЕ']
        
        if day.upper() in ru_upper_days:
            return day.upper()
        
        # 5. Сокращения (пн, вт, ср...)
        short_to_full = {
            'пн': 'ПОНЕДЕЛЬНИК',
            'вт': 'ВТОРНИК',
            'ср': 'СРЕДА',
            'чт': 'ЧЕТВЕРГ',
            'пт': 'ПЯТНИЦА',
            'сб': 'СУББОТА',
            'вс': 'ВОСКРЕСЕНЬЕ',
            'mon': 'ПОНЕДЕЛЬНИK',
            'tue': 'ВТОРНИК',
            'wed': 'СРЕДА',
            'thu': 'ЧЕТВЕРГ',
            'fri': 'ПЯТНИЦА',
            'sat': 'СУББОТА',
            'sun': 'ВОСКРЕСЕНЬЕ'
        }
        
        if day in short_to_full:
            return short_to_full[day]
        
        # 6. На всякий случай - просто в верхний регистр
        return day.upper()
    
    @staticmethod
    def format_schedule_for_display(schedule_data: Dict) -> str:
        """Форматировать расписание для вывода в Telegram"""
        if not schedule_data["success"]:
            return f"❌ {schedule_data['error']}"
        
        lessons = schedule_data["lessons"]
        if not lessons:
            return "📭 На выбранный период занятий не найдено"
        
        # Сортировка: сначала по дню, потом по времени
        lessons_sorted = sorted(lessons, key=lambda x: (
            x.get("day_number", "999"),
            x.get("start_time_seconds", 0)
        ))
        
        # Формируем ответ
        week_type = schedule_data.get("week_type", "")
        week_text = ""
        if week_type == "1":
            week_text = "нечетная неделя"
        elif week_type == "2":
            week_text = "четная неделя"
        
        response = f"📅 *Расписание группы {schedule_data['group']}*"
        if week_text:
            response += f" ({week_text})"
        response += "\n\n"
        
        current_day = None
        for lesson in lessons_sorted:
            day_name = lesson.get("day_name", "").upper()
            
            # Добавляем заголовок дня, если он изменился
            if day_name != current_day:
                response += f"*{day_name}*\n"
                current_day = day_name
            
            # Извлекаем данные
            time_start = lesson.get("start_time", "??:??")
            time_end = lesson.get("end_time", "??:??")
            subject = lesson.get("name", "Не указано")
            teacher = lesson.get("teacher", "")
            room = lesson.get("room", "")
            subject_type = lesson.get("subjectType", "")
            week = lesson.get("week", "")
            form = lesson.get("form", "")
            
            # Форматируем занятие
            response += f"🕐 *{time_start}-{time_end}*"
            
            if subject_type:
                response += f" ({subject_type})"
            
            response += f"\n📚 {subject}\n"
            
            if teacher:
                response += f"👨‍🏫 {teacher}\n"
            
            if room:
                response += f"🚪 {room}\n"
            elif form:
                response += f"🌐 {form}\n"
            
            response += f"📆 Неделя: {week}\n"
            response += "───────────────\n\n"
        
        return response