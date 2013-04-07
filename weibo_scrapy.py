#!/usr/bin/env python
#coding=utf8

try:
    import os
    import sys
    import time
    import threading
    import Queue
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


__prog__= "weibo_login"
__site__= "http://yoyzhou.github.com"
__weibo__= "@pigdata"
__version__="0.1 beta"


#####global variables define#####

visited_uids = set()
task_queue = Queue.Queue()
lock = threading.Lock()

scraped = 0
wanted = 10000000

username        = r'ur_account'          
pwd                 = r'ur_password'     
           
myuid              =  '1248521225'
cookie_file        = 'cookies.dat'


class scrapy(object):
    
    
    
    global username
    global pwd
    global cookie_file
    
    global visited_uids
    global task_queue
    global scraped
    global wanted
    global lock
    
    #//TODO add config file feature
    def __init__(self, thread_number=10, start_uid=None, uids_file=None):
        
        self.task_worker = self.scrapy_do_task
        self.thread_number = thread_number
        self.start_uid = start_uid
        self.uids_file = uids_file
        
        
    def scrapy(self):
        login_status = login(username,pwd,cookie_file)
    
        
        if login_status:
            #saver(uid,output_file)
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
                
               st = scrapy_threading(self.task_worker, wanted)
               st.setDaemon(True)
               st.start()
                
            
            task_queue.join()
                

    def scrapy_do_task(self, uid=None):
         '''
        User needs to implements this method to perform scrapy task, which based on weibo uid.
        @param uid: weibo uid
        @return: a list of uids gained from this task
        '''
         return []
             
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
                        
                        wow = '{0: <25}'.format('[' + time.asctime() + '] ') + ' uid_' + '{0: <12}'.format(uid)
                        #logging.info(wow)
                        print wow
                        for uid in gains:
                            task_queue.put(uid)
                        
                        #signals that queue job is done
                        task_queue.task_done()
                        
                        #counting scrapied number
                        with lock:
                            scraped += 1
                            print 'scraped: ' + str(scraped)
                            
                    except Exception, e:
                        print e
                        pass
                        
            else:
                time.sleep(30)
            
    
    
    
