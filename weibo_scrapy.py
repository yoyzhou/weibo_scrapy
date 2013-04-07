#!/usr/bin/env python
#coding=utf8

try:
    import os
    import sys
    import urllib
    import urllib2
    import cookielib
    import base64
    import re
    import hashlib
    import json
    import time
    import logging
    import threading
    import Queue
    import rsa
    import binascii
    from collections import deque
    from BeautifulSoup import BeautifulSoup
    #from bs4 import NavigableString
    from BeautifulSoup import Tag
    
    from optparse import OptionParser
except ImportError:
        print >> sys.stderr, """\

There was a problem importing one of the Python modules required to run yum.
The error leading to this problem was:

%s

Please install a package which provides this module, or
verify that the module is installed correctly.

It's possible that the above module doesn't match the current version of Python,
which is:

%s

""" % (sys.exc_info(), sys.version)
        sys.exit(1)

__prog__= "weibo_saver"
__site__= "http://chaous.com"
__weibo__= "@聂风_"
__version__="0.1-beta"

def config_option():
    usage =  "usage: %prog [options] arg \n"
    usage += " e.g.: %prog -i 1259955755 # when cookie file is usable \n"
    usage += " e.g.: %prog -u username -p password -i 1259955755"
    parser = OptionParser(usage)
    parser.add_option("-u","--username",dest="username",help="if cookie file is unusable you must provide username and password.")
    parser.add_option("-p","--password",dest="password",help="if cookie file is unusable you must provide username and password.")
    parser.add_option("-i","--uid",dest="uid",help="the id of the user you want save.")

    (options, args) = parser.parse_args()

    if not options.username or not options.password:
        options.username = "wrong_user"
        options.password = "wrong_pass"

    if not options.uid:
        parser.error("You must input -i parameters");

    global opt_main
    opt_main = {}
    opt_main["username"] = options.username
    opt_main["password"] = options.password
    opt_main["uid"] = options.uid

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def base62_encode(num, alphabet=ALPHABET):
    if (num == 0):
        return alphabet[0]
    arr = []
    base = len(alphabet)
    while num:
        rem = num % base
        num = num // base
        arr.append(alphabet[rem])
    arr.reverse()
    return ''.join(arr)

def base62_decode(string, alphabet=ALPHABET):
    base = len(alphabet)
    strlen = len(string)
    num = 0

    idx = 0
    for char in string:
        power = (strlen - (idx + 1))
        num += alphabet.index(char) * (base ** power)
        idx += 1

    return num

def mid_to_murl(mid):
    murl = (base62_encode(int(mid[::-1][14:21][::-1]))+base62_encode(int(mid[::-1][7:14][::-1]))+base62_encode(int(mid[::-1][0:7][::-1])))
    return murl

def murl_to_mid(murl):
    mid = (str(base62_decode(str(murl[::-1][8:12][::-1])))+str(base62_decode(str(murl[::-1][4:8][::-1])))+str(base62_decode(str(murl[::-1][0:4][::-1]))))
    return mid

def get_servertime():
    #servertime_url = 'http://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&client=ssologin.js(v1.4.5)'
    servertime_url = 'http://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&su=' + get_user(username) + \
     '&rsakt=mod&checkpin=1&client=ssologin.js(v1.4.5)';
    data = urllib2.urlopen(servertime_url).read()
    p = re.compile('\((.*)\)')
    try:
        json_data = p.search(data).group(1)
        data = json.loads(json_data)
        servertime = str(data['servertime'])
        nonce = data['nonce']
        rsakv = data['rsakv']
        return servertime, nonce, rsakv
    except:
        print 'Get severtime error!'
        return None

def get_pwd_wsse(pwd, servertime, nonce):
    pwd1 = hashlib.sha1(pwd).hexdigest()
    pwd2 = hashlib.sha1(pwd1).hexdigest()
    pwd3_ = pwd2 + servertime + nonce
    pwd3 = hashlib.sha1(pwd3_).hexdigest()
    return pwd3

