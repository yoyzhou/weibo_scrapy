#!/usr/bin/env python
#coding=utf8

from weibo_scrapy import scrapy


class my_scrapy(scrapy):
    
    def scrapy_do_task(self, uid=None):
         '''
        User needs to overwrite this method to perform uid-based scrapy task.
        @param uid: weibo uid
        @return: a list of uids gained from this task, optional
        '''
         super(my_scrapy, self).__init__(**kwds)
         
         #do what you want with uid here, note that this scrapy is uid based, so make sure there are uids in task queue, 
         #or gain new uids from this function
         
         return 'replace this string with uid list which gained from this task'
     
if __name__ == '__main__':
    
    s = my_scrapy(start_uid = '1197161814')
    s.scrapy()
    