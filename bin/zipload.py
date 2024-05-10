# https://lewiskori.com/blog/how-to-programatically-unzip-files-uploaded-to-google-cloud-storage-buckets/
import io
from zipfile import ZipFile, is_zipfile

from google.cloud import storage
from google.oauth2 import service_account

# declare unzipping function

def zipextract(zipfilename_with_path):

    # auth config
    SERVICE_ACCOUNT_FILE = 'credentials.json'
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE)

    bucketname = 'your-bucket-id'

    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.get_bucket(bucketname)

    destination_blob_pathname = zipfilename_with_path

    blob = bucket.blob(destination_blob_pathname)

    zipbytes = io.BytesIO(blob.download_as_string())
    # download_as_string
    # https://cloud.google.com/python/docs/reference/storage/latest/google.cloud.storage.blob.Blob
    # (Deprecated) Download the contents of this blob as a bytes object.
    # Download the contents of this blob as text (not bytes). download_as_text
    # https://docs.python.org/3/library/io.html
    # io — Core tools for working with streams
    # io.StringIO


    if is_zipfile(zipbytes):
        with ZipFile(zipbytes, 'r') as myzip:
            for contentfilename in myzip.namelist():
                contentfile = myzip.read(contentfilename)

                # unzip pdf files only, leave out if you don't need this.
                if '.pdf' in contentfilename.casefold():

                    output_file = f'./{contentfilename.split("/")[-1]}'
                    outfile = open(output_file, 'wb')
                    outfile.write(contentfile)
                    outfile.close()

                    blob = bucket.blob(
                        f'{zipfilename_with_path.rstrip(".zip")}/{contentfilename}'
                    )
                    with open(output_file, "rb") as my_pdf:
                        blob.upload_from_file(my_pdf)

                    # make the file publicly accessible
                    blob.make_public()
    print('done running function')

if __name__ == '__main__':
    zipfilename_with_path = input('enter the zipfile path: ')
    zipextract(zipfilename_with_path)