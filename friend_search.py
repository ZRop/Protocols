import requests
import re

# Настройки
ACCESS_TOKEN = '17753c0d17753c0d17753c0df71446da5d1177517753c0d7f3daf2a2f4f9ce677b121e2' 
VERSION = '5.131' 

def extract_user_id(profile_link):
    # Удаляем префиксы
    link = profile_link.strip()
    for prefix in ['https://', 'http://', 'vk.com/', '@']:
        if link.startswith(prefix):
            link = link[len(prefix):]
    
    if link.startswith('id'):
        try:
            return int(link[2:])
        except ValueError:
            pass
    method_url = 'https://api.vk.com/method/utils.resolveScreenName'
    params = {
        'screen_name': link,
        'access_token': ACCESS_TOKEN,
        'v': VERSION
    }
    
    response = requests.get(method_url, params=params)
    data = response.json()
    
    if 'response' in data and data['response']:
        if data['response']['type'] == 'user':
            return data['response']['object_id']
    
    raise ValueError("Не удалось определить user_id по ссылке")

def get_friends(user_id, access_token, version):
    """Получает список друзей пользователя"""
    method_url = 'https://api.vk.com/method/friends.get'
    params = {
        'user_id': user_id,
        'access_token': access_token,
        'v': version,
        'fields': 'first_name,last_name,sex,domain'  
    }
    
    response = requests.get(method_url, params=params)
    data = response.json()
    
    if 'error' in data:
        print(f"Ошибка: {data['error']['error_msg']}")
        return None
    
    return data['response']['items']

def main():
    profile_link = input("Введите ссылку на профиль ВКонтакте: ")
    
    try:
        user_id = extract_user_id(profile_link)
        print(f"Найден user_id: {user_id}")
        
        friends = get_friends(user_id, ACCESS_TOKEN, VERSION)
        
        if friends:
            print(f"\nНайдено {len(friends)} друзей:")
            print("-" * 60)
            
            for i, friend in enumerate(friends, 1):
                profile_link = f"https://vk.com/{friend.get('domain', 'id'+str(friend['id']))}"
                print(f"{i}. {friend['first_name']} {friend['last_name']}")
                print(f"   ID: {friend['id']}")
                print(f"   Профиль: {profile_link}")
                print(f"   Пол: {friend['sex']}")
                print("-" * 60)
        else:
            print("Не удалось получить список друзей или у пользователя нет друзей.")
            
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")

if __name__ == "__main__":
    main()
