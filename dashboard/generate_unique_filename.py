import uuid

def generate_unique_filename(extension):
    # Generate a unique filename using UUID
    unique_filename = str(uuid.uuid4()) + extension
    return unique_filename