def get_pwd_rsa(pwd, servertime, nonce):


    #n
    weibo_rsa_pk = 'EB2A38568661887FA180BDDB5CABD5F21C7BFD59C090CB2D245A87AC253062882729293E5506350508E7F9AA3BB77F4333231490F915F6D63C55FE2F08A49B353F444AD3993CACC02DB784ABBB8E42A9B1BBFFFB38BE18D78E87A0E41B9B8F73A928EE0CCEE1F6739884B9777E4FE9E88A1BBE495927AC4A799B3181D6442443'
    #e
    weibo_rsa_e = 65537
   
    message = str(servertime) + '\t' + str(nonce) + '\n' + str(pwd)
    
    key = rsa.PublicKey(int(weibo_rsa_pk, 16), weibo_rsa_e)
    
    encropy_pwd = rsa.encrypt(message, key)

    return binascii.b2a_hex(encropy_pwd)


def get_user(username):
    username_ = urllib.quote(username)
    username = base64.encodestring(username_)[:-1]
    return username

def login(username,pwd,cookie_file):
    if os.path.exists(cookie_file):
        try:
            cookie_jar  = cookielib.LWPCookieJar(cookie_file)
            cookie_jar.load(ignore_discard=True, ignore_expires=True)
            loaded = 1
        except cookielib.LoadError:
            loaded = 0
            print 'Loading cookies error'

        if loaded:
            cookie_support = urllib2.HTTPCookieProcessor(cookie_jar)
            opener         = urllib2.build_opener(cookie_support, urllib2.HTTPHandler)
            urllib2.install_opener(opener)
            print 'Loading cookies success'
            return 1
        else:
            return do_login(username,pwd,cookie_file)
    else:
        return do_login(username,pwd,cookie_file)

def do_login(username,pwd,cookie_file):
    login_data_0 = {
        'entry': 'weibo',
        'gateway': '1',
        'from': '',
        'savestate': '7',
        'userticket': '1',
        #'pagerefer':'',
        'ssosimplelogin': '1',
        'vsnf': '1',
        'vsnval': '',
        'su': '',
        'service': 'miniblog',
        'servertime': '',
        'nonce': '',
        'pwencode': 'wsse',
        'sp': '',
        'encoding': 'UTF-8',
        'url': 'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
        'returntype': 'META'
    }
    
    login_data_1 = {
        'entry': 'weibo',
        'gateway': '1',
        'from': '',
        'savestate': '7',
        'userticket': '1',
        'pagerefer':'',
        'vsnf': '1',
        'su': '',
        'service': 'miniblog',
        'servertime': '',
        'nonce': '',
        'pwencode': 'rsa2',
        'rsakv': '',
        'sp': '',
        'encoding': 'UTF-8',
        'prelt': '45',
        'url': 'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
        'returntype': 'META'
    }

    cookie_jar2     = cookielib.LWPCookieJar()
    cookie_support2 = urllib2.HTTPCookieProcessor(cookie_jar2)
    opener2         = urllib2.build_opener(cookie_support2, urllib2.HTTPHandler)
    urllib2.install_opener(opener2)
    login_url = 'http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.5)'
    try:
        servertime, nonce, rsakv = get_servertime()
    except:
        return
    login_data_1['servertime'] = servertime
    login_data_1['nonce'] = nonce
    login_data_1['su'] = get_user(username)
    login_data_1['sp'] = get_pwd_rsa(pwd, servertime, nonce)
    login_data_1['rsakv'] = rsakv
    login_data = urllib.urlencode(login_data_1)
    #http_headers = {'User-Agent':'Mozilla/5.0 (X11; Linux i686; rv:8.0) Gecko/20100101 Firefox/8.0'}
    http_headers = {'User-Agent':'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)'}
    
    req_login  = urllib2.Request(
        url = login_url,
        data = login_data,
        headers = http_headers
    )
    result = urllib2.urlopen(req_login)
    text = result.read()
    p = re.compile('location\.replace\(\"(.*?)\"\)')
    try:
        login_url = p.search(text).group(1)
        data = urllib2.urlopen(login_url).read()
        #print data
        with open('login.html', 'w') as f:
            f.write(data)
            
        print "Login success!"
        cookie_jar2.save(cookie_file,ignore_discard=True, ignore_expires=True)
        resp = urllib2.urlopen('%s/%s/myfollow' %(urlprefix, myuid))
    
        resp_content = resp.read()
        #print resp_content
        
        return 1
    except:
        print 'Login error!'
        return 0

