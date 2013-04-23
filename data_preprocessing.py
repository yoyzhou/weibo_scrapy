#!/usr/bin/env python
#coding=utf8

'''
Created on Apr 9, 2013

@author: yoyzhou
'''

import os
from os.path import join

def concatenateAll(following_files_folder):
    '''
    Concatenate all weibo info resided in following files, in which each line presents a following user.
    Function needs to eliminate duplications
    '''
    following_user_all = open('following_user_all.txt', 'w')
    uids = set()
    
    for root, _, files in os.walk(following_files_folder):
        for following_file in files:
            with open(join(root, following_file)) as followings:
                for line in followings:
                    if line.strip():
                        try:
                            uid = line.split('*_*')[0].split(':')[1]
                            if not uid in uids:
                                uids.add(uid)
                                following_user_all.write(line)
                        except:
                            print line + following_file
                            pass
                            
    with open('following_uid_all.txt', 'w') as f_all:
        f_all.write('\n'.join(uids))
    
    following_user_all.flush()
    following_user_all.close()

def aggregate_following_ntk(following_files_folder):
    '''
    Aggregate user following network from all the following files, note each file contains all the followings of
    one individual user, whose uid is the prefix of file name. like xxxxxxxxxx_his_followings.txt where xxxxxxxxxx 
    is the user uid. 
    '''
   
    following_ntk = open('following_ntk.txt', 'w')
    
    for root, _, files in os.walk(following_files_folder):
        for following_file in files:
            user_uid = following_file.split('_')[0] #the prefix is user uid
            with open(join(root, following_file)) as follows_file:
                followings = []
                for line in follows_file:
                    if line.strip():
                        try:
                            uid = line.split('*_*')[0].split(':')[1]
                            followings.append(uid)
                        except:
                            print line + following_file
                            pass
                following_ntk.write(user_uid + ':' + ','.join(followings) + '\n')
                            
    following_ntk.flush()
    following_ntk.close()
    
if __name__ == '__main__':
    concatenateAll('D:\\dataset\\weibo\\data\\followings')
    aggregate_following_ntk('D:\\dataset\\weibo\\data\\followings')