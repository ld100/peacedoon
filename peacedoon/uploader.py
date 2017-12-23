import os

import boto3
from boto3.s3.transfer import S3Transfer

import settings


class Uploader(object):
    """Amazon S3 File Uploader"""

    def __init__(self,
                 file_path,
                 s3_filepath=None,
                 s3_http_prefix=None,
                 s3_bucket=None,
                 s3_region=None,
                 aws_access_key=None,
                 aws_secret=None):
        self.file_path = file_path

        if s3_filepath:
            self.s3_filepath = s3_filepath
        else:
            self.s3_filepath = settings.S3_FILEPATH

        if s3_http_prefix:
            self.s3_http_prefix = s3_http_prefix
        else:
            self.s3_http_prefix = settings.S3_HTTP_PREFIX

        if s3_bucket:
            self.s3_bucket = s3_bucket
        else:
            self.s3_bucket = settings.AWS_BUCKET

        if s3_region:
            self.s3_region = s3_region
        else:
            self.s3_region = settings.AWS_REGION

        if aws_access_key:
            self.aws_access_key = aws_access_key
        else:
            self.aws_access_key = settings.AWS_ACCESS_KEY_ID

        if aws_secret:
            self.aws_secret = aws_secret
        else:
            self.aws_secret = settings.AWS_SECRET_ACCESS_KEY

        self.client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret
        )

    # TODO: Implement error handling
    def upload(self, file_path=None):
        if not file_path:
            file_path = self.file_path

        # Create direcotry if not exist
        self.__create_directory()

        file_name = os.path.basename(file_path)
        transfer = S3Transfer(self.client)
        transfer.upload_file(
            file_path,
            self.s3_bucket,
            self.s3_filepath + "/" + file_name
        )
        return "%s/%s/%s" % (self.s3_http_prefix, self.s3_filepath, file_name)

    def __create_directory(self, directory=None):
        if not directory:
            directory = self.s3_filepath

        response = self.client.put_object(
            Bucket=self.s3_bucket,
            Key="%s/" % directory,
        )

        return response
