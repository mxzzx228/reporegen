import os
from github import Github
import base64
import requests
from github import Github, GithubException

from github import Github, GithubException

# Прямо в коде указываем токен
GITHUB_TOKEN = "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"

# Авторизация
g = Github(GITHUB_TOKEN)

try:
    # Указываем пользователя явно
    user = g.get_user("opopopopop222")

    print(f"Здравствуйте, {user.login}!")

    # Получаем список репозиториев
    repos = user.get_repos()

    if not repos:
        print("❌ Репозитории не найдены или у вас нет к ним доступа.")

    for repo in repos:
        print(repo.full_name)

except GithubException as e:
    print(f"❌ GitHub вернул ошибку: {e.status} — {e.data}")
    exit(1)
except Exception as e:
    print(f"❌ Ошибка: {e}")
    exit(1)

# Эта часть будет выполнена только если всё выше успешно
try:
    all_repos = user.get_repos()  # <-- Теперь user определён
    for repo in all_repos:
        print(repo.name)
except NameError:
    print("❌ Не удалось получить доступ к пользователю. Проверь токен.")

# === Функция поиска всех удаленных файлов ===
def get_all_deleted_files(repo):
    deleted_files = []
    try:
        commits = repo.get_commits()
        for commit in commits:
            for file in commit.files:
                if file.status == "removed":
                    deleted_files.append({
                        'filename': file.filename,
                        'commit_sha': commit.parents[0].sha if commit.parents else None,
                        'repo': repo.full_name
                    })
    except Exception as e:
        print(f"Ошибка при обработке {repo.name}: {e}")
    return deleted_files

# === Восстановление и загрузка файла ===
def restore_and_upload_file(repo, filename, commit_sha):
    try:
        print(f"Восстанавливаю файл: {filename} в {repo.full_name}")

        old_content = repo.get_contents(filename, ref=commit_sha)
        if isinstance(old_content, list):
            old_content = old_content[0]

        download_url = old_content.download_url
        response = requests.get(download_url)
        if response.status_code != 200:
            print(f"Не удалось загрузить {filename} по download_url")
            return

        decoded_content = response.content

        # Проверяем, существует ли уже такой файл
        try:
            current_content = repo.get_contents(filename, ref=BRANCH_NAME)
            if isinstance(current_content, list):
                current_content = current_content[0]
            print(f"Файл {filename} уже существует в {repo.full_name}, пропускаем.")
            return
        except:
            pass  # Продолжаем, если файла нет

        # Заливаем обратно
        repo.create_file(
            path=filename,
            message=f"Restored file: {filename}",
            content=decoded_content,
            branch=BRANCH_NAME
        )
        print(f"Файл {filename} успешно восстановлен в {repo.full_name}")

    except Exception as e:
        print(f"Не удалось восстановить {filename} в {repo.full_name}: {e}")

# === Сканирование ===
def scan_repositories():
    print("Начинаю сканирование репозиториев...")
    all_repos = user.get_repos()

    for repo in all_repos:
        print(f"Проверяю репозиторий: {repo.full_name}")
        deleted_files = get_all_deleted_files(repo)

        if not deleted_files:
            print(f"Удалённых файлов в {repo.full_name} нет.")
            continue

        print(f"Найдено {len(deleted_files)} удалённых файлов в {repo.full_name}")
        for df in deleted_files:
            restore_and_upload_file(repo, df['filename'], df['commit_sha'])

# === Точка входа ===
if __name__ == "__main__":
    scan_repositories()
    print("✅ Все репозитории проверены. Работа завершена.")
