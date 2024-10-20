import os

import requests
from django.shortcuts import render
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
            return HttpResponse('Ошибка: требуется авторизация.', status=401)

        headers = {
            'Authorization': f'OAuth {access_token}',
        }

        response = requests.get(f'{YANDEX_DISK_API_URL}?public_key={public_key}', headers=headers)

        if response.status_code == 200:
            files = response.json().get('_embedded').get('items')

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
        return HttpResponse('Токен успешно получен и сохранен в сессии')
    else:
        return HttpResponse(f'Ошибка при получении токена: {token_response.text}', status=token_response.status_code)