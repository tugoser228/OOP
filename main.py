import os
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from api_client import LETIScheduleAPI

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем токен
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    logger.error("Токен бота не найден! Проверьте файл .env")
    exit(1)

# Главное меню
def get_main_keyboard():
    keyboard = [
        [KeyboardButton("📅 Сегодня"), KeyboardButton("⏭️ Завтра")],
        [KeyboardButton("🔍 Ближайшая"), KeyboardButton("📋 Вся неделя")],
        [KeyboardButton("🗓️ Выбрать день"), KeyboardButton("❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /start"""
    user = update.effective_user
    
    welcome_text = f"""
👋 Привет, {user.first_name}!

Я бот для расписания ЛЭТИ.

*Основные команды:*
/start — начать работу
/help — справка по командам
/today [группа] — расписание на сегодня
/tomorrow [группа] — расписание на завтра
/week [группа] — расписание на всю неделю
/day [день] [неделя] [группа] — расписание на конкретный день
/near [группа] — ближайшее занятие

*Примеры использования:*
/today 4352
/tomorrow 4352
/week 4352
/day monday 1 4352
/day вторник 2 4352
/near 4352

Используйте кнопки ниже для быстрого доступа!
    """
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )
    
    logger.info(f"Пользователь {user.id} запустил бота")

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📚 *Все команды бота:*

*Основные команды:*
`/start` - начать работу
`/help` - эта справка

*Расписание (можно через команды или кнопки):*
`/today [группа]` - на сегодня
`/tomorrow [группа]` - на завтра  
`/week [группа]` - вся неделя
`/all [группа]` - вся неделя

*Расширенные команды:*
`/day [день] [неделя] [группа]` - конкретный день
`/near [группа]` - ближайшая пара

*Кнопки меню:*
• 📅 Сегодня - расписание на сегодня
• ⏭️ Завтра - расписание на завтра
• 🔍 Ближайшая - ближайшее занятие
• 📋 Вся неделя - расписание на неделю
• 🗓️ Выбрать день - расписание на конкретный день

*Примеры использования:*
`/today 4352`
`/tomorrow 4352`
`/week 4352`
`/day monday odd 4352`
`/day вторник четная 4352`
`/near 4352`

*Дни недели:* понедельник-воскресенье (можно на рус/англ)
*Тип недели:* нечетная/четная или odd/even
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

# Команда /today
async def today_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Расписание на сегодня"""
    if not context.args:
        await update.message.reply_text("Укажите номер группы. Пример: `/today 4341`", parse_mode='Markdown')
        return
    
    group = context.args[0]
    
    # Получаем текущую неделю
    week_type = LETIScheduleAPI.determine_current_week()  # "1" или "2"
    
    # Получаем текущий день в формате API
    from datetime import datetime
    today_num = datetime.now().weekday()  # 0=понедельник, 1=вторник
    
    # Преобразуем номер дня в название для API
    day_num_to_api = {
        0: "ПОНЕДЕЛЬНИК",
        1: "ВТОРНИК", 
        2: "СРЕДА",
        3: "ЧЕТВЕРГ",
        4: "ПЯТНИЦА",
        5: "СУББОТА",
        6: "ВОСКРЕСЕНЬЕ"
    }
    
    day_for_api = day_num_to_api[today_num]
    
    print(f"🔍 Ищу: группа {group}, день '{day_for_api}', неделя {week_type}")
    
    # Получаем расписание
    schedule = LETIScheduleAPI.get_group_schedule(group, week_type, day_for_api)
    
    # Если не нашли - пробуем без фильтра по неделе (все недели)
    if schedule["total_lessons"] == 0:
        print(f"⚠️ Не найдено на неделе {week_type}, ищу на всех неделях")
        schedule = LETIScheduleAPI.get_group_schedule(group, None, day_for_api)
    
    # Форматируем и отправляем
    formatted = LETIScheduleAPI.format_schedule_for_display(schedule)
    
    # Добавляем пояснение, если пар нет
    if schedule["total_lessons"] == 0:
        week_text = "четной" if week_type == "2" else "нечетной"
        formatted = f"📅 *На сегодня ({day_for_api.lower()}, {week_text} неделя) пар нет*\n\n" + formatted
    
    await update.message.reply_text(formatted, parse_mode='Markdown')

# Команда /week
async def week_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Расписание на всю неделю"""
    if not context.args:
        await update.message.reply_text(
            "Укажите номер группы.\nПример: `/week 4341`",
            parse_mode='Markdown'
        )
        return
    
    group = context.args[0]
    week_type = LETIScheduleAPI.determine_current_week()
    
    week_ru = "нечетная неделя" if week_type == "odd_week" else "четная неделя"
    
    await update.message.reply_text(
        f"📅 Ищу расписание на неделю для группы *{group}*...\n"
        f"📌 {week_ru}",
        parse_mode='Markdown'
    )
    
    # Получаем расписание без фильтра по дню
    schedule = LETIScheduleAPI.get_group_schedule(group, week_type)
    
    # Форматируем и отправляем
    formatted = LETIScheduleAPI.format_schedule_for_display(schedule)
    
    # Если много текста, разбиваем на части
    if len(formatted) > 4000:
        parts = [formatted[i:i+4000] for i in range(0, len(formatted), 4000)]
        for part in parts:
            await update.message.reply_text(part, parse_mode='Markdown')
    else:
        await update.message.reply_text(formatted, parse_mode='Markdown')
    
# Команда /tomorrow
async def tomorrow_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Расписание на завтра"""
    if not context.args:
        await update.message.reply_text(
            "Укажите номер группы.\nПример: `/tomorrow 4352`",
            parse_mode='Markdown'
        )
        return
    
    group = context.args[0]
    
    from datetime import datetime, timedelta
    
    # Определяем завтра
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_num = tomorrow.weekday()  # 0-6
    
    # Если воскресенье, то завтра - понедельник
    if tomorrow_num == 6:  # 6 = воскресенье
        tomorrow += timedelta(days=1)
        tomorrow_num = 0
    
    # Определяем неделю для завтра
    week_type = LETIScheduleAPI.determine_current_week_for_date(tomorrow)
    
    # Дни недели на русском
    days = ["ПОНЕДЕЛЬНИК", "ВТОРНИК", "СРЕДА", "ЧЕТВЕРГ", "ПЯТНИЦА", "СУББОТА", "ВОСКРЕСЕНЬЕ"]
    day_for_api = days[tomorrow_num]
    
    # Получаем расписание
    schedule = LETIScheduleAPI.get_group_schedule(group, week_type, day_for_api)
    
    # Форматируем
    formatted = LETIScheduleAPI.format_schedule_for_display(schedule)
    
    # Добавляем заголовок
    day_ru = day_for_api.lower().capitalize()
    week_name = "нечетной" if week_type == "1" else "четной"
    response = f"📅 *Расписание на завтра ({day_ru}, {week_name} неделя)*\n\n{formatted}"
    
    await update.message.reply_text(response, parse_mode='Markdown')
    
# Команда /day
async def day_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Расписание на конкретный день и неделю"""
    if len(context.args) < 3:
        await update.message.reply_text(
            "Используйте: `/day ДЕНЬ НЕДЕЛЯ ГРУППА`\n\n"
            "*Примеры:*\n"
            "`/day monday odd 4352`\n"
            "`/day вторник четная 4352`\n"
            "`/day 1 1 4352` (понедельник, нечетная неделя)\n\n"
            "*Дни:* monday/tuesday/... или понедельник/вторник/... или 0-6\n"
            "*Недели:* odd/even или нечетная/четная или 1/2",
            parse_mode='Markdown'
        )
        return
    
    day_input = context.args[0]
    week_input = context.args[1]
    group = context.args[2]
    
    # Нормализуем день
    day_normalized = LETIScheduleAPI.normalize_day_name(day_input)
    
    # Нормализуем неделю
    week_normalized = LETIScheduleAPI.normalize_week_type(week_input)
    
    print(f"🔍 Запрос: день='{day_normalized}', неделя='{week_normalized}', группа='{group}'")
    
    # Получаем расписание
    schedule = LETIScheduleAPI.get_group_schedule(group, week_normalized, day_normalized)
    
    # Форматируем
    formatted = LETIScheduleAPI.format_schedule_for_display(schedule)
    
    # Добавляем заголовок
    day_ru = day_normalized.lower().capitalize()
    week_name = "нечетной" if week_normalized == "1" else "четной"
    response = f"📅 *{day_ru}, {week_name} неделя*\n\n{formatted}"
    
    await update.message.reply_text(response, parse_mode='Markdown')
    
# Команда /near
async def near_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ближайшее занятие"""
    if not context.args:
        await update.message.reply_text("Укажите номер группы. Пример: `/near 4352`", parse_mode='Markdown')
        return
    
    group = context.args[0]
    
    from datetime import datetime, timedelta
    
    # Получаем текущее время
    now = datetime.now()
    current_time_str = now.strftime("%H:%M")
    current_weekday = now.weekday()  # 0=понедельник
    
    # Преобразуем строку времени в минуты для сравнения
    def time_to_minutes(time_str):
        try:
            h, m = map(int, time_str.split(':'))
            return h * 60 + m
        except:
            return 0
    
    current_minutes = time_to_minutes(current_time_str)
    
    # Определяем текущую неделю
    week_type = LETIScheduleAPI.determine_current_week()
    
    # Получаем все занятия на этой неделе
    schedule = LETIScheduleAPI.get_group_schedule(group, week_type)
    
    if not schedule["success"] or schedule["total_lessons"] == 0:
        await update.message.reply_text(f"📭 У группы {group} нет занятий на этой неделе.")
        return
    
    # Дни недели в формате API (ЗАГЛАВНЫЕ русские)
    days_api_format = ["ПОНЕДЕЛЬНИК", "ВТОРНИК", "СРЕДА", "ЧЕТВЕРГ", "ПЯТНИЦА", "СУББОТА", "ВОСКРЕСЕНЬЕ"]
    today_name_api = days_api_format[current_weekday]
    
    # Ищем ближайшее занятие
    nearest_lesson = None
    min_days_ahead = 7  # Максимум неделя вперед
    min_time_diff = 24 * 60  # Максимум 24 часа в минутах
    
    for lesson in schedule["lessons"]:
        lesson_day = lesson.get("day_name", "")  # В формате "ПОНЕДЕЛЬНИК"
        lesson_time_str = lesson.get("start_time", "00:00")
        lesson_minutes = time_to_minutes(lesson_time_str)
        
        # Находим индекс дня занятия
        try:
            lesson_day_index = days_api_format.index(lesson_day)
        except ValueError:
            # Если день в другом формате, пробуем нормализовать
            normalized_day = LETIScheduleAPI.normalize_day_name(lesson_day)
            try:
                lesson_day_index = days_api_format.index(normalized_day)
            except:
                continue  # Пропускаем если не распознали день
        
        # Вычисляем разницу в днях
        days_diff = lesson_day_index - current_weekday
        if days_diff < 0:
            days_diff += 7  # Занятие на следующей неделе
        
        # Вычисляем разницу во времени
        if days_diff == 0:
            # Сегодня
            time_diff = lesson_minutes - current_minutes
            if time_diff < 0:
                continue  # Занятие уже прошло сегодня
        else:
            # Не сегодня
            time_diff = days_diff * 24 * 60 + lesson_minutes
        
        # Проверяем, ближе ли это занятие
        if time_diff < min_time_diff or (time_diff == min_time_diff and days_diff < min_days_ahead):
            min_time_diff = time_diff
            min_days_ahead = days_diff
            nearest_lesson = lesson
    
    # Форматируем ответ
    if nearest_lesson:
        day_name = nearest_lesson.get("day_name", "").lower().capitalize()
        time_start = nearest_lesson.get("start_time", "??:??")
        time_end = nearest_lesson.get("end_time", "??:??")
        subject = nearest_lesson.get("name", "Не указано")
        room = nearest_lesson.get("room", "")
        teacher = nearest_lesson.get("teacher", "")
        
        # Определяем когда
        if min_days_ahead == 0:
            when = "Сегодня"
        elif min_days_ahead == 1:
            when = "Завтра"
        else:
            when = f"Через {min_days_ahead} дня(ей)"
        
        response = (
            f"🔍 *Ближайшее занятие для группы {group}:*\n\n"
            f"📅 *{when} ({day_name})*\n"
            f"🕐 *{time_start}-{time_end}*\n"
            f"📚 {subject}\n"
        )
        
        if teacher:
            response += f"👨‍🏫 {teacher}\n"
        
        if room:
            response += f"🚪 {room}\n"
        
        response += f"📆 {'Нечетная' if week_type == '1' else 'Четная'} неделя"
        
    else:
        # Если не нашли ближайшее, покажем первое занятие на неделе
        if schedule["lessons"]:
            # Сортируем правильно
            def get_lesson_sort_key(lesson):
                day_name = lesson.get("day_name", "")
                try:
                    day_index = days_api_format.index(day_name)
                except:
                    day_index = 999
                time_str = lesson.get("start_time", "23:59")
                return (day_index, time_to_minutes(time_str))
            
            first_lesson = sorted(schedule["lessons"], key=get_lesson_sort_key)[0]
            
            day_name = first_lesson.get("day_name", "").lower().capitalize()
            time_start = first_lesson.get("start_time", "??:??")
            time_end = first_lesson.get("end_time", "??:??")
            subject = first_lesson.get("name", "Не указано")
            
            response = (
                f"🔍 *Ближайшее занятие для группы {group}:*\n\n"
                f"📅 *{day_name}*\n"
                f"🕐 *{time_start}-{time_end}*\n"
                f"📚 {subject}\n"
                f"📆 {'Нечетная' if week_type == '1' else 'Четная'} неделя\n\n"
                f"💡 *Сегодня и завтра пар нет*"
            )
        else:
            response = f"📭 У группы {group} нет занятий на этой неделе."
    
    await update.message.reply_text(response, parse_mode='Markdown')

# Команда /testapi
async def test_api_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестирование подключения к API ЛЭТИ"""
    await update.message.reply_text("🔧 Тестирую подключение к API ЛЭТИ...")
    
    test_groups = ['4341', '3301', '2302', '1381', '4301']
    response_text = "📊 *Результаты теста API ЛЭТИ:*\n\n"
    
    for group in test_groups:
        result = LETIScheduleAPI.get_group_schedule(group)
        
        if result["success"]:
            lessons = result["total_lessons"]
            response_text += f"✅ Группа *{group}*: {lessons} занятий\n"
        else:
            response_text += f"❌ Группа *{group}*: {result['error']}\n"
    
    response_text += "\n📡 *Для использования:*\n"
    response_text += "/today [группа] - расписание на сегодня\n"
    response_text += "/week [группа] - вся неделя\n"
    response_text += "/day [день] [неделя] [группа] - конкретный день\n"
    
    await update.message.reply_text(response_text, parse_mode='Markdown')

# Обработка кнопок
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "↩️ Назад":
        await update.message.reply_text(
            "Возвращаюсь в главное меню...",
            reply_markup=get_main_keyboard()
        )
        context.user_data.clear()
        return
    
    user_id = update.effective_user.id
    
    print(f"🔄 Пользователь {user_id} нажал: {text}")
    
    if text == "📅 Сегодня":
        await update.message.reply_text(
            "Введите номер группы (например: 4352):"
        )
        context.user_data['action'] = 'today'
        context.user_data['step'] = 'waiting_group'
        
    elif text == "⏭️ Завтра":
        await update.message.reply_text(
            "Введите номер группы (например: 4352):"
        )
        context.user_data['action'] = 'tomorrow'
        context.user_data['step'] = 'waiting_group'
        
    elif text == "🔍 Ближайшая":
        await update.message.reply_text(
            "Введите номер группы (например: 4352):"
        )
        context.user_data['action'] = 'near'
        context.user_data['step'] = 'waiting_group'
        
    elif text == "📋 Вся неделя":
        await update.message.reply_text(
            "Введите номер группы (например: 4352):"
        )
        context.user_data['action'] = 'week'
        context.user_data['step'] = 'waiting_group'
        
    elif text == "🗓️ Выбрать день":
        # Показываем инструкцию для ручного ввода команды /day
        await update.message.reply_text(
            "📝 *Выбор конкретного дня:*\n\n"
            "Используйте команду:\n"
            "`/day [день] [неделя] [группа]`\n\n"
            "*Примеры:*\n"
            "`/day monday odd 4352`\n"
            "`/day вторник четная 4352`\n"
            "`/day 1 1 4352` (понедельник, нечетная неделя)\n\n"
            "*Или введите данные по шагам:*\n"
            "1. Номер группы\n"
            "2. День недели\n"
            "3. Тип недели",
            parse_mode='Markdown',
            reply_markup=get_day_selection_keyboard()  # Новая клавиатура для выбора
        )
        context.user_data['action'] = 'custom_day'
        context.user_data['step'] = 'waiting_group'
        
    elif text == "❓ Помощь":
        await help_command(update, context)
        
    elif context.user_data.get('step') == 'waiting_group':
        # Пользователь ввёл номер группы
        group = text.strip()
        
        if group.isdigit() and 1000 <= int(group) <= 9999:
            context.user_data['group'] = group
            action = context.user_data['action']
            
            if action in ['today', 'tomorrow', 'near', 'week']:
                # Простые команды - сразу выполняем
                context.user_data['step'] = None
                
                if action == 'today':
                    context.args = [group]
                    await today_schedule(update, context)
                elif action == 'tomorrow':
                    context.args = [group]
                    await tomorrow_schedule(update, context)
                elif action == 'near':
                    context.args = [group]
                    await near_lesson(update, context)
                elif action == 'week':
                    context.args = [group]
                    await week_schedule(update, context)
                    
            elif action == 'custom_day':
                # Для выбора дня - переходим к следующему шагу
                await update.message.reply_text(
                    f"✅ Группа: {group}\n\n"
                    f"Теперь выберите день недели:",
                    reply_markup=get_days_keyboard()
                )
                context.user_data['step'] = 'waiting_day'
                
        else:
            await update.message.reply_text(
                "❌ Некорректный номер группы.\n"
                "Номер должен быть 4 цифры (например: 4351, 3302, 2303)",
                reply_markup=get_main_keyboard()
            )
            context.user_data.clear()
            
    elif context.user_data.get('step') == 'waiting_day':
        # Пользователь выбрал день
        day_input = text
        context.user_data['day'] = day_input
        
        await update.message.reply_text(
            f"✅ Группа: {context.user_data['group']}\n"
            f"✅ День: {day_input}\n\n"
            f"Теперь выберите тип недели:",
            reply_markup=get_weeks_keyboard()
        )
        context.user_data['step'] = 'waiting_week'
        
    elif context.user_data.get('step') == 'waiting_week':
        # Пользователь выбрал неделю
        week_input = text
        group = context.user_data.get('group')
        day_input = context.user_data.get('day')
        
        # Выполняем команду /day
        context.args = [day_input, week_input, group]
        await day_schedule(update, context)
        
        # Очищаем данные пользователя
        context.user_data.clear()
        
    else:
        await update.message.reply_text(
            "Я не понимаю эту команду. Используйте /help или кнопки ниже.",
            reply_markup=get_main_keyboard()
        )

def get_day_selection_keyboard():
    """Клавиатура для выбора дня недели"""
    keyboard = [
        [KeyboardButton("Понедельник"), KeyboardButton("Вторник")],
        [KeyboardButton("Среда"), KeyboardButton("Четверг")],
        [KeyboardButton("Пятница"), KeyboardButton("Суббота")],
        [KeyboardButton("↩️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_days_keyboard():
    """Клавиатура с днями недели"""
    keyboard = [
        [KeyboardButton("Понедельник"), KeyboardButton("Вторник"), KeyboardButton("Среда")],
        [KeyboardButton("Четверг"), KeyboardButton("Пятница"), KeyboardButton("Суббота")],
        [KeyboardButton("Воскресенье"), KeyboardButton("↩️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_weeks_keyboard():
    """Клавиатура с типами недель"""
    keyboard = [
        [KeyboardButton("Нечетная"), KeyboardButton("Четная")],
        [KeyboardButton("Любая"), KeyboardButton("↩️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Главная функция
def main():
    """Запуск бота"""
    
    print("🔧 DEBUG: main() начал выполняться")
    print(f"🔧 Токен: {TOKEN[:15]}...")
    
    try:
        # Создаем приложение
        application = Application.builder().token(TOKEN).build()
        
        
        
        # Регистрируем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("today", today_schedule))
        application.add_handler(CommandHandler("tomorrow", tomorrow_schedule))
        application.add_handler(CommandHandler("day", day_schedule))
        application.add_handler(CommandHandler("near", near_lesson))
        application.add_handler(CommandHandler("week", week_schedule))
        application.add_handler(CommandHandler("all", week_schedule))  # Алиас для /week
        
        # Обработчик кнопок
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
        
        # Запускаем бота
        logger.info("🤖 Бот запускается...")
        print("=" * 50)
        print("Бот для расписания ЛЭТИ")
        print("Используется официальное API ЛЭТИ")
        print("=" * 50)
        print("\n📱 Доступные команды в Telegram:")
        print("/start - начать")
        print("/today [группа] - расписание на сегодня")
        print("/week [группа] - вся неделя")
        print("=" * 50)
        
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        print(f"❌ Ошибка: {e}")

if __name__ == '__main__':
    main()