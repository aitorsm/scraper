from selenium import webdriver
import threading
import requests
import time
import os
import sys

def scroll_to_end(wd: webdriver, sleep_between_interactions: int=1) -> None:
    wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(sleep_between_interactions)


def fetch_image_urls(query: str, max_num_links: int, wd: webdriver, sleep_between_interactions: int = 1)-> set:
    # build the google query
    wd=webdriver.Chrome()
    search_url=f'https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={query}&oq={query}&gs_l=img'
    wd.get(search_url) # load the page
    image_urls = set() # Irreducible set of unique elements
    image_count = 0
    results_start = 0
    while image_count < max_num_links:
        scroll_to_end(wd) # scroll down
        # get all image thumbnail_results
        thumbnail_results = wd.find_elements_by_css_selector("img.Q4LuWd")
        number_results = len(thumbnail_results)
        print(f"Found {number_results} search results. Extracting links from {results_start}:{number_results}")
        for img in thumbnail_results[results_start:number_results]:
            # try to click every thumbnail such that we can get the real image behind it
            try:
                img.click()
                time.sleep(sleep_between_interactions)
            except Exception:
                continue
            # extract real image urls
            actual_images = wd.find_elements_by_css_selector('img.n3VNCb')
            for actual_image in actual_images:
                if actual_image.get_attribute('src') and 'http' in actual_image.get_attribute('src'):
                    image_urls.add(actual_image.get_attribute('src'))

            image_count = len(image_urls)
            if len(image_urls) >= max_num_links:
                print(f"Found:{len(image_urls)} image links, done!")
                break
            else:
                print(f"Found:{len(image_urls)} image links, looking for more ...")
                time.sleep(0.2)
                load_more_button = wd.find_elements_by_css_selector("img.mye4qd") # Try to click the load more button, sometimes it doesn't work
                if load_more_button:
                    wd.execute_script("document.querySelector('.mye4qd').click();")
            # move the result start point further down
            results_start = len(thumbnail_results)        
    return image_urls


def persist_image(folder_path: str, url: str, counter : int) -> None:
    try:
        image_content = requests.get(url).content

    except Exception as e:
        print(f"ERROR - Could not download {url} - {e}")
    else:
        print(f"Successfully downloaded {url}")
    try:
        f = open(os.path.join(folder_path, 'jpg' + "_" + str(counter) + ".jpg"), 'wb')
        f.write(image_content)
        f.close()
        print(f"SUCCESS - saved {url} - as {folder_path}")
    except Exception as e:
        print(f"ERROR - Could not save {url} - {e}")


def search_and_download(search_term: str, driver_path: str, target_path='./images', number_images=10) -> None:
    target_folder = os.path.join(target_path, '_'.join(search_term.lower().split(' ')))
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    with webdriver.Chrome(executable_path=driver_path) as wd:
        res = fetch_image_urls(search_term, number_images, wd=wd, sleep_between_interactions=0.5)
    counter = 0
    for elem in res:
        persist_image(target_folder, elem, counter)
        counter += 1

def main()-> None:
    DRIVER_PATH = './chromedriver'
    TARGET_PATH = './images'
    num_images = 200
    txt_file = open("search_list_3.txt","r")
    file_content = txt_file.read()
    print(f"The file with search terms contains {file_content}")
    search_list = file_content.split(",")
    txt_file.close()
    print(f"The search list is {search_list}")

    add_string = ''
    search_list[:]=[element.strip() + " seedling" for element in search_list]
    print(f"Modified list is {search_list}")
    thread_list = []
    for i in range(len(search_list)): # Create a thread for every search term
        thread_list.append(threading.Thread(target=search_and_download,args=(search_list[i],DRIVER_PATH,TARGET_PATH,num_images)))
    for i in range(len(thread_list)):
        thread_list[i].start()


if __name__ == '__main__':
    sys.exit(main())