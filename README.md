**Background**
--
During the early stages of lockdown, Oxford provided all of their educational books for free online. As an IB student, I saw this and thought that the books could genuinly be useful to me. Unfortunately this offer was on for a limited time, meaning that I needed to find a method of downloading these books.

**Installation**
--
To install files:
`````
git clone https://github.com/whoisoscar/calameo-downloader
`````
To Install Required Modules:
`````
pip install -r requirements.txt
`````

**Usage**
--
`````
cd calmeo-downloader
python3 main.py
`````
Configurations are done within the main.py file.
These configurations include:
* List of book links
* Option to only download PDF version

Given a list of calmeo.com books, the script will go through all the pages and dowload them.
If `only_pdf` is set to false, the script will download both a SVG and PVG version.
    This is done for personal preference as SVG's allow to search and copy text, but are more heavy-weight.

Setting `only_pdf` to true will take significantly less time as SVG's take a long time to download.

You can enter multiple urls within the list and the script will download all of them.
