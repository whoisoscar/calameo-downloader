import requests
from bs4 import BeautifulSoup
import time
import cairosvg
import os, sys
from PyPDF2 import PdfFileMerger
from fpdf import FPDF
from PIL import Image
import urllib3.contrib.pyopenssl
from progressbar import progressbar
import logging
from collections import namedtuple
import re

book_title = re.compile(r"Title:(?P<title>.+?), Author")
book_length = re.compile(r"Length:(?P<length>.+?) pages,")
book_link = re.compile(r"(?P<pattern>.+?)\d+\.(?P<extension>jpg|jpeg|svgz|svg|png)")
book = namedtuple('book',['title','length',"link","extension"])


def get_book_info(url, retry_limit=-1):
    while retry_limit:
        try:
            r = requests.get(url)
        except Exception as e:
            rootLogger.warning(f"While getting book information the following error happened: Http {r.status_code}, exception {e}")
            retry_limit-=1
            continue
        finally:
            if r.status_code == 200:
                break

    parsed_html = BeautifulSoup(r.content, "lxml")
    og_link = book_link.search(parsed_html.head.find('meta', attrs={'property':'og:image'})["content"])
    book_description = parsed_html.head.find('meta', attrs={'name':'description'})["content"]
    title = book_title.search(book_description)
    length = book_length.search(book_description)
    return book(title.group("title").replace("/","_").strip() if title else "",\
                int(length.group("length")) if length else 0,\
                og_link.group("pattern") if og_link else "",\
                og_link.group("extension")if og_link else "")

def download_images(book, directory, retry_limit=-1):
    image_list=[]
    s = requests.Session()
    for i in range(book.length):
        url = f"{book.link}{i+1}"
        while retry_limit:
            try:
                r = s.get(f"{url}.{book.extension}")
            except Exception as e:
                rootLogger.warning(f"While downloading an image from: {url}.{book.extension}\n the following exception happened: {e}")
                retry_limit-=1
                continue
            finally:
                if r.status_code == 200:
                    break
        path=f"{directory}/output{str(i+1)}.{book.extension if book.extension != 'svgz' else 'svg'}"
        with open(path, 'wb') as out_file:
            out_file.write(r.content)
        image_list.append(path)
    return image_list

def file_cleaner(*outputs):
    for output in outputs:
        for file in output:
            os.remove(file)

def convert_svg2pdf(image_list,directory):
    for idx, image in enumerate(image_list):
        cairosvg.svg2pdf(url=image, write_to=f"directory/output{str(idx+1)}.pdf")
        pdf_list.append(f"directory/output{str(idx+1)}.pdf")
    return pdf_list

def convert_jpg2pdf(image_list, book, directory, title=""):
    cover = Image.open(image_list[0])
    width, height = cover.size
    pdf = FPDF(unit = "pt", format = [width, height])

    for idx, page in enumerate(image_list):
        pdf.add_page()
        pdf.image(page, 0, 0)

    output_title = title if title else book.title
    pdf.output(f"{directory}/{output_title}.pdf", "F")

def pdf_merger(pdf_list, book, directory, title=""):
    merger = PdfFileMerger()
    for idx, pdf in enumerate(pdf_list):
        merger.append(pdf)
    output_title = title if title else book.title
    merger.write(f"{directory}/{output_title}.pdf")
    merger.close()

def pdf_maker(books,directory=os.getcwd(), only_pdf=True, verbose=True):
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)s] [%(levelname)s]:  %(message)s", datefmt='%d/%m/%Y %H:%M:%S')
    rootLogger = logging.getLogger()
    rootLogger.setLevel("DEBUG")
    fileHandler = logging.FileHandler(f'{directory}/calameo_{time.strftime("%Y_%m_%d__%H_%M_%S")}.log')
    fileHandler.setFormatter(logFormatter)
    fileHandler.setLevel("DEBUG")
    rootLogger.addHandler(fileHandler)
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(logFormatter)
    consoleHandler.setLevel("INFO")
    rootLogger.addHandler(consoleHandler)
    with requests.Session() as s:
        for book_url,title in books.items():
            book_info = get_book_info(book_url)
            rootLogger.info(f"Successfully registerd {book_info.title} containing {book_info.length} pages")
            image_list = download_images(book_info, directory)
            rootLogger.info(f"Images successfully downloaded {len(image_list)}/{book_info.length}")
            if book_info.extension == "svgz":
                pdf_list = convert_svg2pdf(image_list, directory)
                rootLogger.info(f"Images successfully converted in PDF {len(pdf_list)}/{len(image_list)}")
                pdf_merger(pdf_list, book_info, directory, title)
                rootLogger.info(f"PDF successfully merged")
                if only_pdf:file_cleaner(image_list,pdf_list)
            elif book_info.extension == "jpg":
                convert_jpg2pdf(image_list, book_info, directory, title)
                rootLogger.info(f"Images successfully converted in PDF book")
                if only_pdf:file_cleaner(image_list)
            rootLogger.info(f"Cleanup done")
