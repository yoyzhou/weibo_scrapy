#!/usr/bin/env python
#coding=utf8
try:
    import sys
    import urllib2
    import re
    import json
    from BeautifulSoup import BeautifulSoup
    from BeautifulSoup import Tag
    from weibo_scrapy import scrapy
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
        


class weibo_following_ntk_scrapy(scrapy):
    
    def __init__(self, **kwds):
        super(weibo_following_ntk_scrapy, self).__init__(**kwds)
        self.urlprefix = 'http://weibo.com'
        self.magic_spliter = '*_*'
         
    def scrapy_do_task(self, uid):
        '''
        Note the differences between login uid, aka my following, and other uids.
        '''
        if uid == self.login_uid: #when do task uid equals login uid
            return self.extract_my_followings(uid)
        else:
            return self.extract_his_followings(uid)
        
        
    def extract_my_followings(self, uid):
        
        my_followings = []   
        resp = urllib2.urlopen('%s/%s/myfollow' %(self.urlprefix, uid))
        
        resp_content = resp.read()
        max_followingpage_number, followingpage_href, followings_uid = self.parse_my_follows(resp_content ,uid)
        my_followings.extend(followings_uid)
                
        page = 2
        while(page <= max_followingpage_number):
            
            resp = urllib2.urlopen('http://weibo.com' + followingpage_href[:-1] + str(page))
            resp_content = resp.read()
            _, _, followings_uid = self.parse_my_follows(resp_content ,uid)
            my_followings.extend(followings_uid)
                        
            page += 1
        return my_followings
                         

      
    def parse_my_follows(self, resp_content, myuid):
        
        
        patt_my = '<script>STK && STK.pageletM && STK.pageletM.view\((.*)\)</script>'
        patt = re.compile(patt_my, re.MULTILINE)
        
        max_followingpage_number = 0
        followingpage_href = ''

        followings_mine = []
        
        my_followings_file = open('myfollows.txt', 'a+')
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

        #write my followings to file
        my_followings_file.write('\n'.join([ self.magic_spliter.join([str(k) + ':' + str(v) for k, v in user_info.items()]) for user_info in followings_mine]))
        my_followings_file.close()
        return max_followingpage_number, followingpage_href, new_followings
       
    ################################################################
  
    def extract_his_followings(self, uid):
        
        his_followings = []       
        #scrape user info
        resp = urllib2.urlopen(self.urlprefix + '/%s/info' %uid)
        resp_content = resp.read()        
        self.parse_friend_infos(resp_content, uid)
                
        #scrape user followings, initial time
        resp = urllib2.urlopen(self.urlprefix + '/%s/follow' %uid)
        resp_content = resp.read()            
        following_uids, max_followingpage_number = self.parse_friends_follows(resp_content, uid)          
        his_followings.extend(following_uids)

            
        page = 2
        while(page <= max_followingpage_number):
            #resp = urllib2.urlopen('http://weibo.com' + followingpage_href[:-1] + str(page))
            resp = urllib2.urlopen('http://weibo.com/%s/follow?page=%s' %(uid, str(page)))
            resp_content = resp.read()  
            following_uids, max_followingpage_number = self.parse_friends_follows(resp_content, uid)          
            his_followings.extend(following_uids)

            page +=1
          
        return his_followings
        
    
    
    def parse_friend_infos(self, resp_content, uid):
        
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
                user_info.update(self.extract_user_info(html))
                soup = None
    
        #print user_info
        user_info_file.write('uid:%s,' %uid)
        user_info_file.write(self.magic_spliter.join([ str(k) + ':' +  str(v) for k, v in user_info.items()]))   
        user_info_file.write('\n')
        user_info_file.flush()              
        user_info_file.close()    
              
    
    def extract_user_info(self, div):
        
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
                        item_value = self.clean_content(con.text)
                    else:
                        con_link = pf_item.find('div', attrs = {'class':'con link'}) 
                        if con_link:
                            item_value = self.clean_content(con_link.text)
                        else:
                            item_value = ''                    
                                
                    user_info[item_name] = item_value             
        return user_info
    
    
    #######################################################
    
    def parse_friends_follows(self, resp_content, uid):
        
        
        patt_my = '<script>STK && STK.pageletM && STK.pageletM.view\((.*)\)</script>'
        patt = re.compile(patt_my, re.MULTILINE)
       
        max_followingpage_number = 0
        followings_his=[]
        user_info = {}
    
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
                        
                    for  info in  [more for more in user_item('div') if isinstance(more, Tag)]:
                        class_name = info['class']
                        if class_name == 'name':
                            user_info['name'] = self.clean_content(info.a.text)
                            user_info['address'] = self.clean_content(info.span.text)
                        elif class_name == 'connect':
                            user_info['connect'] = self.clean_content(info.text)
                        elif class_name == 'face mbspace': #face image
                            user_info['face'] = info.a.img['src']
                        elif class_name == 'weibo':
                            pass
                            #user_info['lasttweet'] = self.clean_content(info.text)
                    
                                       
                    followings_his.append(user_info)
                        
        
        new_followings = [user['uid'] for user in followings_his]

        #write user's followings to file
        followings_his_content = '\n'.join([self.magic_spliter.join([str(k) + ':' + str(v) for k, v in user_info.items()]) for user_info in followings_his])
        
        his_follows_file.write(followings_his_content)
        his_follows_file.write('\n')
        his_follows_file.flush()
        his_follows_file.close()
        
        return new_followings, max_followingpage_number
    
    
    def clean_content(self, content):
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
    
if __name__ == '__main__':
    s = weibo_following_ntk_scrapy(uids_file = 'uids_all.txt', config = 'my.ini')
    s.scrapy()