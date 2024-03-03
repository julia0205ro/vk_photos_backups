from vk_token import token
import requests
import json
import datetime
from tqdm import tqdm


class AUTORIZATION():
    '''
    User enters:
    - VK user ID;
    - token from Yandex.Disk Polygon
    '''
    def __init__(self):
        self.input_id = self.owner_id_input()
        self.input_Authorization = self.owner_Authorization_input()

    def owner_id_input(self):
        input_id = input('Please, input your vk id: ')
        return input_id

    def owner_Authorization_input(self):
        input_Authorization = input('Please, input your Yandex '
                                    'token: ')
        return input_Authorization

class VK_CLASS(AUTORIZATION):
    '''
    get vk profile photos
    get max size photos
    store photos info in json files
    '''
    api_base_url_vk = 'https://api.vk.com/method'

    def __init__(self):
        self.owner_id = myself.input_id

    def get_common_params(self):
        return {
            'access_token': token,
            'v': '5.199'
        }

    def get_profile_photo(self):
        params = self.get_common_params()
        self.album_id = 'profile'
        params.update({'owner_id': self.__init__(),
                       'album_id': self.album_id,
                       'photo_sizes': 1,
                       'extended': 1,
                       'rev': 1,
                       'count': 5})
        response = requests.get(
            f"{self.api_base_url_vk}/photos.get?", params=params)
        return response.json()

    def get_profile_photo_max_sizes_url(self):
        photos_info = self.get_profile_photo().get('response').get('items')
        my_dict_max_size = {}
        all_names_list = []
        for info in tqdm(photos_info):
            sizes = info.get('sizes')
            for size in tqdm(sizes):
                if size.get('type') == 'w':
                    all_names_list.append(size.get('url').split('/')[2])
                    my_dict_max_size[info.get('id')] = [size.get('url'),
                                                        size.get('type')]
            for size in tqdm(sizes):
                if size.get('url').split('/')[2] not in all_names_list:
                    if (size.get('width')/size.get('height') <= 3/2 and
                            size.get('type') == 'r'):
                        my_dict_max_size[info.get('id')] = [size.get('url'),
                                                            size.get('type')]
        return my_dict_max_size

    def get_profile_photo_names_list(self):
        names_dict = {}
        for each_dict in tqdm(self.get_profile_photo().get('response').get('items')):
            names_dict[each_dict['id']] = each_dict['likes']['count']
        result = {i: list(names_dict.values()).count(i)
                  for i in tqdm(list(names_dict.values()))}
        new_list = []
        for i in tqdm(result):
            if result[i] > 1:
                for k, v in tqdm(result.items()):
                    if v == result[i]:
                        new_list.append(k)
        second_list = []
        for i in tqdm(names_dict):
            if names_dict[i] in tqdm(new_list):
                second_list.append(i)
        for each_dict in tqdm(self.get_profile_photo().get('response').get('items')):
            for i in tqdm(second_list):
                if each_dict['id'] == i:
                    names_dict[each_dict['id']] = (each_dict['likes']['count'],
                                                   datetime.datetime.
                                                   fromtimestamp(float(each_dict['date'])).
                                                   strftime('%Y-%m-%d %H-%M-%S'))
        return names_dict

    def files_for_upload(self):
        first_dict = self.get_profile_photo_max_sizes_url()
        second_dict = self.get_profile_photo_names_list()
        for key, value in tqdm(second_dict.items()):
            if first_dict.get(key):
                first_dict[key] = [first_dict[key], value]
            else:
                first_dict[key] = value
        new_dict = first_dict.copy()
        return new_dict

    def create_file(self):
        a = self.files_for_upload()
        for i in tqdm(a):
            dict = {'file_name': str(a[i][1]),
                    'size': a[i][0][1]}
            with open(f"{str(a[i][1])}.json()", 'w') as f:
                json.dump(dict, f)

class YANDEX_DISK(VK_CLASS, AUTORIZATION):
    '''
    Store photos on Yandex disk
    '''
    base_url_yandex = 'https://cloud-api.yandex.net'

    def __init__(self):
        self.Authorization = myself.input_Authorization

    def create_dir(self):
        url_create_dir = f'{self.base_url_yandex}/v1/disk/resources'
        params = {
            'path': 'profile_photo'
        }
        headers = {
            'Authorization': self.Authorization
        }
        response = requests.put(url_create_dir, params=params, headers=headers)
        return response.json()

    def upload_photo(self):
        my_dict = super().files_for_upload()
        for i in tqdm(my_dict):
            image_url = my_dict[i][0]
            image_name = str(my_dict[i][1])
            url_for_upload = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
            params = {
                'url': image_url,
                'path': f'profile_photo/{image_name}'
            }
            headers = {
                'Authorization': self.Authorization
            }
            response_two = requests.post(url_for_upload,
                                         params=params,
                                         headers=headers)

if __name__ == '__main__':
    myself = AUTORIZATION()
    vk_client = VK_CLASS()
    yandex_client = YANDEX_DISK()
    vk_client.get_profile_photo()
    vk_client.get_profile_photo_max_sizes_url()
    vk_client.get_profile_photo_names_list()
    vk_client.files_for_upload()
    vk_client.create_file()
    yandex_client.create_dir()
    yandex_client.upload_photo()
