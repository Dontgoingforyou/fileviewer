import io
import os
import zipfile

import requests
from django.shortcuts import render, redirect
from django.http import HttpResponse
from dotenv import load_dotenv

load_dotenv()

YANDEX_CLIENT_ID = os.getenv('YANDEX_CLIENT_ID')
YANDEX_CLIENT_SECRET = os.getenv('YANDEX_CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')

auth_link = f"https://oauth.yandex.ru/authorize?response_type=code&client_id={YANDEX_CLIENT_ID}&redirect_uri={REDIRECT_URI}"

YANDEX_DISK_API_URL = 'https://cloud-api.yandex.net/v1/disk/public/resources'

def index(request):
    return render(request, 'fileviewer/index.html', {'auth_link': auth_link})


def files(request):
    if request.method == 'POST':
        public_key = request.POST.get('public_key')
        access_token = request.session.get('access_token')

        if not access_token:
            print("Токен доступа не найден в сеансе.")
            return HttpResponse('Ошибка: требуется авторизация.', status=401)

        headers = {
            'Authorization': f'OAuth {access_token}',
        }

        response = requests.get(f'{YANDEX_DISK_API_URL}?public_key={public_key}', headers=headers)

        if response.status_code == 200:
            files = response.json().get('_embedded').get('items')

            # Фильтрация по типу файлов
            file_type_filter = request.POST.get('file_type')
            if file_type_filter:
                files = [file for file in files if file_type_filter in file.get('mime_type', '')]

            for file in files:
                file['download_url'] = file.get('file')

            return render(request, 'fileviewer/files.html', {'files': files})
        else:
            return HttpResponse(f'Ошибка при получении файлов: {response.text}', status=response.status_code)

    return HttpResponse('Метод не поддерживается.', status=405)


def oauth_callback(request):
    """Получение access_token из параметров URL"""
    code = request.GET.get('code')

    if not code:
        return HttpResponse('Ошибка: code не получен.', status=400)

    token_url = 'https://oauth.yandex.ru/token'
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': YANDEX_CLIENT_ID,
        'client_secret': YANDEX_CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
    }

    token_response = requests.post(token_url, data=token_data)

    if token_response.status_code == 200:
        access_token = token_response.json().get('access_token')
        request.session['access_token'] = access_token
        print(f"Токен успешно получен и сохранен в сессии: {access_token}")
        return redirect('index')
    else:
        return HttpResponse(f'Ошибка при получении токена: {token_response.text}', status=token_response.status_code)


def download_multuple_files(request):
    if request.method == 'POST':
        selected_files = request.POST.getlist('selected_files')
        if not selected_files:
            return HttpResponse('Ошибка: файлы не выбраны.', status=400)

        # Создание ZIP архива
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for file_url in selected_files:
                file_response = requests.get(file_url)
                if file_response.status_code == 200:
                    file_name = file_url.split('/')[-1]
                    zip_file.writestr(file_name, file_response.content)

        zip_buffer.seek(0)

        # Отправка ZIP-архива пользователю
        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="files.zip"'
        return response
    else:
        return HttpResponse('Метод не поддерживается.', status=405)