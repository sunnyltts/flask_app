import requests
from app import app

API_URL = 'http://3.7.179.205:5000'

class TestApp:

    def test_index(self):
        # client = app.test_client()    Not using this as the mongo is in a docker container
        response = requests.get(f'{API_URL}/')
        assert response.status_code == 200
        assert response.json() == { "message": "Welcome to sample.com" }

    def test_get_all_users(self):
        response = requests.get(f'{API_URL}/api/v1/users')
        assert response.status_code == 200

    def test_create_user(self):
        new_user = {"name": "Smith", "role": "Developer"}
        response = requests.post(f'{API_URL}/api/v1/users', json=new_user)
        resp_json = response.json()
        assert response.status_code == 200
        assert 'message' in resp_json
        assert resp_json['message'] == "User created successfully!"

    def test_delete_user(self):
        user_id = '644ec54d1c71532f400ce581'
        response = requests.delete(f'{API_URL}/api/v1/users/{user_id}')
        resp_json = response.json()
        print(resp_json)
        assert response.status_code == 200
        assert resp_json['message'] == f'User with id: {user_id} deleted successfully!'
