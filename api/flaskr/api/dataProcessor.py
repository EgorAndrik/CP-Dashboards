import io

def process_data(file: io.BufferedIOBase):
    data = file.readline()

    return len(file.readlines())
