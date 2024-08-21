# from googleapiclient.discovery import build
# from google.oauth2 import service_account
#
# SERVICE_ACCOUNT_FILE = 'keys.json'
# SCOPES = ['https://docs.google.com/spreadsheets']
#
# creds = None
# creds = service_account.Credentials.from_service_account_file(
#     SERVICE_ACCOUNT_FILE, scopes=SCOPES)
#
# # The ID spreadsheet.
# SAMPLE_SPREADSHEET_ID = '1eE6fNUw2DRCEivBEGs-EfAF5lbHDJVzQhLODGZWZc6U'
#
# service = build('sheets', 'v4', credentials=creds)
#
# # Call the Sheets API
# sheet = service.spreadsheets()
#
# resource = {
#     "values": [
#         ["Item", "Cost", "Stocked", "Ship Date"],
#         ["Wheel", "$20.50", "4", "3/1/2016"],
#         ["Door", "$15", "2", "3/15/2016"],
#         ["Engine", "$100", "1", "3/20/2016"],
#         ["Totals", "=SUM(B2:B4)", "=SUM(C2:C4)", "=MAX(D2:D4)"]
#     ]
# }
#
# request = service.spreadsheets().values().append(spreadsheetId=SAMPLE_SPREADSHEET_ID,
#                                                  range="Sheet1!A1", valueInputOption="USER_ENTERED",
#                                                  body=resource)
# response = request.execute()
# print('Successfuly')


from googleapiclient.discovery import build
from google.oauth2 import service_account
from pprint import pprint as print
SERVICE_ACCOUNT_FILE = 'keys.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

creds = None
creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# The ID spreadsheet.
SAMPLE_SPREADSHEET_ID = 'secur_key'


service = build('sheets', 'v4', credentials=creds)

# Call the Sheets API
sheet = service.spreadsheets()
result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                            range="sales!A1:D25").execute()
values = result.get('values', [])
print(values)