def last_murl(output_file):
    with open(output_file, 'r') as f:
        f.seek (0, 2) # Seek @ EOF
        fsize = f.tell() # Get Size
        f.seek (max (fsize-1024, 0), 0) # Set pos @ last n chars
        lines = f.readlines() # Read to end
    line = lines[-1:] # Get last line
    murl = '0'
    if len(line) > 0:
        murl = re.sub("\t.*", "", line[0])
        murl = re.sub("\n", "", murl)

    return murl

def clean_content(content):
    content = re.sub("<img src=[^>]* alt=\"", "", content)
    content = re.sub("\" type=\"face\" />", "", content)
    content = re.sub("<[^>]*>", "", content)
    content = re.sub("&quot;", "\"", content)
    content = re.sub("&apos;", "\'", content)
    content = re.sub("&amp;", "&", content)
    content = re.sub("&lt;", "<", content)
    content = re.sub("&gt;", ">", content)
    #clean any whitespaces
    content = re.sub('\s+', '', content, re.MULTILINE)
    
    return content.strip()

def saver(uid,output_file):
    if os.path.exists(output_file):
        last_mid = int(murl_to_mid(last_murl(output_file)))
    else:
        last_mid = 0
    page     = 1
    uid      = int(uid)
    weibo    = {}
    finished = False
    saved_count = 0 # for top
    while not finished:
        urls={}
        urls[0]='http://weibo.com/aj/mblog/mbloglist?_wv=5&count=50&page=%d&uid=%d' % (page,uid)
        urls[1]='http://weibo.com/aj/mblog/mbloglist?_wv=5&count=15&page=%d&uid=%d&pre_page=%d&pagebar=0' % (page,uid,page)
        urls[2]='http://weibo.com/aj/mblog/mbloglist?_wv=5&count=15&page=%d&uid=%d&pre_page=%d&pagebar=1' % (page,uid,page)
        print "now page : %d" % page
        page = page + 1
        for p in urls:
            try:
                d = urllib2.urlopen(urls[p]).read()
                n = json.loads(d)
            except:
                print "Get data error,remove your cookie data and try again"
                finished = True
                break
            soup = BeautifulSoup(n['data'])
            #print soup.prettify()
            posts = soup.findAll(attrs={'action-type' : "feed_list_item"})
            if len(posts)>0:
                for post in posts:
                    mid  = post.get('mid')
                    if mid:
                        mid  = int(mid)
                        forward = post.get('isforward')
                        if forward:
                            origin_nick     = clean_content(str(post.find(attrs={'node-type' : "feed_list_originNick"})))
                            forward_content = "[%s : %s]" % (origin_nick,clean_content(str(post.find(attrs={'node-type' : "feed_list_reason"}))))
                        else:
                            forward_content = ""
                        wb_from = post.find("a",{'class' : "S_link2 WB_time"})
                        murl    = str(re.sub("/.*/","",str(wb_from.get('href'))))
                        ptime   = str(wb_from.get('title'))
                        content = clean_content(str(post.find(attrs={'node-type' : "feed_list_content"})))

                        if mid > last_mid:
                            weibo[mid] = "%s\t%s\t%s %s\n" % (murl,ptime,content,forward_content)
                        elif saved_count > 2:
                            finished = True
                        else:
                            saved_count = saved_count + 1

            else:
                finished = True

            time.sleep(0.5)

        #finished = True

    f = open(output_file,'a+')
    for i in sorted(weibo.items(), key=lambda e:e[0], reverse=False):
        f.write(i[1])

    f.close()

#####global variables define#####

#max number of user's following page to navigate
max_followingpage_number = 1    
#href per following pages
followingpage_href = ''

followings_mine=[]

followings_his=[]

visited_uids = set()
visit_queue = Queue.Queue()

lock = threading.Lock()

following_network = {}

urlprefix = 'http://weibo.com'
magic_spliter = '*_*'
scraped_accounts = 0



username      = r'zhouyoufu18'            #iampigdata@gmail.com, zhouyoufu18
pwd              = r'zyf0132'                   #tonyzhou110, zyf0132
myuid                =  '1248521225'           # 3180262902, 1248521225

username      = r'iamtonyzhou110@gmail.com'            #iampigdata@gmail.com, zhouyoufu18
pwd              = r'tonyzhou110'                   #tonyzhou110, zyf0132
myuid                =  '3225544142'           # 3180262902, 1248521225


