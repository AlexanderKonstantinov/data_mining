from os import path, walk
from shutil import move
from typing import List

from PyPDF2 import PdfFileReader
from PyPDF2.utils import PdfReadError
from PIL import Image
import pytesseract
from pymongo import MongoClient

pytesseract.pytesseract.tesseract_cmd = \
    r'C:\Users\Александр\AppData\Local\Tesseract-OCR\tesseract.exe'

BASE_DIR = r'C:\YandexDisk\Курсы\ML\Методы сбора и обработки данных из сети Интернет\data_mining\data_for_parse\СКД_Поверка весов'
PARSED_IMAGES_DIR = r'C:\YandexDisk\Курсы\ML\Методы сбора и обработки данных из сети Интернет\data_mining\data_for_parse\parsed_images'
UNPARSED_IMAGES_DIR = r'C:\YandexDisk\Курсы\ML\Методы сбора и обработки данных из сети Интернет\data_mining\data_for_parse\unparsed_images'


class PDFElements:
    resources = '/Resources'
    x_object = '/XObject'
    image = '/Image'
    im = '/Im'
    subtype = '/Subtype'
    width = '/Width'
    height = '/Height'
    color_space = '/ColorSpace'
    filter = '/Filter'
    dct_decode = '/DCTDecode'
    flate_decode = '/FlateDecode'
    jpx_decode = '/JPXDecode'


PDF = PDFElements()


class ParsedFile:
    name: str
    folder: str
    path: str
    error_message = None

    def __init__(self, name: str, folder: str):
        self.name = name
        self.folder = folder
        self.path = path.join(folder, name)


class ParsedImageFile(ParsedFile):
    size: tuple
    data: None
    mode: str
    file_type: str
    serial_numbers: list

    def __init__(self, name: str, folder: str):
        super().__init__(name, folder)

    def extract_serial_numbers(self, page_num = None):

        self.serial_numbers = []

        img_obj = Image.open(self.path)
        text = pytesseract.image_to_string(img_obj, 'rus')

        pattern = 'заводской (серийный) номер'
        for idx, line in enumerate(text.split('\n')):
            if line.lower().find(pattern) + 1:
                text_en = pytesseract.image_to_string(img_obj, 'eng')
                number = text_en.split('\n')[idx].split(' ')[-1]
                self.serial_numbers.append(number)

        if len(self.serial_numbers) == 0:
            self.error_message = f'serial number not found in {self.name}' if page_num is None \
                else f'serial number not found in {self.name} on page {page_num}'

            new_image_path = self.path.replace(PARSED_IMAGES_DIR, UNPARSED_IMAGES_DIR)
            move(self.path, new_image_path)
            self.folder = UNPARSED_IMAGES_DIR
            self.path = new_image_path


