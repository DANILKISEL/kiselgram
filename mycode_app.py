import os
import random
from flask import Flask, render_template_string, request

app = Flask(__name__)

ADJECTIVES = ["КИБЕР", "МАТОВЫЙ", "ЛИМИТИРОВАННЫЙ", "ФЛЕКСИ", "СЕКРЕТНЫЙ", "ТОПОВЫЙ", "БРУТАЛЬНЫЙ", "ИНЖЕНЕРНЫЙ"]
NOUNS = ["ДРАКОН", "ОСЬМИНОГ", "АНАКОНДА", "КУБ", "МЕЙНФРЕЙМ", "СИНДИКАТ", "МОНОЛИТ", "РЕГЛАМЕНТ"]

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>Kiselgram 3D Dynamic Auth</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background-color: #000; color: #fff; font-family: sans-serif; text-align: center; padding: 50px 20px; margin: 0; }
        .box { border: 2px solid #d12b7f; padding: 30px; display: inline-block; border-radius: 10px; background: #111; max-width: 380px; text-align: center; box-sizing: border-box; }
        .screenshot-alert { background: #4a1515; color: #ff6b6b; border: 1px solid #ff6b6b; padding: 12px; border-radius: 5px; font-weight: bold; font-size: 13px; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 0.5px; }
        .code-display { font-size: 48px; font-weight: bold; color: #7dbf69; letter-spacing: 5px; margin: 20px 0; background: #222; padding: 15px; border-radius: 5px; border: 1px dashed #7dbf69; }
        .phrase-display { font-size: 15px; color: #ff6b6b; font-weight: bold; text-transform: uppercase; margin-bottom: 25px; letter-spacing: 1px; }
        button { background: linear-gradient(90deg, #d12b7f 0%, #7dbf69 100%); color: white; border: none; padding: 12px; font-weight: bold; border-radius: 5px; cursor: pointer; width: 100%; font-size: 15px; text-transform: uppercase; letter-spacing: 1px; }
        .info { color: #ccc; font-size: 13px; line-height: 1.5; margin-bottom: 15px; }
        h1 { background: linear-gradient(90deg, #d12b7f 0%, #7dbf69 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 32px; margin-bottom: 25px; font-weight: bold; text-transform: uppercase; }
    </style>
</head>
<body>
    <h1>ГЕНЕРАТОР КОДА</h1>
    <div class="box">
        <p class="info">Ваш уникальный одноразовый ключ авторизации для самовывоза. Скопируйте цифры и вставьте их в поле «Ваш Код» в Google Форме.</p>
        <div class="screenshot-alert">⚠️ ОБЯЗАТЕЛЬНО СДЕЛАЙТЕ СКРИНШОТ ЭКРАНА С КОДОМ!</div>
        <div class="code-display">{{ code }}</div>
        <div class="phrase-display">🔐 ФРАЗА: {{ phrase }}</div>
        <form action="/" method="GET">
            <button type="submit">🔄 СГЕНЕРИРОВАТЬ НОВЫЙ КОД</button>
        </form>
        <p style="margin-top: 20px;"><a href="/k/" style="color: #7dbf69; font-weight: bold; text-decoration: none; font-size: 14px;">→ ВОЙТИ В KISELGRAM</a></p>
    </div>
</body>
</html>"""

@app.route("/")
def index():
    random_code = random.randint(1000, 9999)
    random_phrase = f"{random.choice(ADJECTIVES)} {random.choice(NOUNS)}"
    return render_template_string(HTML_TEMPLATE, code=random_code, phrase=random_phrase)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)
