import requests
from bs4 import BeautifulSoup
from time import sleep
import cairosvg
import os
from PyPDF2 import PdfMerger
from fpdf import FPDF
from PIL import Image
import urllib3.contrib.pyopenssl
import progressbar

import argparse
parser = argparse.ArgumentParser(prog='Calameo downloader',
  description='Downloads files from Calameo.com as pdf files')
parser.add_argument('url', nargs='+', help='calameo urls to download')
parser.add_argument('--jpg_only', default=False, action='store_true',
  help='only download the jpg images, faster and more faithful layout, but looses the vectorial information')
args = parser.parse_args()
book_url_list = args.url
only_pdf = args.jpg_only

with requests.Session() as s:
  for book_url in book_url_list:
    if not only_pdf:
      # SVG to PDF
      image_list = []
      pdf_list = []
      print("--> Downloading from SVG to PDF")

      headers = {
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'
      }
      r = s.get(book_url, headers=headers)

      parsed_html = BeautifulSoup(r.text, "lxml")
      og_link = parsed_html.head.find('meta', attrs={'property':'og:image'})["content"].replace("1.svgz","").replace("1.jpg","")
      book_description = parsed_html.head.find('meta', attrs={'name':'description'})["content"]

      pre_book_title  = (book_description.find("Title:"))
      post_book_title = (book_description.find(", Author"))
      book_title      =  book_description[pre_book_title+7:post_book_title]

      pre_book_length  = (book_description.find("Length:"))
      post_book_length = (book_description.find(" pages,"))
      book_length      =  book_description[pre_book_length+8:post_book_length]

      #Download all SVG files
      print("Downloading all "+book_length+" SVG files...")
      for i in progressbar.progressbar(range(int(book_length))):
        while True:
          try:
            r = s.get(og_link+str(i+1)+".svgz",headers=headers)
            break
          except:
            print("Error")
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

      #Join all PDFs
      print("Joining all PDFs...")
      merger = PdfMerger()
      with progressbar.ProgressBar(max_value=int(book_length)) as bar:
        for idx, pdf in enumerate(pdf_list):
          merger.append(pdf)
          bar.update(idx)
      merger.write(book_title+"_svg.pdf")
      merger.close()

      # cleanup
      for image in image_list: os.remove(image)
      for pdf in pdf_list: os.remove(pdf)
    # end if not only_pdf


    # JPG to pdf
    image_list = []
    print("")
    print("--> Downloading from JPG to PDF")
    headers = {
      'Upgrade-Insecure-Requests': '1',
      'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'
    }
    r = s.get(book_url, headers=headers)

    parsed_html = BeautifulSoup(r.text, "lxml")
    og_link = parsed_html.head.find('meta', attrs={'property':'og:image'})["content"].replace("1.svgz","").replace("1.jpg","")
    book_description = parsed_html.head.find('meta', attrs={'name':'description'})["content"]

    pre_book_title = (book_description.find("Title:"))
    post_book_title = (book_description.find(", Author"))
    book_title = book_description[pre_book_title+7:post_book_title]

    pre_book_length = (book_description.find("Length:"))
    post_book_length = (book_description.find(" pages,"))
    book_length = book_description[pre_book_length+8:post_book_length]

    #Download all JPG files
    print("Downloading all JPG files...")
    for i in progressbar.progressbar(range(int(book_length))):
      while True:
        try:
          r = s.get(og_link+str(i+1)+".jpg",headers=headers)
          break
        except:
          print("Error")
          continue

      with open('output'+str(i+1)+".jpg", 'wb') as out_file:
        out_file.write(r.content)
      image_list.append("output"+str(i+1)+".jpg")

    #Join all JPG's
    print("Joining all JPG files into final PDF...")
    cover = Image.open(image_list[0])
    width, height = cover.size

    pdf = FPDF(unit = "pt", format = [width, height])
    with progressbar.ProgressBar(max_value=int(book_length)) as bar:
      for idx, page in enumerate(image_list):
        pdf.add_page()
        pdf.image(page, 0, 0)
        bar.update(idx)
    pdf.output(book_title+"_jpg.pdf", "F")

    for image in image_list: os.remove(image)
