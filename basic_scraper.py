### THIS CODE WAS PART OF A PROGRAMMING ASSIGNMENT AT MOLDE UNIVERSITY COLLEGE IN OCTOBER 2020
### Simple code to web scrape the website called xkcd. 
### This code will download the images from the URL and store them in a seperate folder.
### It will also write a CSV file with potential errors along the way.

### Note: This is raw code, and might not function as intended. 

import sys
import os
import requests
import timeit
import lxml
from PIL import Image
from bs4 import BeautifulSoup
import urllib
import re
import csv

def line_separator(i): 
    '''Prints a visible line that seperates the other print statements in the terminal'''
    if i == 'start':
        print("\n---------------------")
    elif i == 'end':
        print("---------------------")
    else:
        return None

def read_comicdata():
    '''Reads the comic data and stores potential errors in a seperate CSV file.'''
    stored_comics = []

    try:
        comic_database_file = open('database/comicdata.csv', encoding='utf-8')
        csv_file = csv.reader(comic_database_file, delimiter=';')
        
        for row in csv_file:
            try:
                if os.path.isfile(row[5]):
                    stored_comics.append(row)
            except IndexError:
                continue
        comic_database_file.close()
    except FileNotFoundError:
        print('No database file was found')
        error_log.append('No database file was found, a file will be created at the end of the script')


    return stored_comics

def get_url_list(comicdata):
    ### FOR TESTING: input('Press Enter to get todays number')

    res = requests.get("https://xkcd.com")
    res.raise_for_status() # if not 200, script will stop
    soup = BeautifulSoup(res.text, "html.parser") # last attribute choses what parser we want to use
    result = soup.find_all(string=re.compile("Permanent link to this comic"))
    todays_number = []

    # extract todays number from result string
    for character in str(result):
        if character.isdigit():
            todays_number.append(character)
    todays_number = int("".join(todays_number))

    print(todays_number)

    # concatenate number to end of url and append to url_list
    url_list = []
    for number in range(int(todays_number)):
        number += 1 # force start from 1 and not 0
        url_list.append("https://xkcd.com/"+str(number))

    ### for reverse url order (start from last) uncomment line under (FOR DEBUGGING)
    # url_list = sorted(url_list, reverse=True) # start from first or from last

    # if comic image exist, delete url to that comic page
    for url_stored in comicdata:
        if url_stored[2] in url_list:
            url_list.remove(url_stored[2])
            error_log.append('removed URL ' +  url_stored[2] + ' from url_list')



    ### for debugging (skip looping through specified urls) Remove the # signs.
    ### skips urls from:
    # x = 0
    # y = 402
    # del url_list[x:y]


    print("\nCURRENT TOTAL NUMBER OF COMICS IS " + str(len(url_list)) + ".\n")

    return url_list


