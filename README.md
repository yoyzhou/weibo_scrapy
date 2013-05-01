WEIBO_SCRAPY
============

WEIBO\_SCRAPY是一个PYTHON实现的，使用多线程抓取WEIBO信息的框架。WEIBO\_SCRAPY框架给用户提供WEIBO的模拟登录和多线程抓取微博信息的接口，让用户只需关心抓取的业务逻辑，而不用处理棘手的WEIBO模拟登录和多线程编程。

WEIBO\_SCRAPY is a **Multi-Threading** SINA WEIBO data extraction Framework in Python. WEIBO\_SCRAPY provides WEIBO login simulator and interface for WEIBO data extraction with multi-threading, it saves users a lot of time by getting users out of writing WEIBO login simulator from scratch and multi-threading programming, users now can focus on their own **extraction** logic.


=======

###WEIBO\_SCRAPY的功能
1\. 微博模拟登录

2\. 多线程抓取框架

3\. **抓取任务**接口

4\. 抓取参数配置

###WEIBO\_SCRAPY Provides
1\. WEIBO Login Simulator

2\. Multi-Threading Extraction Framework

3\. **Extraction Task** Interface

4\. Easy Way of Parameters Configuration

###How to Use WEIBO\_SCRAPY
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
		     print 'WOW...'
		     return 'replace this string with uid list which gained from this task'
		 
	if __name__ == '__main__':
		
		s = my_scrapy(uids_file = 'uids_all.txt', config = 'my.ini')
		s.scrapy()

###相关阅读(Readings)
[基于UID的WEIBO信息抓取框架WEIBO_SCRAPY](http://yoyzhou.github.io/blog/2013/04/08/weibo-scrapy-framework-with-multi-threading/)
