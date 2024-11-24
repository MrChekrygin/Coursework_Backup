import requests
import json
from tqdm import tqdm


class VKPhotoBackup:
    def __init__(self, vk_token, ya_token, vk_user_id, photo_count=5):
        self.vk_token = vk_token
        self.ya_token = ya_token
        self.vk_user_id = vk_user_id
        self.photo_count = photo_count
        self.vk_api_url = "https://api.vk.com/method/photos.get"
        self.ya_disk_url = "https://cloud-api.yandex.net/v1/disk/resources"

    def get_vk_photos(self):
        """Получить фотографии пользователя из ВКонтакте"""
        params = {
            'access_token': self.vk_token,
            'v': '5.131',
            'owner_id': self.vk_user_id,
            'album_id': 'profile',
            'extended': 1,
            'photo_sizes': 1,
            'count': self.photo_count,
        }
        response = requests.get(self.vk_api_url, params=params)
        response.raise_for_status()
        photos = response.json()['response']['items']

        # Формируем список фотографий с максимальным размером
        photo_list = []
        for photo in photos:
            max_size = max(photo['sizes'], key=lambda x: x['height'] * x['width'])
            photo_info = {
                'url': max_size['url'],
                'likes': photo['likes']['count'],
                'date': photo['date'],
                'size': max_size['type']
            }
            photo_list.append(photo_info)
        return photo_list

    def upload_to_yandex_disk(self, photos):
        """Загрузить фотографии на Яндекс.Диск"""
        headers = {"Authorization": f"OAuth {self.ya_token}"}
        folder_name = f"VK_Photos_{self.vk_user_id}"

        # Создаем папку
        requests.put(f"{self.ya_disk_url}?path={folder_name}", headers=headers)

        # Загружаем фотографии
        json_result = []
        for photo in tqdm(photos, desc="Uploading photos"):
            filename = f"{photo['likes']}.jpg"
            upload_url = f"{self.ya_disk_url}/upload"
            params = {"path": f"{folder_name}/{filename}", "url": photo['url']}
            response = requests.post(upload_url, headers=headers, params=params)
            response.raise_for_status()

            json_result.append({"file_name": filename, "size": photo['size']})
        return json_result

    def save_json(self, data, file_name='result.json'):
        """Сохранить данные в JSON-файл"""
        with open(file_name, 'w') as f:
            json.dump(data, f, indent=4)

    def run(self):
        """Запуск процесса резервного копирования"""
        print("Получение фотографий из ВКонтакте...")
        photos = self.get_vk_photos()

        print("Загрузка фотографий на Яндекс.Диск...")
        json_data = self.upload_to_yandex_disk(photos)

        print("Сохранение результатов в JSON-файл...")
        self.save_json(json_data)
        print("Процесс завершен успешно!")


if __name__ == "__main__":
    vk_token = input("Введите токен ВКонтакте: ")
    ya_token = input("Введите токен Яндекс.Диска: ")
    vk_user_id = input("Введите ID пользователя ВКонтакте: ")
    photo_count = int(input("Введите количество фотографий для сохранения (по умолчанию 5): ") or 5)

    backup = VKPhotoBackup(vk_token, ya_token, vk_user_id, photo_count)
    backup.run()
