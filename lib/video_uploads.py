import pickle
import os
import datetime
import json
import http.client
import httplib2
import random
import time
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request


def create_service():
    client_secret_file = "client_secrets.json"
    api_name = "youtube"
    api_version = "v3"
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]

    CLIENT_SECRET_FILE = client_secret_file
    API_SERVICE_NAME = api_name
    API_VERSION = api_version
    SCOPES = [scope for scope in scopes[0]]

    cred = None

    pickle_file = f"token_{API_SERVICE_NAME}_{API_VERSION}.pickle"

    if os.path.exists(pickle_file):
        with open(pickle_file, "rb") as token:
            cred = pickle.load(token)

    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            cred = flow.run_local_server()

        with open(pickle_file, "wb") as token:
            pickle.dump(cred, token)

    try:
        service = build(API_SERVICE_NAME, API_VERSION, credentials=cred)
        return service
    except Exception as e:
        print("Unable to connect.")
        print(e)
        return None


def upload_video(args, service, utc_time):
    """
    Creates request body for YouTube api for video
    """
    with open(args["metadata"].name) as metadata_json:
        metadata = json.load(metadata_json)

        upload_body = {
            "snippet": {
                "title": metadata["Video"]["Title"],
                "description": metadata["Video"]["Description"],
                "tags": metadata["Video"]["Tags"],
                "categoryId": 20,
            },
            "status": {
                "privacyStatus": "private",
                "publishAt": utc_time.isoformat(),
                "selfDeclaredMadeForKids": False,
            },
        }

    media_file = MediaFileUpload(
        args["video"].name, chunksize=(1024 * 1024), resumable=True
    )

    print("Starting video upload")
    response_upload = (
        service.videos()
        .insert(part="snippet,status", body=upload_body, media_body=media_file)
        .execute()
    )

    resumable_upload(response_upload)

    print("Setting thumbnail on video")
    service.thumbnails().set(
        videoId=response_upload.get("id"),
        media_body=MediaFileUpload(args["thumbnail"].name),
    ).execute()

    print("Done")


def resumable_upload(insert_request):

    if "next_chunk" not in insert_request:
        return

    httplib2.RETRIES = 1

    MAX_RETRIES = 10

    RETRIABLE_EXCEPTIONS = (
        httplib2.HttpLib2Error,
        IOError,
        http.client.NotConnected,
        http.client.IncompleteRead,
        http.client.ImproperConnectionState,
        http.client.CannotSendRequest,
        http.client.CannotSendHeader,
        http.client.ResponseNotReady,
        http.client.BadStatusLine,
    )
    RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

    response = None
    error = None
    retry = 0
    while response is None:
        try:
            print("Uploading file...")
            status, response = insert_request.next_chunk()
            if response is not None:
                if "id" in response:
                    print("Video id '%s' was successfully uploaded." % response["id"])
                else:
                    print(
                        "The upload failed with an unexpected response: %s" % response
                    )
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = "A retriable HTTP error %d occurred:\n%s" % (
                    e.resp.status,
                    e.content,
                )
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = "A retriable error occurred: %s" % e

        if error is not None:
            print(error)
            retry += 1
            if retry > MAX_RETRIES:
                exit("No longer attempting to retry.")

            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            print("Sleeping %f seconds and then retrying..." % sleep_seconds)
            time.sleep(sleep_seconds)