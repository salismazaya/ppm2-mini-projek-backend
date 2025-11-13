from django.conf import settings
import mimetypes, requests, json, base64
from functools import lru_cache
from dataclasses import dataclass

BASE_URL = settings.APPSCRIPT_STORAGE_API

class AppScriptError(Exception):
    pass


@dataclass
class UploadSuccess:
    status: str
    file_id: str
    filename: str


@dataclass
class DownloadSuccess:
    data: bytes
    filename: str
    mimetype: str


def upload_file(data: bytes, extension: str) -> UploadSuccess:
    mimetype = mimetypes.guess_type("mantap." + extension)[0]
    payload = {
        'extension': extension,
        'mimeType': mimetype,
        'data': base64.b64encode(data).decode(),
    }

    response = requests.post(BASE_URL, data = json.dumps(payload))
    response_json = json.loads(response.text)

    if response_json.get('status') == 'error':
        raise AppScriptError(response_json['message'])
    
    result = UploadSuccess(
        status = response_json['status'],
        file_id = response_json['fileId'],
        filename = response_json['fileName'],
    )

    return result


@lru_cache(maxsize = 12)
def download_file(file_id: str):
    response = requests.get(BASE_URL, params = {'fileId': file_id})
    response_json = json.loads(response.text)

    if response_json.get('status') == 'error':
        raise AppScriptError(response_json['message'])
    
    data = base64.b64decode(response_json['data'])
    mimetype = mimetypes.guess_type(response_json['filename'])[0]

    result = DownloadSuccess(
        data = data,
        filename = response_json['filename'],
        mimetype = mimetype
    )

    return result