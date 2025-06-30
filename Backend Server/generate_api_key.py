import secrets

# Generate a secure API key
api_key = secrets.token_hex(32)

# Generate a secure Flask secret key
flask_secret_key = secrets.token_hex(32)

print("\nGenerated API Key:")
print(api_key)
print("\nGenerated Flask Secret Key:")
print(flask_secret_key)
print("\nAdd these keys to your .env files:")
print("\n1. Main server .env file:")
print("OTA_API_KEY=" + api_key)
print("\n2. OTA server .env file:")
print("API_KEY=" + api_key)
print("FLASK_SECRET_KEY=" + flask_secret_key)
print("FLASK_ENV=development") 