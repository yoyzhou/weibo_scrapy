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
    Concatenate all weibo user info resided in following files, in which each line presents a following user.
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

def user_info_to_csv(user_info_file):
    
    users_needed = set()
    with open('fntk.csv', 'r') as fntk:
        for line in fntk:
            uids = line.split('\t')
            if not uids[0] in users_needed:
                users_needed.add(uids[0])
            if not uids[1] in users_needed:
                users_needed.add(uids[1])
                
    user_info_csv = open('following_user_needed.csv', 'w')
    
    user_info_csv.write('Id\tLabel\tSex\n' )
    with open(user_info_file) as userinfos:
        for line in userinfos:
             info_dict = {}
             if line.strip():
                 try:
                     infos = line.split('*_*')
                     for info in infos:
                        field = info.split(':')[0]
                        value = info.split(':')[1]
                        info_dict[field.strip()] = value.strip()
                 except:
                        print line + following_file
                        pass
             str_info = ''
#             str_info += info_dict['uid'] + '\t' + info_dict['sex'] + '\t' + \
#                               info_dict['fnick'] + '\t' + info_dict['name'] + '\t' +\
#                               info_dict['face'] + '\t' + info_dict['address'] + '\t' +\
#                               info_dict['connect'] + '\n'
             if info_dict['uid'] in users_needed:
                 str_info += info_dict['uid'] + '\t'  + info_dict['name'] + '\t' + info_dict['sex']  + '\n'
                 user_info_csv.write(str_info )
            
             
        user_info_csv.flush()
        user_info_csv.close()
        
        
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
    #concatenateAll('D:\\dataset\\weibo\\data\\followings')
    #aggregate_following_ntk('D:\\dataset\\weibo\\data\\followings')
    
    user_info_to_csv('following_user_all.txt')