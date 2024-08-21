import datetime

from googleapiclient.discovery import build
from google.oauth2 import service_account

SERVICE_ACCOUNT_FILE = 'keys.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

creds = None
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# The ID spreadsheet.
SAMPLE_SPREADSHEET_ID = '1eE6fNUw2DRCEivBEGs-EfAF5lbHDJVzQhLODGZWZc6U'

service = build('sheets', 'v4', credentials=creds)

# Call the Sheets API
sheet = service.spreadsheets()

resource = {
  # "majorDimension": "ROWS",
  "values": [
    ["F.I.O", "Jamshid Jabborov"],
    ['created_at', datetime.datetime.now().strftime('%Y-%m-%d')]
  ]
}

request = service.spreadsheets().values().append(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                                 range="sales!A1", valueInputOption="USER_ENTERED",
                                                  body=resource)
response = request.execute()

print('Successfuly')
