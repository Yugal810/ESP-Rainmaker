import pytest
import os
import json
from app import app, firmware_manager

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def test_firmware():
    # Create a test firmware file
    firmware_path = os.path.join(firmware_manager.firmware_folder, 'test_firmware.bin')
    with open(firmware_path, 'wb') as f:
        f.write(b'test firmware content')
    yield firmware_path
    # Cleanup
    if os.path.exists(firmware_path):
        os.remove(firmware_path)

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'

def test_version_endpoint(client, test_firmware):
    response = client.get('/version')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'version' in data
    assert 'hash' in data
    assert 'size' in data

def test_firmware_download(client, test_firmware):
    response = client.get('/firmware')
    assert response.status_code == 200
    assert response.mimetype == 'application/octet-stream'

def test_firmware_upload(client):
    data = {
        'firmware': (open(test_firmware, 'rb'), 'test_firmware.bin')
    }
    response = client.post('/upload', data=data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'message' in data
    assert 'hash' in data

def test_invalid_file_upload(client):
    data = {
        'firmware': (b'invalid content', 'test.txt')
    }
    response = client.post('/upload', data=data)
    assert response.status_code == 400

def test_api_key_validation(client):
    # Test without API key
    response = client.get('/version')
    assert response.status_code == 401

    # Test with invalid API key
    headers = {'X-API-Key': 'invalid_key'}
    response = client.get('/version', headers=headers)
    assert response.status_code == 401 