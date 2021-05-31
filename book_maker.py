import requests
from bs4 import BeautifulSoup
import time
from time import sleep
import cairosvg
import os
from PyPDF2 import PdfFileMerger
from fpdf import FPDF
from PIL import Image
import urllib3.contrib.pyopenssl
from progressbar import progressbar
import logging

logging.basicConfig(filename=f'calameo_{time.strftime("%Y_%m_%d__%H_%M_%S")}.log',
                    format='%(asctime)s %(levelname)s:%(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S',
                    level=logging.DEBUG)

def pdf_maker(books, only_pdf=False):
    with requests.Session() as s:
        for book_url,title in books.items():
            if not only_pdf:
                image_list = []
                pdf_list = []
                #
                #Download from SVG to PDF
                #
                print("--> Downloading from SVG to PDF")

                headers = {
                    'Upgrade-Insecure-Requests': '1',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'
                }
                r = s.get(book_url)

                parsed_html = BeautifulSoup(r.text, "lxml")
                og_link = parsed_html.head.find('meta', attrs={'property':'og:image'})["content"].replace("1.svgz","").replace("1.jpg","")
                book_description = parsed_html.head.find('meta', attrs={'name':'description'})["content"]

                pre_book_title = (book_description.find("Title:"))
                post_book_title = (book_description.find(", Author"))
                book_title = book_description[pre_book_title+7:post_book_title]

                pre_book_length = (book_description.find("Length:"))
                post_book_length = (book_description.find(" pages,"))
                book_length = book_description[pre_book_length+8:post_book_length]
                #Download all SVG files
                print("Downloading all "+book_length+" SVG files...")
                for i in progressbar.ProgressBar(range(int(book_length))):
                    while True:
                        try:
                            r = s.get(og_link+str(i+1)+".svgz",headers=headers)
                            break
                        except:
                            #print("Error")
                            continue
                    with open('output'+str(i+1)+".svg", 'wb') as out_file:
                        out_file.write(r.content)
                    image_list.append("output"+str(i+1)+".svg")
                #Convert SVG to PDF
                print("Converting all SVG files to PDF...")
                with progressbar.ProgressBar(max_value=int(book_length)) as bar:
                    for idx, image in enumerate(image_list):
                        cairosvg.svg2pdf(url=image, write_to="output"+str(idx+1)+".pdf")
                        pdf_list.append("output"+str(idx+1)+".pdf")
                        bar.update(idx)
                #Join all PDF's
                print("Joining and exporting all PDFs...")
                merger = PdfFileMerger()
                with progressbar.ProgressBar(max_value=int(book_length)) as bar:
                    for idx, pdf in enumerate(pdf_list):
                        merger.append(pdf)
                        bar.update(idx)
                merger.write("SVG - "+book_title+".pdf")
                merger.close()

                for image in image_list:
                    os.remove(image)

                for pdf in pdf_list:
                    os.remove(pdf)

            image_list = []
            #
            #Download from JPG to PDF
            #
            print("")
            print("--> Downloading from JPG to PDF")
            r = s.get(book_url)

            parsed_html = BeautifulSoup(r.text, "lxml")
            og_link = parsed_html.head.find('meta', attrs={'property':'og:image'})["content"].replace("1.svgz","").replace("1.jpg","")
            book_description = parsed_html.head.find('meta', attrs={'name':'description'})["content"]

            pre_book_title = (book_description.find("Title:"))
            post_book_title = (book_description.find(", Author"))
            book_title = book_description[pre_book_title+7:post_book_title]
            logging.info(f"{book_title} is being downloaded")
            pre_book_length = (book_description.find("Length:"))
            post_book_length = (book_description.find(" pages,"))
            book_length = book_description[pre_book_length+8:post_book_length]
            logging.info(f"Number of pages: {book_length}")
            #Download all JPG files
            print("Downloading all JPG files...")
            progress = progressbar.ProgressBar()
            for i in progress(range(int(book_length))):
                while True:
                    try:
                        r = s.get(og_link+str(i+1)+".jpg")
                        break
                    except:
                        #print("Error")
                        continue

                with open('output'+str(i+1)+".jpg", 'wb') as out_file:
                    out_file.write(r.content)
                image_list.append("output"+str(i+1)+".jpg")
            #Join all JPG's
            print("Joining all JPG files into final PDF...")
            cover = Image.open(image_list[0])
            width, height = cover.size

            pdf = FPDF(unit = "pt", format = [width, height])

            for idx, page in enumerate(image_list):
                pdf.add_page()
                pdf.image(page, 0, 0)

            output_title = title if title else book_title.replace("/","_")
            pdf.output(output_title+".pdf", "F")

            for image in image_list:
                os.remove(image)

            print("All JPG files cleaned")
