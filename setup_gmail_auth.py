from src.core.services.gmail_auth import authenticate

if __name__ == "__main__":
    print("Starting Gmail OAuth setup...")
    creds = authenticate()
    print("Authentication successful!")
