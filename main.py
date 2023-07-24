import requests
from io import BytesIO
from pypdf import PdfReader, PdfWriter


def send_to_ocr(name, stream):
    """Sends the prepared stream to OCR API via POST request, extracts text"""

    api_url = 'https://api.ocr.space/parse/image'
    # Note: do not publish the key!
    api_key = ''

    payload = {
        'apikey': api_key
    }

    # Find size of PDF file
    file_size = stream.__sizeof__()
    # Must be less than 1 MB
    if file_size > 1024 ** 2:
        raise Exception(f'API request failed: page too large, {file_size} bytes')

    # Send the request
    r = requests.post(api_url, files={name: stream}, data=payload)

    # Check if successful
    if r.status_code != 200:
        raise Exception(f'API request failed: {r.status_code}, {r.text}')

    # Try extracting text from JSON
    json = r.json()
    try:
        return json['ParsedResults'][0]['ParsedText']
    except KeyError:
        raise Exception(f'API request failed: {r.status_code}, {r.text}')


def extract_text(pdf):
    """
    Extracts text from PDF file at given URL
    Can use a stream instead
    Uses external API if regular extraction fails
    Raises an exception if that fails too
    pdf - pdf url or stream
    """

    # Get the file from URL
    reader = PdfReader(pdf)
    number_of_pages = len(reader.pages)
    print(f'{number_of_pages} pages')

    # Try to extract text via pypdf
    text = ''
    for i in range(0, number_of_pages):
        page = reader.pages[i]
        text += page.extract_text()

    # Note: find a way to check if this is enough or OCR is required.
    # Assumed it isn't enough for now
    if False:
        return text

    # Try extracting the text with API requests
    # Page by page
    text = ''
    for i in range(0, number_of_pages):
        page = reader.pages[i]
        writer = PdfWriter()
        # Add a single page
        writer.add_page(page)
        size_ok = True
        with BytesIO() as bytes_stream:
            writer.write(bytes_stream)
            bytes_stream.seek(0)

            # Find size of PDF file
            file_size = bytes_stream.__sizeof__()
            # Must be less than 1 MB
            if file_size > 1024 ** 2:
                size_ok = False
            else:
                # OCR the page
                text += send_to_ocr(f'{pdf}_p{i}.pdf', bytes_stream)
        if not size_ok:
            # If size is too big, try to compress
            for p in writer.pages:
                p.compress_content_streams()
            # writer.remove_images()

            with BytesIO() as bytes_stream:
                writer.write(bytes_stream)
                bytes_stream.seek(0)

                # Find size of PDF file
                file_size = bytes_stream.__sizeof__()
                # Must be less than 1 MB
                if file_size > 1024 ** 2:
                    raise Exception(f'API request failed: page {i} too large, {file_size} bytes')
                else:
                    # OCR the page
                    text += send_to_ocr(f'{pdf}_p{i}.pdf', bytes_stream)

    return text


if __name__ == '__main__':
    # Note: for testing, replace these
    file_urls = [
        'C:/Users/ionsh/Downloads/GeoBase_NHNC1_Data_Model_UML_EN.pdf',
        'C:/Users/ionsh/Downloads/8.pdf',
        'C:/Users/ionsh/Downloads/0.pdf'
    ]

    file_urls_remote = [
        'https://raw.githubusercontent.com/py-pdf/pypdf/main/resources/GeoBase_NHNC1_Data_Model_UML_EN.pdf',
        'https://www.africau.edu/images/default/sample.pdf'
    ]

    # Local URLs
    if True:
        for j in range(len(file_urls)):
            try:
                print(f'Test {j}: extracted \'{extract_text(file_urls[j])}\'')
            except Exception as ex:
                print(f'Test {j} failed: {ex}')

    # Remote URLs
    if True:
        for j in range(len(file_urls_remote)):
            try:
                r = requests.get(url=file_urls_remote[j], timeout=120)
                with BytesIO(r.content) as file:
                    print(f'Test {j}: extracted \'{extract_text(file)}\'')
            except Exception as ex:
                print(f'Test {j} failed: {ex}')
