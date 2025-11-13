from django.conf import settings
from uuid import uuid4

def handle_uploaded_file(f):
    _, extension = f.name.split(".", 1)
    random_filename = str(uuid4()) + "." + extension

    yield random_filename

    with open(settings.BASE_DIR / random_filename, "wb") as destination:
        for chunk in f.chunks():
            destination.write(chunk)


def get_random_new_filename(old_filename: str):
    _, extension = old_filename.split(".", 1)
    random_filename = str(uuid4()) + "." + extension

    return random_filename