username      = r'hearthinking@gmail.com'            #iampigdata@gmail.com, zhouyoufu18
pwd              = r'tonyzhou110'                   #tonyzhou110, zyf0132
myuid                =  '2717618181'           # 3180262902, 1248521225

username      = r'iampigdata@gmail.com'            #iampigdata@gmail.com, zhouyoufu18
pwd              = r'TonyZhou110'                   #tonyzhou110, zyf0132
myuid                =  '3180262902'           # 3180262902, 1248521225

#===================================================================#

username      = r'zhouyoufu18'            #iampigdata@gmail.com, zhouyoufu18
pwd              = r'zyf0132'                   #tonyzhou110, zyf0132
myuid                =  '1248521225'           # 3180262902, 1248521225



cookie_file  = "cookie_file.dat"
refreshed_cookies = False


kaifulee_uid = '1197161814'

scraped = 0
wanted = 10000000
scrapy_sleep_interval = 5
sleep_time = 5 #seconds

uids_list = []
uids_done = []

thread_number = 10

def main(start_uid = None):
    #config_option()
    
    #networkfile = open('network.txt', 'a+')
    
    
    global visited_uids
    global visit_queue
    global lock
    global scraped_accounts
    global scraped
    global wanted
    global scrapy_sleep_interval
    global sleep_time
    global uids_list
    global uids_done
    
    #logging.basicConfig(filename='damn.log')
    #openurl = 'http://weibo.com/yoyoyoyozhou'
    
    #first load uids
    uids_list, uids_done = load_uids('uids_all.txt', 'uids_done.txt')
    
    login_status = login(username,pwd,cookie_file)

    
    if login_status:
        #saver(uid,output_file)
        if start_uid == None or start_uid == myuid:
            my_followings = extract_my_followings(myuid)
            visited_uids.add(myuid)
        
            for f in my_followings:
                visit_queue.put(f)
        elif start_uid == 'from_file':
            
            for uid in uids_list:
                #if not uid in uids_done: 
                visit_queue.put(uid)
            
            for uid in uids_done:
                visited_uids.add(uid)       
        else: #start from a specified uid but not mine
            visited_uids.add(myuid) #in case i have followed by someone
            his_followings = extract_his_followings(start_uid)
            visited_uids.add(start_uid)
        
            for f in his_followings:
                visit_queue.put(f)
        #per debug
        scraped_accounts = 0
        
        
        #spawn a pool of threads, and pass them queue instance 
        for _ in range(thread_number):
            
            t = his_following_threading(visit_queue, lock, wanted, scrapy_sleep_interval, sleep_time)
            t.setDaemon(True)
            t.start()
            #threads.append(t)
        
        visit_queue.join()
            
        #populate queue with data   
#        for uid in my_followings:
#            visit_queue
        
        #wait on the queue until everything has been processed     
#        visit_queue.join()
                     
class his_following_threading(threading.Thread):
    """Threaded Url Grab"""
   
    def __init__(self, queue, lock, wanted, scrapy_sleep_interval, sleep_time):
        threading.Thread.__init__(self)
        self.queue = queue
        self.lock = lock
        #self.scraped = scraped
        self.wanted = wanted
        self.scrapy_sleep_interval = scrapy_sleep_interval
        self.sleep_time = sleep_time #seconds
        
    def run(self):
        global scraped
        global cookie_file
        global refreshed_cookies
        global following_network
        while scraped < self.wanted:
            #grabs host from queue

            if self.queue:
              
                uid = self.queue.get()
                #print 'get: ' + uid
                #following_network[uid] = []
                if uid in visited_uids or  uid in following_network:
                    self.queue.task_done()
                
                else:
                    
                    try:
                       
#                        print 'consume: ' + uid
                        his_followings = extract_his_followings(uid)
                        visited_uids.add(uid)
