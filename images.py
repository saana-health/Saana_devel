from bs4 import BeautifulSoup
import urllib.request
import urllib
from io import StringIO
import image
import validators
from urllib.parse import urlparse
from fuzzywuzzy import process

##html_page = urllib2.urlopen("http://imgur.com")
##soup = BeautifulSoup(html_page)
##print soup
##links = soup.find_all('img')
##print links
##images = []
##for img in soup.findAll('img'):
##    print img
##    images.append(img.get('src'))
##
##print(images)

def validate_url(url):
    if not validators.url(url):
        o = urlparse(baseurl)
        image_url = o[0] + "://" + o[1] + url
    else:
        image_url = url
    return image_url

def best_image_function(name, images_all, images_name):
    highest = 0
    max_width = 0
    max_img = ""
    Ratios =  process.extract(name,images_all)
    print(Ratios)
    if Ratios != []:
        highest = process.extractOne(name,images_all)
        #print highest
    if highest[1] <50:
        Ratios_name = process.extract(name,images_name)
        #print Ratios_name
        if Ratios_name != []:
            highest = process.extractOne(name,images_name)
            if highest[1] > 50:
                return validate_url(images_all[images_name.index(highest[0])])
            else:
                for img in images_all:
                    #print img
                    real_url = validate_url(img)
                    try:
                        file = StringIO.StringIO(urllib.urlopen(real_url).read())
                        im=image.open(file)
                        width, height = im.size
                        if width > max_width:
                            max_width = width
                            max_img = real_url
                        print(width)
                        print(height)
                    except IOError:
                        pass
                return max_img               
    else:
        return  validate_url(highest[0])
    
def get_img_title(baseurl):
    images_url = []
    images_nom = []
    tagBool = False
    img_title = ("", "")
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0')]
    j = opener.open(baseurl)
    data = j.read()
    soup = BeautifulSoup(data, features="html5lib")
    links = soup.find_all('img')
    #print links
    title = soup.title.string
    #print title 
    for tag in soup.find_all("meta"):
        if tag.get("property", None) == "og:image":
            #print tag.get("content", None)
            img_title = (title, tag.get("content", None))
            tagBool = True
            break
        elif tag.get("property", None) == "og:image:secure_url":
            best_img = tag.get("content", None)
            #print tag.get("content", None)
            tagBool = True
            img_title = (title, tag.get("content", None))
            break
    if tagBool == False:
        print("else")
        for m_image in links:
            images_url.append(m_image['src'])
            images_nom.append(m_image['alt'])
            #print images_url
            #print images_nom
        img_title = (title, best_image_function(title, images_url, images_nom))
    return img_title
#print get_img_title("https://deliciouslyella.com/recipes/coconut-lentil-dahl/")
#print get_img_title("https://mywholefoodlife.com/2013/07/24/wheat-berry-salad-with-corn-and-peppers")

