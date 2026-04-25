# Twitch Vibe Coding

Система параллельных задач с approval-воркфлоу для стримов на Twitch.

Зрители предлагают идеи в чате, голосуют за них, а ты (стример) утверждаешь идеи на выполнение. After approval, задача уходит в очередь и выполняется в отдельной ветке с автоматическим PR.

## Быстрый старт (1 минута)

```bash
# 1. Клонировать и перейти в папку
git clone <your-repo> && cd vibe_coding

# 2. Запустить (ONE COMMAND)
chmod +x init.sh && ./init.sh

# 3. Отредактировать настройки
nano .env        # Twitch credentials
nano config.yaml # Ваш канал

# 4. Запустить бота
vibe run
```

Или ещё проще:

```bash
pip install -e . && vibe init
```

## Возможности

- **Предложение идей** — зрители пишут `[IDEA]` в чате
- **Голосование** — `!vote +1` / `!vote -1`
- **Approval воркфлоу** — утверждение или отклонение идей
- **Git интеграция** — автоматические branch → PR
- **CLI управления** — управление очередью из терминала

## Установка

### Вариант 1: pip (рекомендуется)

```bash
pip install -e .
vibe init
```

### Вариант 2: Скрипты

```bash
chmod +x init.sh && ./init.sh
```

### Вариант 3: Вручную

```bash
pip install aiosqlite pyyaml typer python-dotenv rich
python -c "from vibe_coding.cli.main import app; app(['init'])"
```

### Настройка .env

Получить токен: https://twitchapps.com/kraken/

```bash
TWITCH_OAUTH_TOKEN=oauth:xxxxxxxxxxxx
TWITCH_NICK=your_username
```

### Настройка config.yaml

```yaml
vibe_coding:
  vote_threshold: 3

twitch:
  channel: "your_channel"
```

## Команды
  branch_prefix: "feature/twitch-idea-"
  base_branch: "main"
```

### 4. Запуск бота

```bash
python -m vibe_coding.bot.listener
```

## Использование

### Команды для зрителей

```
[IDEA] Add dark mode, Complexity: M, Priority: high
```

```
!vote #1 +1        # голосовать за
!vote #1 -1        # против
!list              # список идей
!pending          # ожидающие
```

### Команды для стримера (в чате)

```
!approve #1         # утвердить
!reject #1          # отклонить
```

### CLI команды

```bash
# Список всех идей
vibe ideas

# Список ожидающих
vibe pending

# Утвердить идею
vibe approve 1

# Отклонить идею
vibe reject 1

# Статистика
vibe stats
```

## Workflow

```
Зритель: [IDEA] Add dark mode, Complexity: M
Зрители: !vote #1 +1 (нужно 3+ голосов)
Бот: @username, idea #1 reached 3 votes! Type !approve #1 or !reject #1
Стример: !approve #1
Бот: Approved idea #1: Add dark mode
       Adding to execution queue...

[Background Agent]
→ Создаёт branch: feature/twitch-idea-1-add-dark-mode
→ Выполняет задачу
→ Создаёт PR через gh CLI
→ Ждёт merge
```

## Установка CLI команды

```bash
# Добавить в PATH
export PATH="$PATH:$(pwd)"

# Или создать алиас в ~/.zshrc
alias vibe='python -m vibe_coding.cli.main'
```

## Требования

- Python 3.11+
- Twitch аккаунт бота
- gh CLI для PR (опционально)

## Структура проекта

```
vibe_coding/
├── config.yaml          # Конфигурация
├── .env                # Secrets (не коммитить)
├── pyproject.toml
├── vibe_coding/
│   ├── bot/           # Twitch бот
│   │   ├── connection.py
│   │   ├── parser.py
│   │   └── handlers.py
│   ├── cli/          # CLI интерфейс
│   │   └── main.py
│   ├── db/           # База данных
│   │   ├── schema.py
│   │   ├── models.py
│   │   └── repository.py
│   ├── agent_queue.py # Очередь задач
│   └── git_workflow.py # Git операции
├── agent/
│   └── task_queue.txt # Очередь задач
└── tests/
```

## ЧаВо

**Как получить Twitch OAuth токен?**
→ https://twitchapps.com/kraken/

**Как установить gh CLI?**
→ https://cli.github.com/

**Бот не подключается?**
Проверь `.env` файл и убедись что токен валидный.

**Как изменить порог голосов?**
→ Измени `vote_threshold` в `config.yaml`

## Лицензия

MIT