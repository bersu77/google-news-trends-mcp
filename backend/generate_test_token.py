import jwt
import time

# Use the same secret from the .env file
SECRET_KEY = "app_secret_key_7X3nQ9pL2kR5vM8wS1tY6uJ4fZ9cX5bA0dE3gH7iK1oP4nM8jV2sW5rT9yU6fZ"
ALGORITHM = "HS256"

# Create a test token
payload = {
    "sub": "test-user-123",
    "email": "test@example.com",
    "aud": "authenticated",
    "exp": int(time.time()) + 3600,  # 1 hour expiration
    "iat": int(time.time())
}

token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
print(f"Test JWT token: {token}")
