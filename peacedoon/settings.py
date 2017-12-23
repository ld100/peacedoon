import os

from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

# TODO: Set environment variables to docker-compose.yml
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_DEFAULT_REGION = os.environ.get('AWS_DEFAULT_REGION')
AWS_REGION = AWS_DEFAULT_REGION
AWS_BUCKET = os.environ.get('AWS_BUCKET')

S3_FILEPATH = os.environ.get('S3_FILEPATH')
S3_HTTP_PREFIX = os.environ.get('S3_HTTP_PREFIX')