from django.utils.translation import get_language

MESSAGES = {
'uk': {
'Required':'Обов’язкове поле.',
'Possible duplicate. Confirm “allow duplicate” to create a separate client.':'Можливий дублікат. Підтвердьте створення окремого клієнта відповідним прапорцем.',
'Another administrator changed this chart. Reload before saving.':'Інший адміністратор змінив карту. Оновіть сторінку перед збереженням.',
'This submission has already been processed.':'Це надсилання вже оброблено.',
'Manual UTC offset requires ±840 minutes and a reason.':'Ручне UTC-зміщення має бути в межах ±840 хвилин; обов’язково вкажіть причину.',
'Select a valid IANA time zone.':'Вкажіть чинний часовий пояс IANA, наприклад Europe/Kyiv.',
'This local time does not exist because of a clock change.':'Такого місцевого часу не існує через переведення годинника. Виправте час.',
'Invalid time occurrence.':'Неправильний варіант повторюваного часу.',
'Ambiguous local time. Select one:':'Цей місцевий час повторюється. Оберіть один варіант:',
'Ephemeris manifest missing. Run ops/setup_data.py first.':'Файли ефемерид не підготовлені. Потрібне встановлення даних на сервері.',
'Requested Swiss ephemeris unavailable; fallback rejected.':'Запитані ефемериди недоступні. Розрахунок зупинено, стару карту збережено.',
'Select a valid city or clear the selection for manual coordinates.':'Оберіть чинне місто або скасуйте вибір і введіть координати вручну.',
'The ephemeris could not calculate this chart.':'Не вдалося розрахувати карту за ефемеридами. Перевірте дані й повторіть спробу.',
'Houses cannot be calculated for these coordinates and time.':'Для цих координат і часу не вдалося розрахувати доми.',
'Ephemeris checksum mismatch or missing file.':'Файл ефемерид відсутній або не пройшов перевірку цілісності.',
},
'ru': {
'Required':'Обязательное поле.',
'Possible duplicate. Confirm “allow duplicate” to create a separate client.':'Возможный дубликат. Подтвердите создание отдельного клиента соответствующим флажком.',
'Another administrator changed this chart. Reload before saving.':'Другой администратор изменил карту. Обновите страницу перед сохранением.',
'This submission has already been processed.':'Эта отправка уже обработана.',
'Manual UTC offset requires ±840 minutes and a reason.':'Ручное UTC-смещение должно быть в пределах ±840 минут; обязательно укажите причину.',
'Select a valid IANA time zone.':'Укажите действующий часовой пояс IANA, например Europe/Kyiv.',
'This local time does not exist because of a clock change.':'Такого местного времени не существует из-за перевода часов. Исправьте время.',
'Invalid time occurrence.':'Неправильный вариант повторяющегося времени.',
'Ambiguous local time. Select one:':'Это местное время повторяется. Выберите один вариант:',
'Ephemeris manifest missing. Run ops/setup_data.py first.':'Файлы эфемерид не подготовлены. Требуется установка данных на сервере.',
'Requested Swiss ephemeris unavailable; fallback rejected.':'Запрошенные эфемериды недоступны. Расчёт остановлен, старая карта сохранена.',
'Select a valid city or clear the selection for manual coordinates.':'Выберите действующий город или отмените выбор и введите координаты вручную.',
'The ephemeris could not calculate this chart.':'Не удалось рассчитать карту по эфемеридам. Проверьте данные и повторите попытку.',
'Houses cannot be calculated for these coordinates and time.':'Для этих координат и времени не удалось рассчитать дома.',
'Ephemeris checksum mismatch or missing file.':'Файл эфемерид отсутствует или не прошёл проверку целостности.',
}}

def local_error(text):
    lang = (get_language() or 'uk')[:2]
    if lang == 'en':
        return text
    messages = MESSAGES.get(lang, MESSAGES['uk'])
    for key, translated in messages.items():
        if text.startswith(key):
            return translated + text[len(key):]
    return text
