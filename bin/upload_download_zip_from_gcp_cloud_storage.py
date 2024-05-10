import io
import os
import pathlib

from dotenv import load_dotenv
from google.cloud import storage
from google.oauth2 import service_account
from zipfile import ZipFile, ZipInfo


load_dotenv()

GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID')
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')
STORAGE_BUCKET_NAME = os.getenv('STORAGE_BUCKET_NAME')

TARGET_DIRECTORY = os.getenv('TARGET_DIRECTORY')
SOURCE_DIRECTORY = os.getenv('SOURCE_DIRECTORY')

credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)

client = storage.Client(
    project=GCP_PROJECT_ID,
    credentials=credentials
)


def upload():
    source_dir = pathlib.Path(SOURCE_DIRECTORY)

    archive = io.BytesIO()
    with ZipFile(archive, 'w') as zip_archive:
        for file_path in source_dir.iterdir():
            with open(file_path, 'r') as file:
                zip_entry_name = file_path.name
                zip_file = ZipInfo(zip_entry_name)
                zip_archive.writestr(zip_file, file.read())

    archive.seek(0)

    object_name = 'super-important-data-v1'
    bucket = client.bucket(STORAGE_BUCKET_NAME)

    blob = storage.Blob(object_name, bucket)
    blob.upload_from_file(archive, content_type='application/zip')


def download():
    target_dir = pathlib.Path(TARGET_DIRECTORY)

    object_name = 'super-important-data-v1'
    bucket = client.bucket(STORAGE_BUCKET_NAME)

    blob = storage.Blob(object_name, bucket)
    object_bytes = blob.download_as_bytes()

    archive = io.BytesIO()
    archive.write(object_bytes)

    with ZipFile(archive, 'w') as zip_archive:
        zip_archive.extractall(target_dir)
    

if __name__ == '__main__':
    upload()
    download()

