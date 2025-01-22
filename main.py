import os
import requests
import json
import datetime

# Библиотека для работы с API Google Диска
from pydrive.drive import GoogleDrive

# Добавление индикатора прогресса
from quickstart import gauth
from tqdm import tqdm

from configparser import ConfigParser

urlsconf = 'config.ini'
config = ConfigParser()
config.read(urlsconf)


class VK:
    """Класс для получения фотографий профиля и
    сохранения фотографий в максимальном размере в json-файл"""

    def __init__(self, access_token: str, user_id: str, version: str = '5.199') -> None:
        """Передача обязательных параметров API VK:
        access_token и используемая версия API"""

        self.access_token: str = access_token
        self.version: str = version
        self.user_id: str = user_id
        self.params: dict = {'access_token': self.access_token, 'v': self.version}

    def get_profile_photo_info(self) -> dict:
        """Получение информации о фотографиях профиля
        с помощью метода photos.get"""

        url: str = 'https://api.vk.com/method/photos.get'
        album_id: str = 'profile'
        params: dict = {
            'owner_id': self.user_id,
            'album_id': album_id,
            'extended': 1,
        }

        response = requests.get(url, params={**self.params, **params})
        # Информации обо всех полученных фотографиях
        images_info: dict = response.json()
        # Список информации о конкретных фотографиях
        images_list: list = images_info.get('response').get('items')

        # Сохранение информации по фотографиям в json-файл с результатами
        with open('photos_info.json', 'w', encoding='utf-8') as file:
            json.dump(images_info, file, indent=2)

        # Получение url и имени конкретной фотографии
        images_url: list = []  # Создание списка url картинок
        names_list: list = []  # Создание списка имен картинок

        for image in tqdm(images_list,
                          desc='Получение url и имени фотографии'):
            image_url: str = image.get('orig_photo').get('url')
            images_url.append(image_url)

            # Получение кол-ва лайков для имени фотографии
            image_likes: int = image.get('likes').get('count')
            if image_likes not in names_list:
                names_list.append(image_likes)
            else:  # Получение даты для имени фотографии, если кол-во лайков одинаково
                image_date: str = (datetime.datetime.fromtimestamp(image.get('date')).
                                   strftime('%Y-%m-%d'))
                image_name: str = f'{image_likes}, {image_date}'
                names_list.append(image_name)

        # Создание словаря, в котором имя фотографии является ключом,
        # ссылка на фотографию - значением
        dict_photo: dict = dict(zip(names_list, images_url))
        print(dict_photo)

        return dict_photo

    def get_photos(self, directory) -> None:
        """Скачивание фотографии"""

        # Создание директории для скаченных фотографий
        if not os.path.exists(directory):
            os.makedirs(directory)

        for key, value in tqdm(self.get_profile_photo_info().items(),
                               desc='Скачивание фотографий'):
            response = requests.get(value)
            with open(f'{directory}/{key}.jpg', 'wb') as file:
                file.write(response.content)
                print(response.status_code)


class Yandex:
    """Класс для сохранения фотографии на Я.Диске"""

    def __init__(self, Authorization: str) -> None:
        self.Authorization = Authorization
        self.headers: dict = {'Authorization': f'OAuth {self.Authorization}'}

    def create_foldef(self) -> dict:
        """Создание папки на Я.Диске"""

        url: str = 'https://cloud-api.yandex.net/v1/disk/resources'
        path: str = 'profile_photos'
        params: dict = {
            'path': path
        }

        response = requests.put(url, params={**params}, headers={**self.headers})
        response_json: dict = response.json()

        return response_json

    def upload_photos(self, directory) -> None:
        """Загрузить фотографии профиля на Я.Диск"""

        # Получение URL для обращения к загрузчику файлов
        url: str = 'https://cloud-api.yandex.net/v1/disk/resources/upload'

        for filename in tqdm(os.listdir(directory),
                        desc='Загрузка фотографии на Я.Диск'):
            path: str = f'profile_photos/{filename}'
            response = requests.get(url, params={'path': path},
                                    headers={**self.headers})
            url_for_upload: str = response.json().get('href')

            # Загрузка файла на полученный URL
            with open(f'{directory}/{filename}', 'rb') as photo:
                response = requests.put(url_for_upload, files={'file': photo})
                print(response.status_code)


class Google:
    """Класс для сохранения фотографии на Google Диске"""

    def __init__(self, drive) -> None:
        """Аутентификации через OAuth2"""

        self.drive = GoogleDrive(gauth)

    def get_folder_id(self) -> str:
        """Получение id папки на Google Диске
        для загрузки фотографий профиля"""

        folder_metadata: dict = {
            'title': 'profile_photo_folder',
            'mimeType': 'application/vnd.google-apps.folder'
        }
        file_list: list = (self.drive.ListFile({'q': "'root' in parents and trashed=false"})
                           .GetList())

        # проверка на наличие папки на Google Диске
        for file in tqdm(file_list,
                         desc='Поиск папки на Google Диске и получение id'):
            if folder_metadata.get('title') in file.get('title'):
                return file.get('id')
        else:
            folder = self.drive.CreateFile(folder_metadata)
            folder.Upload()
            return folder.get('id')

    def upload_photos(self, directory) -> None:
        """Загрузка файла в папку на Google Диске"""

        for filename in tqdm(os.listdir(directory),
                        desc='Загрузка файла на Google Диск'):
            file_metadata: dict = {
                'title': filename,
                'parents': [{'id': self.get_folder_id()}]
            }
            file = self.drive.CreateFile(file_metadata)
            file.SetContentFile(f'{directory}/{filename}')
            file.Upload()

            print(f'Файл {file.get("title")} загружен с ID: {file.get("id")}')


# Запуск кода
if __name__ == '__main__':
    directory_profile_photos = 'profile_photos'

    # Создание экземпляра класса VK
    access_token: str = config.get('vk_token', 'access_token')
    user_id: str = input('Input your vk user id: ')
    vk = VK(access_token, user_id)

    # Выхов методов класса VK
    vk.get_photos(directory_profile_photos)

    Authorization: str = input('Input your Yandex OAuth-token: ')

    # Создание экземпляра класса Yandex
    yandex = Yandex(Authorization)

    # Вызов методов класса Yandex
    yandex.create_foldef()
    yandex.upload_photos(directory_profile_photos)

    # Создание экземпляра класса Google
    google = Google(gauth)

    # Вызов методов класса Google
    google.upload_photos(directory_profile_photos)
