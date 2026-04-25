# Twitch Vibe Coding

Система управления задачами для Twitch стримов с голосованием и автоматическим созданием Pull Requests.

## Зачем этот проект?

Во время стрима зрители предлагают идеи для проекта — фичи, баг-фиксы, улучшения. Обычно ты (стример) должен:
1. Следить за чатом
2. Записывать идеи
3. Решать какие делать, а какие нет
4. Потом не забыть что хотели сделать

**Vibe Coding автоматизирует этот процесс:**
- Зрители пишут `[IDEA]` в чате с описанием
- Другие зрители голосуют `!vote +1` / `!vote -1`
- Бот отслеживает голоса и когда набирается порог (по умолчанию 3) — сообщает тебе
- Ты пише `!approve #1` чтобы одобрить
- Бот создаёт branch, выполняет задачу, создаёт PR

Всё что тебе нужно — написать одну команду в чате!

## Возможности

- **[IDEA] command** — зрители предлагают идеи в чате
- **Голосование** — `!vote +1` / `!vote -1` от зрителей
- **Approval workflow** — `!approve #N` / `!reject #N` от стримера
- **Auto branch** — автоматическое создание git branch
- **Auto PR** — автоматический Pull Request через gh CLI
- **CLI управление** — `vibe ideas`, `vibe pending`, `vibe stats`

## Быстрый старт (2 минуты)

### Шаг 1: Скачай и установи

```bash
# Клонировать репозиторий
git clone https://github.com/DoonyFreeman/Twich_vibe_coding.git
cd Twich_vibe_coding

# Установить зависимости ( one command)
pip install -e .
```

### Шаг 2: Создать конфигурацию

```bash
# Создаёт .env и config.yaml автоматически
vibe init
```

### Шаг 3: Настроить Twitch

Открой файл `.env` в любом редакторе:

```bash
nano .env
```

Добавь свои данные:

```
# Получить на https://twitchapps.com/kraken/
TWITCH_OAUTH_TOKEN=oauth:xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWITCH_NICK=твой_никнейм
```

Открой `config.yaml`:

```bash
nano config.yaml
```

Измени `channel` на название твоего канала:

```yaml
twitch:
  channel: "твой_канал"
```

### Шаг 4: Запустить

```bash
vibe run
```

Готово! Бот подключился к чату.

## Подробная настройка

### Получение Twitch OAuth Token

1. Перейди на https://twitchapps.com/kraken/
2. Нажми "Connect to Twitch"
3. Разреши доступ
4. Скопируй токен (начинается с `oauth:`)
5. Вставь в `.env` как `TWITCH_OAUTH_TOKEN=oauth:xxxxxxxx`

Важно: токен действует долго, но если бот отключится — получи новый.

### Настройка config.yaml

Полный список опций:

```yaml
vibe_coding:
  vote_threshold: 3    # голосов для одобрения (можно изменить)
  bot_nick: "VibeTCoder"  # ник бота
  time_format: "%Y-%m-%d %H:%M:%S"

twitch:
  channel: "твой_канал"       # НАЗВАНИЕ канала БЕЗ #
  irc_server: "irc.chat.twitch.tv"
  irc_port: 6667

database:
  path: "ideas.db"            # файл базы данных

agent:
  task_queue_path: "agent/task_queue.txt"
  branch_prefix: "feature/twitch-idea-"
  base_branch: "main"
```

## Использование

### Команды для зрителей

Зритель хочет предложить идею:

```
[IDEA] Add dark mode to settings, Complexity: M, Priority: high
```

Бот ответит что идея создана и сколько голосов нужно.

Зритель хочет проголосовать:

```
!vote #1 +1    # голосует ЗА
!vote #1 -1    # голосует ПРОТИВ
```

Посмотреть список идей:

```
!list         # все идеи
!pending    # только ожидающие
```

### Команды для стримера (в Twitch чате)

```
!approve #1    # одобрить идею #1 и добавить в очередь
!reject #1     # отклонить идею #1
```

### CLI команды (в терминале)

```bash
vibe ideas           # показать все идеи
vibe ideas --status pending  # толькоpending
vibe pending         # показать ожидающие (нужно 3+ голосов)
vibe approve 1      # approve через CLI
vibe reject 1       # reject через CLI
vibe stats          # статистика: сколько всего, pending, approved и т.д.
```

## Workflow (как это работает)

```
1. Зритель пишет в чате:
   [IDEA] Add dark mode, Complexity: M

2. Бот создаёт идею в базе, отвечает:
   @username, idea #1 created! Need 3 votes to approve.

3. Зрители голосуют:
   !vote #1 +1
   !vote #1 +1
   !vote #1 +1

4. Бот пишет когда набралось 3+ голосов:
   @author, idea #1 reached 3 votes! Type !approve #1 or !reject #1

5. Стример пишет:
   !approve #1

6. Бот одобряет и добавляет в очередь:
   Approved idea #1: Add dark mode
   Adding to execution queue...

7. (Автоматически) Создаётся branch:
   feature/twitch-idea-1-add-dark-mode

8. (Автоматически) Выполняется задача
   (пока не реализовано — ждёт Agent)

9. (Автоматически) Создаётся PR через gh CLI
```

## Требования

- **Python 3.11+** — проверь `python --version`
- **Twitch аккаунт** — для бота нужен аккаунт
- **gh CLI** (опционально) — для автоматических PR https://cli.github.com/

## Структура проекта

```
Twich_vibe_coding/
├── .env                    # Twitch credentials (НЕ коммитить!)
├── config.yaml             # Настройки
├── pyproject.toml         # Python пакет
├── setup.py              # Установщик
├── init.sh              # Скрипт быстрой установки
├── run.sh              # Скрипт запуска
├── README.md           # Этот файл
├── vibe_coding/
│   ├── __init__.py
│   ├── __main__.py
│   ├── config.py      # Загрузка конфигурации
│   ├── agent_queue.py # Очередь задач
│   ├── git_workflow.py # Git операции
│   ├── bot/          # Twitch бот
│   │   ├── connection.py  # IRC подключение
│   │   ├── parser.py     # Парсинг сообщений
│   │   └── handlers.py  # Обработчики команд
│   ├── cli/          # CLI интерфейс
│   │   └── main.py
│   └── db/          # Ба��а данных
│       ├── schema.py
│       ├── models.py
│       └── repository.py
├── agent/           # Очередь задач для Agent
│   └── task_queue.txt
└── tests/           # Тесты
```

## Частые вопросы

**Бот не подключается к чату**

Проверь:
1. Правильный ли токен в `.env`? (начинается с `oauth:`)
2. Правильный ли ник в `TWITCH_NICK`?
3. Существует ли канал в `config.yaml`?

**Как изменить порог голосов?**

Измени `vote_threshold` в `config.yaml`:
```yaml
vibe_coding:
  vote_threshold: 5  # теперь нужно 5 голосов
```

**Как посмотреть все идеи?**

```bash
vibe ideas           # все
vibe pending      # только ожидающие
vibe stats        # статистика
```

**Можно ли использовать без Twitch?**

Да! Базу данных и CLI можно использовать локально:
```bash
vibe ideas
vibe approve 1
vibe stats
```

**Нужен ли gh CLI для PR?**

Нет, опционально. Без gh CLI задачи выполняются в branch, но PR нужно создавать вручную.

## Лицензия

MIT License

Copyright (c) 2024 VibeCoder

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.