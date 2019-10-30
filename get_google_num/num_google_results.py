import re
import datetime
import requests
from bs4 import BeautifulSoup
import progressbar
import os.path

import os
import socks
import socket
socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
socket.socket = socks.socksocket
import urllib2
print(urllib2.urlopen('http://icanhazip.com').read())


REGEX = r'About (.*) results'
REGEX2 = r'(.*) results<nobr>'
'''
proxy  = "152.3.148.145"
import socket

real_create_conn = socket.create_connection

def set_src_addr(*args):
    address, timeout = args[0], args[1]
    source_address = (proxy[proxyNum], 0)
    proxyNum = proxyNum + 1
    return real_create_conn(address, timeout, source_address)

socket.create_connection = set_src_addr
'''
            
def number_of_search_results(key):
    def extract_results_stat(url):
        headers = { 
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/21.0'
        }
        print "searching " + url
        search_results = requests.get(url.replace('%',' '), headers=headers, allow_redirects=True)
        if search_results.status_code == 200:
            numResults = 0
            try:
                soup = BeautifulSoup(search_results.text)
                result_stats = soup.find(id='resultStats')
                m = re.match(REGEX, result_stats.text)
                numResults = int(m.group(1).replace(',',''))
            except:
                pass    
            return numResults
        else:
            raise

    google_main_url = 'https://www.google.co.in/search?q=' + key
    google_news_url = 'https://www.google.co.in/search?hl=en&gl=in&tbm=nws&authuser=0&q=' + key
    return extract_results_stat(google_main_url)
    
numLines = 0
with open('results_shrt_desc.txt') as f:
  for line in f:
    if len(line)>3:
      numLines = numLines + 1

print "There are " + str(numLines) + " foods"
bar = progressbar.ProgressBar(maxval=numLines,widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])

startLine = 0
if os.path.isfile('finished.txt'):
  with open('finished.txt') as f:
    for line in f:
      if len(line)>0:
        startLine = int(line.strip())
print startLine

i = 0
with open('results_shrt_desc.txt') as f:
  for line in f:
    if len(line)>3:
      i = i+1
      bar.update(i)
      if i>startLine:
        (ndb_no,long_des) = line.split('|')
        successful = False
        while not successful:
          try:
            num=number_of_search_results(long_des)
            with open("ndb_no-shrt_des-num.txt", "a") as myfile:
              myfile.write(ndb_no + "|" + long_des.strip() + "|" + str(num) + "\n")
            with open("finished.txt","a") as myfile:
              myfile.write(str(i) + "\n")
            successful = True
          except:
            print "Google is blocking now"
            os.system('/etc/init.d/tor restart')
#            print(urllib2.urlopen('http://icanhazip.com').read())
            #break
    
'''
d_view = [ (v,k) for k,v in foods.iteritems() ]
d_view.sort(reverse=True) # natively sort tuples by first element
for v,k in d_view:
    print "%s: %d" % (k,v)
    '''