#                        with open('%s_his_followings.txt' %(uid), 'w') as followings_file:
#                            followings_file.write('\n'.join(his_following_details))
                             
    #                    lock.acquire()
                        
                        wow = '{0: <25}'.format('[' + time.asctime() + '] ') + ' uid_' + '{0: <12}'.format(uid)
                        #logging.info(wow)
                        print wow
                        for f in his_followings:
                            self.queue.put(f)
                        #signals to queue job is done
                        self.queue.task_done()
                        
                        with self.lock:
                            scraped += 1
                            print 'scraped: ' + str(scraped)
                            
                                
                            if scraped < self.wanted and scraped % self.scrapy_sleep_interval == 0 :
                                with open('following_network.txt', 'w') as ntk:
                                    ntk.write('\n'.join([str(k) + ':' + ','.join(v) for k, v in following_network.items()]))
                                    ntk.flush()
                                    
                                   
                                with open('uids_done.txt','w') as done:
                                    done.write('\n'.join(visited_uids))
                                    done.flush()
                                    #time.sleep(self.sleep_time)
                                    #login_status = login(username,pwd,cookie_file)
#                                    if refreshed_cookies:
#                                        pass
#                                    else:
#                                        refreshed_cookies = False
                                        #os.remove(cookie_file)
                                        #os.rename(cookie_file, self.name + '.dat')
                                        #//TODO
                                    #only perform login can refresh cookies?
                                    #login_status = do_login(username,pwd,cookie_file)
                                    #if login_status:
                                    #    refreshed_cookies = True
                                    #    pass
                                    #else:
                                    #    print 'Logon failed after refresh cookie'
                                    #    return
                    except:
                        pass
            else:
                time.sleep(30)
            
            
def extract_my_followings(myuid):
    
    my_followings = []   
    resp = urllib2.urlopen('%s/%s/myfollow' %(urlprefix, myuid))
    
    resp_content = resp.read()
    my_followings.extend(parse_my_follows(resp_content ,myuid))
            
    page = 2
    while(page <= max_followingpage_number):
        
        resp = urllib2.urlopen('http://weibo.com' + followingpage_href[:-1] + str(page))
        resp_content = resp.read()
        my_followings.extend(parse_my_follows(resp_content ,myuid))
                    
        page += 1
    return my_followings
                     
def extract_his_followings(uid):
    
    his_followings = []
    #his_followings_content = []        
    #scrape user info
    resp = urllib2.urlopen(urlprefix + '/%s/info' %uid)
    resp_content = resp.read()        
    parse_friend_infos(resp_content, uid)
            
    #scrape user followings, initial time
    resp = urllib2.urlopen(urlprefix + '/%s/follow' %uid)
    resp_content = resp.read()            
    following_uids, max_followingpage_number = parse_friends_follows(resp_content, uid)          
    his_followings.extend(following_uids)
    #his_followings_content.append(following_details)
        
    page = 2
    while(page <= max_followingpage_number):
        #resp = urllib2.urlopen('http://weibo.com' + followingpage_href[:-1] + str(page))
        resp = urllib2.urlopen('http://weibo.com/%s/follow?page=%s' %(uid, str(page)))
        resp_content = resp.read()  
        following_uids, max_followingpage_number = parse_friends_follows(resp_content, uid)          
        his_followings.extend(following_uids)
        #his_followings_content.append(following_details)
        page +=1
      
    return his_followings
    
################################################################



def parse_my_follows(resp_content, myuid):
    
    
    
    patt_my = '<script>STK && STK.pageletM && STK.pageletM.view\((.*)\)</script>'
    patt = re.compile(patt_my, re.MULTILINE)
    
   
    #follows_info = []
    global max_followingpage_number
    global followingpage_href
    
    global visited_uids
    global visit_queue
    
    followings_mine = []
    
    my_followings_file = open('myfollows.txt', 'a+')
    #max_followingpage_number = 1
    #print resp_content
    weibo_scripts = patt.findall(resp_content)
    
    for script in weibo_scripts: 
        
        view_json = json.loads(script)
              
           
        if 'html' in view_json and view_json['pid'] == 'pl_relation_myfollow':
            html = view_json['html']
            soup = BeautifulSoup(html)
            #get swith pages <a bpfilter="relation" href="/1248521225/myfollow?t=1&amp;page=1" action-data="page=1&amp;t=&amp;f=" action-type="switchType" class="page S_txt1" href="/1248521225/myfollow?t=1&amp;page=1">
