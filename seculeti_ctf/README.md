# seculeti_ctf

Минимальный запуск (in-memory хранилище):

1) Docker Compose запускается из этой папки.
2) Приложение слушает порт 5000.

## Структура

- `seculeti_ctf/app` — код Clean Architecture.
- `seculeti_ctf/templates` — основной набор шаблонов.
- `front_end-demo` — legacy шаблоны (подхватываются автоматически).

## Локальный запуск

```cmd
cd /d %USERPROFILE%\PycharmProjects\seculetiCTF\seculeti_ctf
docker-compose up --build
```

## Примечания

- Для совместимости включен fallback на `front_end-demo` через Jinja ChoiceLoader.
- Все данные хранятся в памяти процесса и сбрасываются при перезапуске.
