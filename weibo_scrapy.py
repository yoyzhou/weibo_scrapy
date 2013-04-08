#!/usr/bin/env python
#coding=utf8

try:
    import sys
    import time
    import threading
    import Queue
    import ConfigParser
    from weibo_login import login

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


__prog__= "weibo_scrapy"
__site__= "http://yoyzhou.github.com"
__weibo__= "@pigdata"
__version__="0.1 beta"


#####global variables#####

visited_uids = set()
task_queue = Queue.Queue()
lock = threading.Lock()

scraped = 0
config_file = 'scrapy.ini'

class scrapy(object):
    
    global visited_uids
    global task_queue
    global lock
    
    global scraped
    global config_file
    
    #//TODO add config file feature
    def __init__(self, config=None, thread_number=None, start_uid=None, uids_file=None):
        
        _config = {}
        if config:
            _config = self.__load_configuration__(config)
        else:
            _config = self.__load_configuration__(config_file)
        
        self.login_username = _config['login_username']
        self.login_uid = _config['login_uid']
        self.login_password = _config['login_password']
        self.cookies_file = _config['cookies_file']
        
        #get scrapy settings
        self.thread_number = _config['thread_number']
        
        self.start_uid = _config['start_uid']
        self.uids_file = _config['uids_file']
        self.wanted = _config[ 'wanted']
        
        #accepts arguments also, and arguments have higher priority
        if thread_number:
            self.thread_number = thread_number
        if start_uid and uids_file:
            raise Exception('You can only specify `start_uid` or `uids_file` in constructor')  
          
        if start_uid:
            self.start_uid = start_uid
            self.uids_file = None
        if uids_file:
            self.uids_file = uids_file
            self.start_uid = None
        
    def scrapy(self):
        
        login_status = login(self.login_username, self.login_password, self.cookies_file)
    
        if login_status:
            
            if self.start_uid:
                task_queue.put(self.start_uid)
            
            elif self.uids_file:
                uids_list = self.__load_uids__()
                for uid in uids_list:
                    task_queue.put(uid)
                
            else: #start uid or uids file is needed
                raise Exception('ERROR: Start uid or uids file is needed.') 
           
            #spawn a pool of threads, and pass them queue instance 
            for _ in range(self.thread_number):
                st = scrapy_threading(self.scrapy_do_task, self.wanted)
                st.setDaemon(True)
                st.start()
                
            
            task_queue.join()
                

    def scrapy_do_task(self, uid=None):
        '''
        User needs to implements this method to perform scrapy task, which based on weibo uid.
        @param uid: weibo uid
        @return: a list of uids gained from this task
        '''
        #return []
        pass
    
    def __load_configuration__(self, config_file):
        config = ConfigParser.RawConfigParser(allow_no_value=True)
        config.read(config_file)
        settings = {}
        #get login account user info
        settings['login_username'] = config.get('login_account_info', 'login_username')
        settings['login_uid'] = config.get('login_account_info', 'login_uid')
        settings['login_password'] = config.get('login_account_info', 'login_password')
        settings['cookies_file'] = config.get('login_account_info', 'cookies_file')
        
        #get scrapy settings
        settings['thread_number'] = config.getint('scrapy_settings', 'thread_number')
        settings['start_uid'] = config.get('scrapy_settings', 'start_uid')
        settings['uids_file'] = config.get('scrapy_settings', 'uids_file')
        settings['wanted'] = config.getint('scrapy_settings', 'wanted')
        
        return settings
    
    def __load_uids__(self):
        '''
        Loads uids from file. File should be formatted as one uid on each line.
        '''
        uids_list = []
        with open(self.uids_file, 'r') as uids:
            for uid in uids:
                if uid:
                    uids_list.append(uid.strip())
       
        return uids_list
 
class scrapy_threading(threading.Thread):
    """Thread class to handle scrapy task"""
    
    def __init__(self, task, wanted):
        threading.Thread.__init__(self)
        self.do_task = task
        self.wanted = wanted
        
    def run(self):
        global visited_uids
        global task_queue
        global scraped
        global lock
    
        while scraped < self.wanted:
            
            #crawl info based on each uid
            if task_queue:
              
                uid = task_queue.get()
                
                if uid in visited_uids: #already crawled
                    task_queue.task_done()
                
                else:
                    try:
                        gains = self.do_task(uid)
                        
                        #per debug
                        wow = '{0: <25}'.format('[' + time.asctime() + '] ') + ' uid_' + '{0: <12}'.format(uid)
                        print wow
                        for uid in gains:
                            task_queue.put(uid)
                        
                        #signals that queue job is done
                        task_queue.task_done()
                        
                        #counting scrapied number
                        with lock:
                            scraped += 1
                            #per debug
                            print 'scraped: ' + str(scraped)
                            
                    except Exception, e:
                        print e
                        pass
                        
            else:
                time.sleep(30)
            