#                with open('pretty.txt','w') as f:
#                    f.write(soup.prettify())
            followpages = soup.findAll('a', attrs = {'bpfilter' : 'relation', 'action-type' : 'switchType'})
           
            #calculate how many pages of following I have
            if followpages: #make sure people who follows more than one page of followings
                max_followingpage_number = 1
                for followpage in followpages:
                    followingpage_href = followpage.get('href')
                    
                    if followpage.string:
                        pagenumber = int(followpage.string.strip())
                        if pagenumber > max_followingpage_number:
                            max_followingpage_number = pagenumber
                    
            #print soup.prettify()
            myfollows = soup.findAll('div', attrs={'action-type' : 'user_item'})
            #[user_item for user_item in soup('div') if 'my_follow_list' in user_item.get('class')]
            for user_item in myfollows:
                
                action_data = user_item.get('action-data')
                user_info = {}
                for field in action_data.split("&"):
                    field_name, field_value = field.split('=')
                    if field_name not in ['gid','remark']:
                        user_info[field_name] = field_value
                user_desc = user_item.find('div', attrs={'class' : "intro\ S_txt2"})
                if user_desc:
                    user_info['user_desc'] = user_desc.string.strip()
                
                followings_mine.append(user_info)
                    
                #print user_info
    new_followings = [user['uid'] for user in followings_mine]
    
    if not following_network.has_key(myuid):#first time scrape my followings
        following_network[myuid] = new_followings
    else:
        following_network[myuid].extend(new_followings)
    
    visited_uids.add(myuid)
    #visit_queue.extend(new_followings)        
    
    #write my followings to file
    my_followings_file.write('\n'.join([ magic_spliter.join([str(k) + ':' + str(v) for k, v in user_info.items()]) for user_info in followings_mine]))
    my_followings_file.close()
    return new_followings
   
def parse_friend_infos(resp_content, uid):
    
    patt_my = '<script>STK && STK.pageletM && STK.pageletM.view\((.*)\)</script>'
    patt = re.compile(patt_my, re.MULTILINE)
    
    
    info_tags = ['pl_profile_infoBase', 'pl_profile_infoCareer', 'pl_profile_infoEdu', 'pl_profile_infoTag']
    
    user_info = {}
    user_info_file = open('user_infos.txt', 'a+')
    
    weibo_scripts = patt.findall(resp_content)
    
    for script in weibo_scripts: 
        
        view_json = json.loads(script)
            
        if 'html' in view_json and view_json['pid'] == 'pl_profile_photo':
            html = view_json['html']
            soup = BeautifulSoup(html)
            #get the number of fans, follows and tweets of user
            user_info['follows_n'] = soup.find('strong', attrs = {'node-type' : 'follow'}).string
            user_info['fans_n'] = soup.find('strong', attrs = {'node-type' : 'fans'}).string
            user_info['tweets_n'] = soup.find('strong', attrs = {'node-type' : 'weibo'}).string
            soup = None
            continue
        #get other more info of user
        #basic info
        if 'html' in view_json and view_json['pid'] in info_tags:  
            html = view_json['html']
            user_info.update(extract_user_info(html))
            soup = None

    #print user_info
    user_info_file.write('uid:%s,' %uid)
    user_info_file.write(magic_spliter.join([ str(k) + ':' +  str(v) for k, v in user_info.items()]))   
    user_info_file.write('\n')
    user_info_file.flush()              
    user_info_file.close()    
          

def extract_user_info(div):
    
    user_info = {}
    pf_items = []
    
    soup = BeautifulSoup(div)
    
    if soup and soup.div:
        pf_items = [ div for div in soup.div.contents if isinstance(div, Tag)]
    
    for pf_item in pf_items:
        if pf_item['class'] == 'pf_item clearfix':
            item_name = pf_item.find('div', attrs = {'class':'label S_txt2'})
            if item_name:
                item_name = item_name.text
                con = pf_item.find('div', attrs = {'class':'con'})
                if con:
                    item_value = clean_content(con.text)
                else:
                    con_link = pf_item.find('div', attrs = {'class':'con link'}) 
                    if con_link:
                        item_value = clean_content(con_link.text)
                    else:
                        item_value = ''                    
                            
                user_info[item_name] = item_value             
    return user_info


#######################################################

