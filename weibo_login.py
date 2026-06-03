#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Created on Mar 18, 2013

@author: yoyzhou
'''

try:
    import os
    import sys
    import urllib.parse
    import urllib.request
    import http.cookiejar
    import base64
    import re
    import hashlib
    import json
    import rsa
    import binascii

except ImportError as e:
    print(f"""\

There was a problem importing one of the Python modules required.
The error leading to this problem was:

{e}

Please install a package which provides this module, or
verify that the module is installed correctly.

It's possible that the above module doesn't match the current version of Python,
which is:

{sys.version}

""", file=sys.stderr)
    sys.exit(1)


__prog__ = "weibo_login"
__site__ = "http://yoyzhou.github.com"
__weibo__ = "@pigdata"
__version__ = "0.1 beta"


def get_prelogin_status(username):
    """
    Perform prelogin action, get prelogin status, including servertime, nonce, rsakv, etc.
    """
    prelogin_url = 'http://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&su=' + get_user(username) + \
     '&rsakt=mod&checkpin=1&client=ssologin.js(v1.4.5)'
    data = urllib.request.urlopen(prelogin_url).read()
    p = re.compile(r'\((.*)\)')
    
    try:
        json_data = p.search(data.decode('utf-8')).group(1)
        data = json.loads(json_data)
        servertime = str(data['servertime'])
        nonce = data['nonce']
        rsakv = data['rsakv']
        return servertime, nonce, rsakv
    except Exception as e:
        print(f'Getting prelogin status met error: {e}')
        return None


def login(username, pwd, cookie_file):
    """
        Login with use name, password and cookies.
        (1) If cookie file exists then try to load cookies;
        (2) If no cookies found then do login
    """
    # If cookie file exists then try to load cookies
    if os.path.exists(cookie_file):
        try:
            cookie_jar = http.cookiejar.LWPCookieJar(cookie_file)
            cookie_jar.load(ignore_discard=True, ignore_expires=True)
            loaded = 1
        except http.cookiejar.LoadError:
            loaded = 0
            print('Loading cookies error')
        
        # install loaded cookies for urllib
        if loaded:
            cookie_support = urllib.request.HTTPCookieProcessor(cookie_jar)
            opener = urllib.request.build_opener(cookie_support, urllib.request.HTTPHandler)
            urllib.request.install_opener(opener)
            print('Loading cookies success')
            return 1
        else:
            return do_login(username, pwd, cookie_file)
    
    else:  # If no cookies found
        return do_login(username, pwd, cookie_file)


def do_login(username, pwd, cookie_file):
    """
    Perform login action with use name, password and saving cookies.
    @param username: login user name
    @param pwd: login password
    @param cookie_file: file name where to save cookies when login succeeded 
    """
    # POST data per LOGIN WEIBO, these fields can be captured using httpfox extension in FIrefox
    login_data = {
        'entry': 'weibo',
        'gateway': '1',
        'from': '',
        'savestate': '7',
        'userticket': '1',
        'pagerefer': '',
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

    cookie_jar2 = http.cookiejar.LWPCookieJar()
    cookie_support2 = urllib.request.HTTPCookieProcessor(cookie_jar2)
    opener2 = urllib.request.build_opener(cookie_support2, urllib.request.HTTPHandler)
    urllib.request.install_opener(opener2)
    login_url = 'http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.5)'
    try:
        servertime, nonce, rsakv = get_prelogin_status(username)
    except Exception as e:
        print(f'Error getting prelogin status: {e}')
        return 0
    
    # Fill POST data
    login_data['servertime'] = servertime
    login_data['nonce'] = nonce
    login_data['su'] = get_user(username)
    login_data['sp'] = get_pwd_rsa(pwd, servertime, nonce)
    login_data['rsakv'] = rsakv
    login_data_encoded = urllib.parse.urlencode(login_data).encode('utf-8')
    http_headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:8.0) Gecko/20100101 Firefox/8.0'}
    req_login = urllib.request.Request(
        url=login_url,
        data=login_data_encoded,
        headers=http_headers
    )
    result = urllib.request.urlopen(req_login)
    text = result.read().decode('utf-8')
    p = re.compile(r'location\.replace\("(.*?)"\)')  # double quote regex
    ps = re.compile(r"location\.replace\('(.*?)'\)")  # single quote regex
    
    try:
        # Search login redirection URL
        try:
            # first try with double quote regex
            login_url = p.search(text).group(1)
        except Exception:
            # try with single quote regex
            login_url = ps.search(text).group(1)
            
        data = urllib.request.urlopen(login_url).read().decode('utf-8')
        
        # Verify login feedback, check whether result is TRUE
        patt_feedback = r'feedBackUrlCallBack\((.*)\)'
        p = re.compile(patt_feedback, re.MULTILINE)
        
        feedback = p.search(data).group(1)
        
        feedback_json = json.loads(feedback)
        if feedback_json['result']:
            cookie_jar2.save(cookie_file, ignore_discard=True, ignore_expires=True)
            return 1
        else:
            return 0
    except Exception as e:
        print(f'Login error: {e}')
        return 0


def get_pwd_wsse(pwd, servertime, nonce):
    """
        Get wsse encrypted password
    """
    pwd1 = hashlib.sha1(pwd.encode('utf-8')).hexdigest()
    pwd2 = hashlib.sha1(pwd1.encode('utf-8')).hexdigest()
    pwd3_ = pwd2 + servertime + nonce
    pwd3 = hashlib.sha1(pwd3_.encode('utf-8')).hexdigest()
    return pwd3


def get_pwd_rsa(pwd, servertime, nonce):
    """
    Get rsa2 encrypted password, using RSA module from https://pypi.python.org/pypi/rsa/3.1.1, documents can be accessed at 
    http://stuvel.eu/files/python-rsa-doc/index.html
    """
    # n, n parameter of RSA public key, which is published by WEIBO.COM
    # hardcoded here but you can also find it from values return from prelogin status above
    weibo_rsa_n = 'EB2A38568661887FA180BDDB5CABD5F21C7BFD59C090CB2D245A87AC253062882729293E5506350508E7F9AA3BB77F4333231490F915F6D63C55FE2F08A49B353F444AD3993CACC02DB784ABBB8E42A9B1BBFFFB38BE18D78E87A0E41B9B8F73A928EE0CCEE1F6739884B9777E4FE9E88A1BBE495927AC4A799B3181D6442443'
    
    # e, exponent parameter of RSA public key, WEIBO uses 0x10001, which is 65537 in Decimal
    weibo_rsa_e = 65537
   
    message = str(servertime) + '\t' + str(nonce) + '\n' + str(pwd)
    
    # construct WEIBO RSA Publickey using n and e above, note that n is a hex string
    key = rsa.PublicKey(int(weibo_rsa_n, 16), weibo_rsa_e)
    
    # get encrypted password
    encropy_pwd = rsa.encrypt(message.encode('utf-8'), key)

    # turn back encrypted password binaries to hex string
    return binascii.b2a_hex(encropy_pwd).decode('utf-8')


def get_user(username):
    username_ = urllib.parse.quote(username)
    username = base64.encodebytes(username_.encode('utf-8'))[:-1]
    return username.decode('utf-8')


if __name__ == '__main__':
    
    username = 'ur_user_name_here'
    pwd = 'ur_password_here'
    cookie_file = 'weibo_login_cookies.dat'
    
    if login(username, pwd, cookie_file):
        print('Login WEIBO succeeded')
    else:
        print('Login WEIBO failed')
