from flask import Flask, render_template, request, jsonify
import aiml
import os
import random
from datetime import datetime
import time

app = Flask(__name__)

# Monkey-patch для устаревшего time.clock()
if not hasattr(time, 'clock'):
    time.clock = time.perf_counter

# Инициализация ядра AIML
kernel = aiml.Kernel()
aiml_files = []

# Состояния пользователей для игры "Угадай число"
user_states = {}


class AIMLManager:
    """Класс для управления загрузкой и обработкой AIML файлов"""

    @staticmethod
    def load_aiml_files():
        """Загружает AIML файлы из директории"""
        if os.path.isfile("std-startup.xml"):
            kernel.learn("std-startup.xml")
            aiml_files.append("std-startup.xml")
        else:
            # Создаем стандартный startup файл, если он отсутствует
            AIMLManager.create_default_startup()
            kernel.learn("std-startup.xml")
            aiml_files.append("std-startup.xml")

        # Загружаем дополнительные AIML файлы, если они есть
        if os.path.isdir("aiml"):
            for file in os.listdir("aiml"):
                if file.endswith(".aiml"):
                    kernel.learn(f"aiml/{file}")
                    aiml_files.append(f"aiml/{file}")

    @staticmethod
    def create_default_startup():
        """Создает стандартный startup файл AIML"""
        with open("std-startup.xml", "w", encoding="utf-8") as startup_file:
            startup_file.write('''<?xml version="1.0" encoding="UTF-8"?>
<aiml version="2.0">
    <category>
        <pattern>LOAD AIML</pattern>
        <template>
            <learn>aiml/*.aiml</learn>
        </template>
    </category>
</aiml>''')


class ChatManager:
    """Класс для управления чатом и обработки сообщений"""

    @staticmethod
    def process_message(user_id, message):
        """Обрабатывает сообщение пользователя"""
        # Удаляем пробелы между буквами, если они есть
        normalized_msg = message

        # Проверяем, находится ли пользователь в режиме игры
        if user_id in user_states and user_states[user_id].get("in_game", False):
            return ChatManager.handle_game_response(user_id, normalized_msg)

        # Обрабатываем сообщение через AIML
        aiml_response = kernel.respond(normalized_msg)

        # Если AIML не нашел ответа, используем стандартные ответы
        if not aiml_response or aiml_response.strip() == "":
            return ChatManager.get_default_response(normalized_msg)

        return aiml_response

    @staticmethod
    def handle_game_response(user_id, message):
        """Обрабатывает ответ пользователя в режиме игры"""
        game_data = user_states[user_id]

        if message.lower() in ["выход", "exit", "закончить"]:
            user_states[user_id]["in_game"] = False
            return "Игра завершена. Число было: " + str(game_data["number"]) + ". Чем еще могу помочь?"

        try:
            guess = int(message)
        except ValueError:
            return "Пожалуйста, введите число от 1 до 100 или 'выход' для завершения игры."

        if guess < game_data["number"]:
            return "Мое число больше! Попробуйте еще раз."
        elif guess > game_data["number"]:
            return "Мое число меньше! Попробуйте еще раз."
        else:
            user_states[user_id]["in_game"] = False
            return "Поздравляю! Вы угадали число " + str(guess) + " за " + str(
                game_data["attempts"]) + " попыток. Хотите сыграть еще?"

    @staticmethod
    def get_default_response(message):
        """Возвращает стандартные ответы, если AIML не нашел подходящего"""
        message_lower = message.lower()

        if any(word in message_lower for word in ["привет", "здравствуй", "hello"]):
            return "Привет! Как я могу вам помочь?"
        elif any(word in message_lower for word in ["пока", "до свидания", "прощай"]):
            return "До свидания! Возвращайтесь снова."
        elif "игра" in message_lower:
            return "Хотите сыграть в игру 'Угадай число'? Просто скажите 'играть'."
        else:
            return "Извините, я не совсем понял ваш вопрос. Можете переформулировать?"

    @staticmethod
    def start_game(user_id):
        """Начинает новую игру 'Угадай число'"""
        user_states[user_id] = {
            "in_game": True,
            "number": random.randint(1, 100),
            "attempts": 0
        }
        return "Я загадал число от 1 до 100. Попробуйте угадать!"


class BotResponse:
    """Класс для формирования структурированных ответов бота"""

    @staticmethod
    def create_response(text, quick_replies=None):
        """Создает структурированный ответ бота"""
        response = {
            "text": text,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "quick_replies": quick_replies or []
        }
        return response


# Инициализация AIML при старте приложения
AIMLManager.load_aiml_files()


@app.route("/")
def home():
    """Главная страница с чатом"""
    return render_template("index.html")


@app.route("/send_message", methods=["POST"])
def send_message():
    """Обрабатывает отправленное сообщение"""
    data = request.json
    user_id = data.get("user_id", "default_user")
    message = data.get("message", "").strip()

    # Обрабатываем специальные команды
    if message.lower() == "играть":
        response_text = ChatManager.start_game(user_id)
        quick_replies = ["Выход"]
    elif message.lower() == "помощь":
        response_text = "Я могу ответить на ваши вопросы или сыграть с вами в игру 'Угадай число'. Просто скажите 'играть'."
        quick_replies = ["Играть", "Привет", "Пока"]
    else:
        response_text = ChatManager.process_message(user_id, message)

        # Добавляем быстрые ответы в зависимости от контекста
        if user_id in user_states and user_states[user_id].get("in_game", False):
            quick_replies = ["50", "25", "75", "Выход"]
        elif any(word in response_text.lower() for word in ["игра", "играть"]):
            quick_replies = ["Играть", "Нет", "Помощь"]
        else:
            quick_replies = ["Играть", "Помощь", "Пока"]

    # Увеличиваем счетчик попыток, если пользователь в игре
    if user_id in user_states and user_states[user_id].get("in_game", False):
        user_states[user_id]["attempts"] += 1

    return jsonify(BotResponse.create_response(response_text, quick_replies))


if __name__ == "__main__":
    app.run(debug=True)