def parse_friends_follows(resp_content, uid):
    
    
    patt_my = '<script>STK && STK.pageletM && STK.pageletM.view\((.*)\)</script>'
    patt = re.compile(patt_my, re.MULTILINE)
   
    
    max_followingpage_number = 0
    #global followingpage_href
    
    followings_his=[]

    user_info = {}
    
#    file_name = '%s_his_followings.txt' %(uid)
    
#    if (os.path.isfile(file_name)):
#        return #do nothing
    
    his_follows_file = open('%s_his_followings.txt' %(uid), 'a+') 
    
    weibo_scripts = patt.findall(resp_content)
    
    
    for script in weibo_scripts: 
        
        view_json = json.loads(script)
        
        if 'html' in view_json and view_json['pid'] == 'pl_relation_hisFollow':
            html = view_json['html']
            soup = BeautifulSoup(html)
            
            #get how many pages of followings which the user owns
            followpages = soup.find('div', attrs = {'class' : 'W_pages W_pages_comment'})
           
            #calculate how many pages of followings per user
            if followpages: #people who follows nobody or have only one page of followings do not have followpages div
                for followpage in [page for page in followpages.contents if isinstance(page, Tag)]:
                    if followpage.get('class') == 'page S_bg1':
                        followingpage_href = followpage.get('href')
                    
                        if followpage.string:
                            pagenumber = int(followpage.string.strip())
                            if pagenumber > max_followingpage_number:
                                max_followingpage_number = pagenumber
                
            friendollowings = soup.findAll('li', attrs={'class':'clearfix S_line1', 'action-type' : 'itemClick'})
            
            for user_item in friendollowings:
                
                action_data = user_item.get('action-data')
                user_info = {}
                for field in action_data.split("&"):
                    field_name, field_value = field.split('=')
                    user_info[field_name] = field_value
                
                if uid in following_network: 
                    if user_info['uid'] in following_network[uid]:
                        max_followingpage_number = 0
                        his_follows_file.flush()
                        his_follows_file.close()
                        return
                    
                for  info in  [more for more in user_item('div') if isinstance(more, Tag)]:
                    class_name = info['class']
                    if class_name == 'name':
                        user_info['name'] = clean_content(info.a.text)
                        user_info['address'] = clean_content(info.span.text)
                    elif class_name == 'connect':
                        user_info['connect'] = clean_content(info.text)
                    elif class_name == 'face mbspace': #face image
                        user_info['face'] = info.a.img['src']
                    elif class_name == 'weibo':
                        pass
                        #user_info['lasttweet'] = clean_content(info.text)
                
                                   
                followings_his.append(user_info)
                    
                    #print user_info
    
    new_followings = [user['uid'] for user in followings_his]
    
    if not following_network.has_key(uid):#first time scrape user's followings
        following_network[uid] = new_followings
    else:
        following_network[uid].extend(new_followings)
    
    #visited_uids.add(uid)
    #visit_queue.extend(new_followings) 
    
    #write user's followings to file
    followings_his_content = '\n'.join([magic_spliter.join([str(k) + ':' + str(v) for k, v in user_info.items()]) for user_info in followings_his])
    
    his_follows_file.write(followings_his_content)
    his_follows_file.write('\n')
    his_follows_file.flush()
    his_follows_file.close()
    
    return new_followings, max_followingpage_number

def load_uids(uids_file_name, uids_done_file_name):
    uids_list = []
    uids_done = []
    with open(uids_file_name, 'r') as uids:
        for uid in uids:
            if uid:
                uids_list.append(uid.strip())
    
    with open(uids_done_file_name, 'r') as uids:
        for uid in uids:
            if uid:
                uids_done.append(uid.strip())
                
    return uids_list, uids_done

if __name__  ==  '__main__':
    
        
    main('from_file')
    with open('following_network.txt', 'w') as ntk:
        ntk.write('\n'.join([str(k) + ':' + ','.join(v) for k, v in following_network.items()]))
        ntk.flush()
        ntk.close()
        
#    output_file  = "myfollows.html"
#    user_info_html = 'user_info.html'
#    friends_follows_html = 'his_followings.html'
#    
#    parse_my_follows(output_file,'22--my')
#    parse_my_follows(output_file,'22--my')
#    parse_friend_infos(user_info_html,'22--his')
#    parse_friends_follows(friends_follows_html,'22--his')
    
    
    
    
    