class ParsedPDFFile(ParsedFile):
    # list of tuple as ('page_number', 'parsed_image_file or None, if page no extracted')
    extracted_pages: list

    def __init__(self, name: str, folder: str):
        super().__init__(name, folder)

    def extract_pdf_images(self):
        try:
            pdf_file = PdfFileReader(open(self.path, 'rb'), strict=False)
        except PdfReadError as e:
            print(e)
            self.error_message = 'pdf read error'
            return
        except FileNotFoundError as e:
            print(e)
            self.error_message = 'file not found error'
            return
        except Exception as e:
            print(e)
            self.error_message = 'unknown error'
            return

        self.extracted_pages = []

        for page_num in range(0, pdf_file.getNumPages()):

            image_file = ParsedImageFile('', '')
            self.extracted_pages.append((page_num + 1, image_file))

            page = pdf_file.getPage(page_num)
            page_obj = page[PDF.resources][PDF.x_object].getObject()

            im_name = ''
            try:
                im_name = next(k for k, v in page_obj.items() if k.startswith(PDF.im))
            except Exception as e:
                image_file.error_message = f'pdf element not found on page {page_num + 1}'
                continue

            # Check pdf elements
            if not (page_obj.get(im_name)
                    and page_obj[im_name].get(PDF.subtype) == PDF.image
                    and page_obj[im_name].get(PDF.width)
                    and page_obj[im_name].get(PDF.height)
                    and page_obj[im_name].get(PDF.color_space)
                    and page_obj[im_name].get(PDF.filter)):
                image_file.error_message = f'pdf element not found on page {page_num + 1}'
                continue

            try:
                image_file.data = page_obj[im_name]._data
            except Exception as e:
                image_file.error_message = f'binary image data not found {page_num + 1}'
                continue

            image_file.size = (page_obj[im_name][PDF.width], page_obj[im_name][PDF.height])
            image_file.mode = 'RGB' if page_obj[im_name][PDF.color_space].__contains__('RGB') else 'P'

            decoder = page_obj[im_name][PDF.filter]
            if decoder == PDF.dct_decode:
                file_type = 'jpg'
            elif decoder == PDF.flate_decode:
                file_type = 'png'
            elif decoder == PDF.jpx_decode:
                file_type = 'jp2'
            else:
                file_type = 'bmp'

            image_file.file_type = file_type

        if not len(self.extracted_pages):
            self.error_message = 'images extracted error'

    def save_pdf_images(self):
        for page_num, page in self.extracted_pages:
            if page.error_message is None:

                path_part = self.path.split(f'{BASE_DIR}\\')[1].replace('\\', '_#_')

                page.name = f'{path_part}_#_{page_num}.{page.file_type}'
                page.folder = PARSED_IMAGES_DIR
                page.path = path.join(page.folder, page.name)

                with open(page.path, 'wb') as image:
                    image.write(page.data)

    def extract_serial_numbers(self):

        for page_num, page in self.extracted_pages:
            if page.error_message is None:
                page.extract_serial_numbers(page_num)


def parse_file(folder: str, filename: str) -> List[ParsedFile]:

    if filename.endswith('.pdf'):
        pdf_file = ParsedPDFFile(filename, folder)

        pdf_file.extract_pdf_images()

        if pdf_file.error_message is None:
            pdf_file.save_pdf_images()
            pdf_file.extract_serial_numbers()
            return [f for _, f in pdf_file.extracted_pages]
        else:
            return [pdf_file]

    elif filename.endswith('.jpg'):
        image_file = ParsedImageFile(filename, folder)
        image_file.extract_serial_numbers()
        return [image_file]

    unknown_file = ParsedFile(filename, folder)
    unknown_file.error_message = 'unknown file format'

    return [unknown_file]


def parse(folder: str):
    files = []
    count = 0
    for (dirpath, dirnames, filenames) in walk(folder):
        for filename in filenames:
            print(f'{count} {filename}')
            files.extend(parse_file(dirpath, filename))
            count = count + 1

    return files


def save_to_mongo(files: List[ParsedFile]):
    client = MongoClient('mongodb://localhost:27017/')
    db = client['parsed_data']

    for file in files:

        if file.error_message is None:
            db['parsed_data'].insert_many([{'serial_number': num, 'filepath': file.path} for num in file.serial_numbers])
        else:
            db['unparsed_files'].insert_one({'filepath': file.path, 'error': file.error_message})


def print_stats(files):
    unparsed_pdf = 0

    parsed_images = 0
    unparsed_images = 0

    unknown_files = 0

    for file in files:
        if isinstance(file, ParsedPDFFile):

            if file.error_message is not None:
                unparsed_pdf = unparsed_pdf + 1

        elif isinstance(file, ParsedImageFile):
            if file.error_message is None:
                parsed_images = parsed_images + 1
            else:
                unparsed_images = unparsed_images + 1

        else:
            unknown_files = unknown_files + 1

    print(f'''
unparsed pdf\t{unparsed_pdf}
parsed images\t{parsed_images}
unparsed images\t{unparsed_images}
unknown files\t{unknown_files}
---estimate---\t{parsed_images * 100 / (unparsed_pdf + parsed_images + unparsed_images + unknown_files)} 
''')


if __name__ == '__main__':

    parsed_files = parse(BASE_DIR)

    save_to_mongo(parsed_files)

    print_stats(parsed_files)

    print(1)
