from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)

auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")

print("Open this URL in browser:", auth_url)

creds = flow.run_local_server(port=8080, access_type="offline", prompt="consent")

with open("token.json", "w") as token:
    token.write(creds.to_json())

print("Authorization complete. token.json created.")
