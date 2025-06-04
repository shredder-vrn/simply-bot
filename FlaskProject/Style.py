from flask import Flask, render_template_string, request
from pygments import highlight
from pygments.lexers import get_lexer_by_name, get_all_lexers
from pygments.formatters import HtmlFormatter
from pygments.style import Style
from pygments.token import Keyword, Name, Comment, String, Error, Number, Operator, Generic

app = Flask(__name__)

# Получаем список всех доступных лексеров (языков)
LEXERS = sorted([(lexer[1][0], lexer[0]) for lexer in get_all_lexers() if lexer[1]])


# Стиль для чёрной темы
class BlackStyle(Style):
    default_style = ""
    styles = {
        Comment: 'italic #5C6370',
        Keyword: 'bold #C678DD',
        Name: '#E06C75',
        Name.Function: '#61AFEF',
        Name.Class: 'bold #E5C07B',
        String: '#98C379',
        Error: 'bg:#1E0010 #E06C75',
        Number: '#D19A66',
        Operator: '#56B6C2',
        Generic.Heading: 'bold #528BFF',
    }


# Стиль для голубой темы
class BlueStyle(Style):
    default_style = ""
    styles = {
        Comment: 'italic #6A7B8B',
        Keyword: 'bold #1E6FBF',
        Name: '#2D2D2D',
        Name.Function: '#3A7DBF',
        Name.Class: 'bold #3A7DBF',
        String: '#2E6E3A',
        Error: 'bg:#F2DEDE #A94442',
        Number: '#8A2BE2',
        Operator: '#1E6FBF',
        Generic.Heading: 'bold #1E6FBF',
    }


# Стандартный стиль
class CustomStyle(Style):
    styles = {
        Comment: 'italic #888',
        Keyword: 'bold #005',
        Name: '#000',
        Name.Function: '#0A0',
        Name.Class: 'bold #0A0',
        String: 'bg:#eee #800',
        Error: 'bg:#e3d2d2 #a00',
        Number: '#60E',
        Operator: 'bold #666',
        Generic.Heading: 'bold #000080',
    }


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Подсветка синтаксиса</title>
    <style>
        {{ style }}
        body {
            background-color: {{ bg_color }};
            color: {{ text_color }};
            font-family: Arial, sans-serif;
        }
        .code-container {
            display: flex;
            flex-direction: column;
            max-width: 800px;
            margin: 20px auto;
            padding: 20px;
        }
        textarea {
            width: 100%;
            height: 300px;
            font-family: monospace;
            margin-bottom: 10px;
            background-color: {{ textarea_bg }};
            color: {{ textarea_color }};
            border: 1px solid {{ border_color }};
        }
        .highlight {
            padding: 10px;
            border: 1px solid {{ border_color }};
            border-radius: 4px;
            background: {{ highlight_bg }};
            overflow-x: auto;
        }
        button {
            padding: 8px 16px;
            background-color: {{ button_bg }};
            color: {{ button_color }};
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 10px;
        }
        button:hover {
            background-color: {{ button_hover }};
        }
        .theme-selector {
            margin-bottom: 15px;
        }
        select {
            padding: 8px;
            border-radius: 4px;
            border: 1px solid {{ border_color }};
            background-color: {{ textarea_bg }};
            color: {{ textarea_color }};
            margin-right: 10px;
        }
        .controls {
            margin-bottom: 15px;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
        }
        .control-group {
            display: flex;
            align-items: center;
            margin-right: 15px;
        }
        label {
            margin-right: 8px;
        }
    </style>
</head>
<body>
    <div class="code-container">
        <h1>Подсветка синтаксиса</h1>

        <form method="post">
            <div class="controls">
                <div class="control-group">
                    <label for="language">Язык:</label>
                    <select name="language" id="language">
                        {% for alias, name in lexers %}
                            <option value="{{ alias }}" {% if language == alias %}selected{% endif %}>{{ name }}</option>
                        {% endfor %}
                    </select>
                </div>

                <div class="control-group">
                    <label>Тема:</label>
                    <button type="submit" name="theme" value="light">Светлая</button>
                    <button type="submit" name="theme" value="blue">Голубая</button>
                    <button type="submit" name="theme" value="dark">Тёмная</button>
                </div>
            </div>

            <textarea name="code" rows="20" cols="80">{{ code }}</textarea>

            <div class="controls">
                <button type="submit" name="action" value="highlight">Подсветить синтаксис</button>
            </div>
        </form>

        {% if highlighted %}
        <div class="highlight">
            {{ highlighted|safe }}
        </div>
        {% endif %}
    </div>
</body>
</html>
"""


@app.route('/', methods=['GET', 'POST'])
def index():
    code = ''
    highlighted = None
    theme = request.form.get('theme', 'light')
    language = request.form.get('language', 'python')

    if request.method == 'POST':
        code = request.form.get('code', '')
        language = request.form.get('language', 'python')

        try:
            lexer = get_lexer_by_name(language)
        except:
            lexer = get_lexer_by_name('text')  # fallback to plain text

        if theme == 'dark':
            style_class = BlackStyle
            formatter = HtmlFormatter(style=style_class, linenos=True, cssclass="source")
        elif theme == 'blue':
            style_class = BlueStyle
            formatter = HtmlFormatter(style=style_class, linenos=True, cssclass="source")
        else:
            style_class = CustomStyle
            formatter = HtmlFormatter(style=style_class, linenos=True, cssclass="source")

        highlighted = highlight(code, lexer, formatter)

    # Устанавливаем цвета для выбранной темы
    if theme == 'dark':
        style = HtmlFormatter(style=BlackStyle).get_style_defs('.source')
        theme_colors = {
            'bg_color': '#1E1E1E',
            'text_color': '#D4D4D4',
            'textarea_bg': '#252526',
            'textarea_color': '#D4D4D4',
            'border_color': '#3C3C3C',
            'highlight_bg': '#252526',
            'button_bg': '#3C3C3C',
            'button_color': '#FFFFFF',
            'button_hover': '#4E4E4E'
        }
    elif theme == 'blue':
        style = HtmlFormatter(style=BlueStyle).get_style_defs('.source')
        theme_colors = {
            'bg_color': '#E6F2FF',
            'text_color': '#2D2D2D',
            'textarea_bg': '#FFFFFF',
            'textarea_color': '#2D2D2D',
            'border_color': '#B3D1FF',
            'highlight_bg': '#FFFFFF',
            'button_bg': '#1E6FBF',
            'button_color': '#FFFFFF',
            'button_hover': '#3A7DBF'
        }
    else:  # light theme
        style = HtmlFormatter(style=CustomStyle).get_style_defs('.source')
        theme_colors = {
            'bg_color': '#FFFFFF',
            'text_color': '#000000',
            'textarea_bg': '#F8F8F8',
            'textarea_color': '#000000',
            'border_color': '#DDDDDD',
            'highlight_bg': '#F8F8F8',
            'button_bg': '#005',
            'button_color': '#FFFFFF',
            'button_hover': '#003'
        }

    return render_template_string(HTML_TEMPLATE,
                                  code=code,
                                  highlighted=highlighted,
                                  style=style,
                                  lexers=LEXERS,
                                  language=language,
                                  **theme_colors)


if __name__ == '__main__':
    app.run(debug=True)