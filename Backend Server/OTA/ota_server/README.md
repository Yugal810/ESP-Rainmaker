# Industrial OTA Update Server

A robust, production-ready Over-The-Air (OTA) update server for ESP32 devices.

## Features

- Secure firmware distribution
- Version control and metadata
- Automatic firmware backups
- Rate limiting
- API key authentication
- Health monitoring
- Comprehensive logging
- CORS support
- File integrity verification (SHA-256)
- Configurable settings

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the server:
- Copy `config/config.yaml.example` to `config/config.yaml`
- Update the configuration as needed

4. Set up environment variables:
```bash
export API_KEY=your_secure_api_key  # Required for authentication
```

## Usage

1. Start the server:
```bash
python app.py
```

2. API Endpoints:

- `GET /health` - Health check
- `GET /version` - Get current firmware version and metadata
- `GET /firmware` - Download latest firmware
- `POST /upload` - Upload new firmware

3. Example API calls:

```bash
# Check version
curl -H "X-API-Key: your_api_key" http://localhost:8081/version

# Upload firmware
curl -X POST -H "X-API-Key: your_api_key" \
     -F "firmware=@path/to/firmware.bin" \
     http://localhost:8081/upload

# Download firmware
curl -H "X-API-Key: your_api_key" \
     -O http://localhost:8081/firmware
```

## Security

- API key authentication required for all endpoints
- Rate limiting to prevent abuse
- File size limits
- Secure file handling
- Automatic firmware backups

## Testing

Run the test suite:
```bash
pytest tests/
```

## Monitoring

- Logs are stored in `logs/ota_server.log`
- Health check endpoint for monitoring
- Detailed error logging
- Firmware backup system

## Configuration

Key configuration options in `config/config.yaml`:

- Server settings (host, port, SSL)
- Firmware settings (max size, backup)
- Security settings (API key, rate limits)
- Logging settings
- Notification settings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License 