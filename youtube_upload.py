import httplib2
import os
import random
import time
import datetime
from enum import Enum
import json

from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload

from google_auth_oauthlib.flow import InstalledAppFlow
import google.oauth2

httplib2.RETRIES = 1

MAX_RETRIES = 10

RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError)

RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

CLIENT_SECRETS_FILE = "client_secrets.json"
SAVED_CREDENTIALS_FILE = 'credentials.json'

YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

class PrivacyStatus(Enum):
  PUBLIC = 'public'
  PRIVATE = 'private'
  UNLISTED = 'unlisted'
  def __str__(self):
    return self.value

def get_authenticated_service():
  flow = InstalledAppFlow.from_client_secrets_file(
      CLIENT_SECRETS_FILE,
      scopes=[YOUTUBE_UPLOAD_SCOPE])

  credentials = None
  if os.path.exists(SAVED_CREDENTIALS_FILE):
    info = None
    with open(SAVED_CREDENTIALS_FILE, 'r') as f:
      info = json.load(f)
    credentials = google.oauth2.credentials.Credentials(
      token=info['token'],
      refresh_token=info['refresh_token'],
      token_uri=info['token_uri'],
      client_id=info['client_id'],
      client_secret=info['client_secret'],
      scopes=info['scopes'],
    )
    credentials.expiry = datetime.datetime.fromisoformat(info['expiry'])
    if credentials.expired:
      credentials.refresh(google.auth.transport.requests.Request())
  else:
    flow.run_local_server()
    credentials = flow.credentials

    info = { 
      'token': credentials.token,
      'refresh_token': credentials.refresh_token,
      'token_uri': credentials.token_uri,
      'client_id': credentials.client_id,
      'client_secret': credentials.client_secret,
      'scopes': credentials.scopes,
      'expiry': credentials.expiry.isoformat(),
    }
    with open(SAVED_CREDENTIALS_FILE, 'w') as f:
      json.dump(info, f)

  return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)

def initialize_upload(youtube, filename, title, description, category, keywords, privacy_status):
  print(f'Beginning upload of {filename} with title {title}...')
  body=dict(
    snippet=dict(
      title=title,
      description=description,
      tags=keywords,
      categoryId=category
    ),
    status=dict(
      privacyStatus=privacy_status.value,
      selfDeclaredMadeForKids=False
    )
  )
  insert_request = youtube.videos().insert(
    part=",".join(body.keys()),
    body=body,
    media_body=MediaFileUpload(filename, chunksize=-1, resumable=True)
  )

  return resumable_upload(insert_request)

def resumable_upload(insert_request):
  response = None
  error = None
  retry = 0
  while response is None:
    try:
      print("Uploading file...")
      status, response = insert_request.next_chunk()
      if response is not None:
        if 'id' in response:
          print(f"Video id {response['id']} was successfully uploaded.")
          return True
        else:
          print(f"The upload failed with an unexpected response: {response}")
          return False
    except HttpError as e:
      if e.resp.status in RETRIABLE_STATUS_CODES:
        error = f"A retriable HTTP error {e.resp.status} occurred:\n{e.content}" 
      else:
        raise
    except RETRIABLE_EXCEPTIONS as e:
      error = f"A retriable error occurred: {e}"

    if error is not None:
      print(error)
      retry += 1
      if retry > MAX_RETRIES:
        print("No longer attempting to retry.")
        return False

      max_sleep = 2 ** retry
      sleep_seconds = random.random() * max_sleep
      print(f"Sleeping {sleep_seconds} seconds and then retrying...")
      time.sleep(sleep_seconds)

def upload(filename, title, description, category=27, keywords=[], privacy_status=PrivacyStatus.PRIVATE):
  if not os.path.exists(filename):
    print("Please specify a valid filename")
    return
  youtube = get_authenticated_service()
  try:
    return initialize_upload(youtube, filename, title, description, category, keywords, privacy_status)
  except HttpError as e:
    print(f"An HTTP error {e.resp.status} occurred:\n{e.content}")
    return False