import requests, sqlite3, urllib.request
import os, sys, json, random, re, time
import wget


# Script por Rodrigo Vázquez
# contacta en https://twitter.com/rodvan

DB = os.path.join(os.path.dirname(sys.argv[0]), "database.db")
ERASE_LINE = '\x1b[2K'
good = "\033[92m✔\033[0m"

page_id = "tupagina"
since_date = "2010-01-01"
selection = "videos" # can be "photos" or "all"
limit = 100
access_token = "tutoken"
url = "https://graph.facebook.com/v4.0/" + str(page_id) + "/feed?fields=message,message_tags,created_time,picture,likes,permalink_url,shares,full_picture,status_type,reactions,attachments{url,title,media_type,type},is_instagram_eligible,properties,is_popular,story&since=" + str(since_date) + "&limit=" + str(limit) +"&access_token=&access_token=" + str(access_token)
error_status = "no"

response = requests.get(url)
keep_continue = False
counter = 0
# SYSTEM FUNCTIONS
# DOWNLOAD VIDEO
def extract_url(html):
    #url = re.search('sd_src:"(.+?)"'.decode('utf-8'), html.decode('utf-8'))[0]
    #url = re.search('hd_src:"(.+?)"', html)[0]
    try:
        url = re.search('sd_src:"(.+?)"', html)[0]
        if url is not None:
            # cleaning the url
            url = url.replace('hd_src:"', '')
            url = url.replace('sd_src:"', '')
            url = url.replace('"', "")
        else:
            url = ""
    except:
        url = ""
    return url

def download_fbvideo(url):
    r = requests.get(url)
    sys.stdout.write(ERASE_LINE)
    file_url = extract_url(r.text)
    path = "videos/" + str(random.random())[3:12] + ".mp4"
    print("Downloading video...", end="\r", flush=True)
    if file_url != "":
        urllib.request.urlretrieve(file_url, path)
    else:
        print("Video source was not found, skipping download for this.")
    sys.stdout.write(ERASE_LINE)
    print(good, "Video downloaded:", path)
    return path

def download_photo(url):
    path = "photos/" + str(random.random())[3:12] + ".jpg"
    resp = urllib.urlopen(url)
    image_data = resp.read()
    f = open(path, 'wb')
    f.write(image_data)
    f.close()
    return path

def add_post_db(created_time, fbid, permalink_url, message, full_picture, status_type, shares, at_url, at_media_type, at_type, is_instagram_eligible, is_popular, file_path ):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS page_posts
                     (ID INTEGER PRIMARY KEY AUTOINCREMENT, created_time text, fbid text UNIQUE, permalink_url text, message text, full_picture text, status_type text, shares int, at_url text, at_media_type text, at_type text, is_instagram_eligible text, is_popular text, file_path text)''')
    c.execute(
        "INSERT OR IGNORE INTO page_posts (created_time, fbid, permalink_url, message, full_picture, status_type, shares, at_url, at_media_type, at_type, is_instagram_eligible, is_popular, file_path ) VALUES (?, ? , ?, ? , ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (str(created_time), str(fbid), str(permalink_url), str(message), str(full_picture), str(status_type), str(shares), str(at_url), str(at_media_type), str(at_type), str(is_instagram_eligible), str(is_popular), str(file_path)))
    # print("Lead added to Database: " + str(url))
    conn.commit()

def process_store(data):
    file_path = ""
    if data:
        if data["data"]:
            for post in data["data"]:
                if post.get("attachments"):
                    try:
                        if post["attachments"]["data"][0]["url"]:
                            at_url = post["attachments"]["data"][0]["url"]
                        else:
                            at_url = ""
                    except:
                        at_url = ""
                    at_media_type = post["attachments"]["data"][0]["media_type"]
                    at_type = post["attachments"]["data"][0]["type"]
                else:
                    at_url = ""
                    at_media_type = ""
                    at_type = ""
                if at_media_type == "video":
                    try:
                        if selection == "videos" or selection == "all":
                            if post["status_type"] == "added_video":
                                file_path = download_fbvideo(at_url)
                                time.sleep(1)
                                print(counter)
                                add_post_db(post.get("created_time", ""), post.get("id", ""), post.get("permalink_url", ""),
                                            post.get("message", ""), post.get("full_picture", ""), post.get("status_type", ""),
                                            post.get("shares", ""), at_url, at_media_type, at_type,
                                            post.get("is_instagram_eligible", ""), post.get("is_popular", ""), file_path)

                    except:
                        file_path = "error"
                elif at_media_type == "photo":
                    try:
                        if selection == "photos" or selection == "all":
                           file_path = download_photo(url)
                           time.sleep(1)
                           add_post_db(post.get("created_time", ""), post.get("id", ""), post.get("permalink_url", ""),
                                       post.get("message", ""), post.get("full_picture", ""), post.get("status_type", ""),
                                       post.get("shares", ""), at_url, at_media_type, at_type,
                                       post.get("is_instagram_eligible", ""), post.get("is_popular", ""), file_path)
                    except:
                        file_path = "error"

                print("se extrajo el post: " + str(post.get("created_time", "")))
        else:
            print("Saltando post por problemas.")
            error_status = "yes"
    else:
        error_status = "yes"


# MAIN FUNCTIONS
if response.status_code == 200:
    data = response.json()
    if data:
        process_store(data)
    if data["paging"]["next"]:
        keep_continue = True
        next_url = data["paging"]["next"]
else:
    print("Token might be invalid, rewnew it")

while keep_continue == True:
    response = requests.get(next_url)
    data = response.json()
    if data:
        process_store(data)
        #print(data)
    if data["paging"]["next"]:
        keep_continue = True
        next_url = data["paging"]["next"]
    else:
        if error_status == "yes":
            print("retrying to request on paging next.")
        else:
            keep_continue = False
    time.sleep(10)