def download_files():
    url_regex = re.compile(r'https+(.*)')

    # define regex for url number extract
    number_regex = re.compile(r'\d*$')

    # list all images that is already stored
    stored_images = [f for f in os.listdir('images') if os.path.splitext(f)[-1] == '.png' or os.path.splitext(f)[-1] == '.jpg']

    for number_iterate, url in enumerate(url_list):

        # get number from the end of url and use as comic id
        search_comic_id = number_regex.search(url)
        comic_id = search_comic_id.group()

        line_separator('start')
        print("CURRENT PAGE: " + url)


        # downloads webpage into object (only from the HTML <head> tag)
        print(f"RETRIEVING INFO FROM: {url}")
        res = requests.get(url, stream=True)

        # parse raw request to raw html text with beautifulsoup
        soup = BeautifulSoup(res.text, "html.parser")


        # get direct link to comic image
        comic_element = soup.select("#comic img")
        if comic_element == []:
            print("Could not find comic image.")
            error_log.append('Direct link to comic Id: ' + str(comic_id) + ' had invalid URL: ' + url)
        else:
            comic_url = "https:" + comic_element[0].get("src")

            # fix bug with the above line when comic_element does not contain domain name
            if 'xkcd.com' not in comic_url:
                print('..using regex')
                # regex find line that has: "Image URL (for hotlinking/embedding):"
                comic_element = soup.find_all(string=re.compile("Image URL \(for hotlinking/embedding\):"))
                # extract url from the line with regex object stated in the beginning of this function
                extract_url = url_regex.search(comic_element[0])
                comic_url = extract_url.group()
                error_log.append('Regex was used for comic Id: ' + str(comic_id) + ' with URL: ' + comic_url)
                error_log.append('Fixed URL: ' + comic_url)


        # get comic title from html
        comic_name = soup.select("html body div#middleContainer.box div#ctitle")
        if comic_name == []:
            print("Could not find comic image.")
            error_log.append('Comic image with Id: ' + str(number_iterate) + ' had the invalid URL: ' + url)
            url_invalid = True
        else:
            filtered_comic_name = comic_name[0].text # using .text to filter out object content
            print("\nCOMIC TITLE: " + filtered_comic_name)
            url_invalid = False

        # only continue if url is valid
        if url_invalid == True:
            print('Skipping this image')
            url_invalid = False
            line_separator('end')
        else:
            # download webpage (comic image) into object
            print(f"DOWNLOADING IMAGE: {comic_url}")
            res = requests.get(comic_url)
            res.raise_for_status()

            # if image is already stored, skip downloading
            file_path = os.path.join("images", os.path.basename(comic_url))
            print(comic_url)
            if os.path.basename(comic_url) in stored_images:
                error_log.append('Comic image with Id: ' + str(number_iterate) + ' with name ' + os.path.basename(comic_url) + ' alread exists, skipped downloading')
            else:
                # open a binary object file
                image_file = open(file_path, "wb") #writes binary
                # ..and write binary data from object file (comic image) to image file
                print("SAVED IMAGE PATH:", file_path)
                for chunk in res.iter_content(100000):
                    image_file.write(chunk)
                image_file.close()


            # append: comic title, url, size, path --> dictionary
            comic_db[filtered_comic_name] = {
            "Id": comic_id,
            "URL": url,
            "DirectURL": comic_url,
            "Size": sys.getsizeof(res.content), # get size from response file instead of checking image file, should be faster but may not be as accurate?..
            "Path": file_path,
            }

            print("FILE SIZE:", comic_db[filtered_comic_name]["Size"])

            line_separator('end')

        ### for debugging (limit loops)
        # set max iterations counting from 0
        # if number_iterate == 6:
        #     break


def print_dict():
    # input('Press Enter to print out comic dictionary')

    for key in comic_db:
        line_separator('start')
        print("COMIC TITLE:", '"',key,'"')
        print("Comic Id.:", comic_db[key]["Id"])
        print("IMAGE URL:", comic_db[key]["DirectURL"])
        print("IMAGE URL:", comic_db[key]["URL"])
        print("FILE SIZE:", comic_db[key]["Size"], "BYTES")
        print("FILE PATH:", comic_db[key]["Path"])
        line_separator('end')


# write data from comic_db to csv
def write_comic_csv_database():
    # input('Press Enter write comic database to csv')
    print('Writing comicdata.csv to: database/comicdata.csv')
    with open(r"database/comicdata.csv","w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, delimiter=";")
        writer.writerow(["Comic Database"])
        writer.writerow(["Id","Title","URL","Direct URL","Size in Bytes","Relative filepath"])
        for key in comic_db:
            writer.writerow([comic_db[key]["Id"],key,comic_db[key]["URL"],comic_db[key]["DirectURL"],comic_db[key]["Size"],comic_db[key]["Path"]])

# write logs
def write_log_csv():
    # create new or overwrite my_log file
    # input('Press Enter to write error log')
    print("Writing my_log.txt to: logs/my_log.txt")
    if error_log == []:
        logfile = open(r'logs/my_log.txt','w', newline='', encoding='utf-8')
        logfile.write('No Errors logged')
        logfile.close()

    else:
        logfile = open(r'logs/my_log.txt','w', newline='', encoding='utf-8')
        for item in error_log:
            logfile.write(item+'\n')
        logfile.close()



# create (if not exist) subfolder images to store cimics
os.makedirs("images", exist_ok=True)
os.makedirs("database", exist_ok=True)
os.makedirs("logs", exist_ok=True)



# declare global variables for storing data
comic_db = {} # comic dict database
comic_list = [] # comic list database
error_log = [] # error logging list

# fetch all URL
stored_comics = read_comicdata() # find stored URL
url_list = get_url_list(stored_comics) # get remaining URL

# execute instances
download_files()

# print_dict()

write_comic_csv_database()

write_log_csv()
