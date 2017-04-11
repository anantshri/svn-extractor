#!/bin/python

import requests
import sys
import argparse
import os
import sqlite3
import traceback
import re
# disable insecurerequestwarning
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def getext(filename):
    name, ext = os.path.splitext(filename)
    return ext[1:]

def readsvn(data,urli,match,proxy_dict):
    old_line=""
    file_list=""
    dir_list=""
    user = ""
    pattern = re.compile(match, re.IGNORECASE)
    global author_list
    global excludes
    if not urli.endswith('/'):
        urli = urli + "/"    
    for a in data.text.splitlines():
        #below functionality will find all usernames from svn entries file
        if (a == "has-props"):
            author_list.append(old_line)
        if (a == "file"):
            if not pattern.search(old_line):
                continue
            ignore = getext(old_line) in excludes
            if ignore: print urli + old_line, '(not extracted)'
            else: print urli + old_line
            if no_extract and not ignore:
                save_url_svn(urli,old_line,proxy_dict)
            file_list=file_list + ";" +  old_line
        if (a == "dir"):
            if old_line != "":
                folder_path = os.path.join("output", urli.replace("http://","").replace("https://","").replace("/",os.path.sep),  old_line)
                if not os.path.exists(folder_path):
                    if no_extract:
                        os.makedirs(folder_path)
                dir_list = dir_list + ";" + old_line
                print urli + old_line
                try:
                    d=requests.get(urli+old_line + "/.svn/entries", verify=False,proxies=(proxy_dict))
                    readsvn(d,urli+old_line,match,proxy_dict)
                except:
                    print "Error Reading %s%s/.svn/entries so killing" % (urli, old_line)
                    
        old_line = a
    return file_list,dir_list,user

def readwc(data,urli,match,proxy_dict):
    folder = os.path.join("output", urli.replace("http://","").replace("https://","").replace("/",os.path.sep))
    pattern = re.compile(match, re.IGNORECASE)
    global author_list
    global excludes
    if not folder.endswith(os.path.sep):
        folder = folder  + os.path.sep
    with open(folder + "wc.db","wb") as f:
        f.write(data.content)
    conn = sqlite3.connect(folder + "wc.db")
    c = conn.cursor()
    try:
        c.execute('select local_relpath, ".svn/pristine/" || substr(checksum,7,2) || "/" || substr(checksum,7) || ".svn-base" as alpha from NODES where kind="file";')
        list_items = c.fetchall()
        #below functionality will find all usernames who have commited atleast once.
        c.execute('select distinct changed_author from nodes;')
        author_list = [r[0] for r in c.fetchall()]
        c.close()
        for filename,url_path in list_items:
            if not pattern.search(filename):
                continue
            ignore = getext(filename) in excludes
            if ignore: print urli + filename, '(not extracted)'
            else: print urli + filename
            if no_extract and not ignore:
                save_url_wc(urli,filename,url_path,proxy_dict)
    except Exception,e:
        print "Error reading wc.db, either database corrupt or invalid file"
        if show_debug:
            traceback.print_exc()
        return 1
    return 0

def show_list(list,statement):
	print statement
	cnt=1
	for x in set(list):
		print str(cnt) + " : " + str(x)
		cnt = cnt + 1

def save_url_wc(url,filename,svn_path,proxy_dict):
    global author_list 
    if filename != "":
        if svn_path is None:
            folder_path = os.path.join("output", url.replace("http://","").replace("https://","").replace("/",os.path.sep, filename.replace("/",os.path.sep)))
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
        else:
            folder = os.path.join("output", url.replace("http://","").replace("https://","").replace("/",os.path.sep), os.path.dirname(filename).replace("/",os.path.sep))
            if not os.path.exists(folder):
                os.makedirs(folder)
            if not folder.endswith(os.path.sep):
                folder = folder  + os.path.sep
            try:
                r=requests.get(url + svn_path, verify=False,proxies=(proxy_dict))
                with open(folder+os.path.basename(filename),"wb") as f:
                    f.write(r.content)
            except Exception,e:
                print "Error while accessing : " + url + svn_path
                if show_debug:
                    traceback.print_exc()

    return 0

def save_url_svn(url,filename,proxy_dict):
    global author_list
    folder=os.path.join("output", url.replace("http://","").replace("https://","").replace("/",os.path.sep))
    if not folder.endswith(os.path.sep):
        folder = folder  + os.path.sep
    try:
        r=requests.get(url + "/.svn/text-base/" + filename + ".svn-base", verify=False,proxies=(proxy_dict))
        if not os.path.isdir(folder+filename):
            with open(folder + filename,"wb") as f:
                f.write(r.content)
    except Exception,e:
        print "Problem saving the URL"
        if show_debug:
            traceback.print_exc()
    return 0

def main(argv):
    target=''
    #placing global variables outside all scopes
    global show_debug
    global no_extract
    global excludes
    global author_list 
    author_list=[]
    desc="""This program is used to extract the hidden SVN files from a webhost considering
either .svn entries file (<1.6)
or wc.db (> 1.7) are available online.
This program actually automates the directory navigation and text extraction process"""
    epilog="""Credit (C) Anant Shrivastava http://anantshri.info. Contributions from orf, sullo, paddlesteamer. 
    Greets to Amol Naik, Akash Mahajan, Prasanna K, Lava Kumar for valuable inputs"""
    parser = argparse.ArgumentParser(description=desc,epilog=epilog)
    parser.add_argument("--url",help="Provide URL",dest='target',required=True)
    parser.add_argument("--debug",help="Provide debug information",action="store_true")
    parser.add_argument("--noextract",help="Don't extract files just show content",action="store_false")
    #using no extract in a compliment format if its defined then it will be false hence
    parser.add_argument("--userlist",help="show the usernames used for commit",action="store_true")
    parser.add_argument("--wcdb", help="check only wcdb",action="store_true")
    parser.add_argument("--entries", help="check only .svn/entries file",action="store_true")
    parser.add_argument("--proxy",help="Provide HTTP Proxy in http(s)://host:port format", dest='proxy',required=False)
    parser.add_argument("--match", help="only download files that match regex")
    parser.add_argument("--exclude", help="exclude files with extensions separated by ','",dest='excludes',default='')
    x=parser.parse_args()
    url=x.target
    no_extract=x.noextract
    show_debug=x.debug
    match=x.match
    excludes = x.excludes.split(',')
    prox=x.proxy
    proxy_dict=""
    if prox != None:
        print prox
        print "Proxy Defined"
        proxy_dict = {"http":prox,"https":prox}
    else:
        print "Proxy not defined"
        proxy_dict = ""
    if (match):
        print "Only downloading matches to %s" % match
        match="("+match+"|entries$|wc.db$)"  # need to allow entries$ and wc.db too
    else:
        match=""
    if (x.wcdb and x.entries):
        print "Checking both wc.db and .svn/entries (default behaviour no need to specify switch)"
        x.wcdb = False
        x.entries=False
    if url is None:
        exit()
    print url
    if not url.endswith('/'):
        url = url + "/"
    print "Checking if URL is correct"
    try:
        r=requests.get(url, verify=False,proxies=(proxy_dict))
    except Exception,e:
        print "Problem connecting to URL"
        if show_debug:
            traceback.print_exc()
        exit()
    if [200,403,500].count(r.status_code) > 0:
        print "URL is active"
        if no_extract:
            folder_path=os.path.join("output",  url.replace("http://","").replace("https://","").replace("/",os.path.sep))
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
        if not x.entries:
            print "Checking for presence of wc.db"
            r=requests.get(url + "/.svn/wc.db", verify=False,allow_redirects=False,proxies=(proxy_dict))
            if r.status_code == 200:
                print "WC.db found"
                rwc=readwc(r,url,match,proxy_dict)
                if rwc == 0:
                    if x.userlist:
                        show_list(author_list,"List of Usersnames used to commit in svn are listed below")
                        exit()
        else:
            if show_debug:
                print "Status code returned : " + str(r.status_code)
                print "Full Respose"
                print r.text
            print "WC.db Lookup FAILED"
        if not x.wcdb:
            print "lets see if we can find .svn/entries"
            #disabling redirection to make sure no redirection based 200ok is captured.
            r=requests.get(url + "/.svn/entries", verify=False,allow_redirects=False,proxies=(proxy_dict))
            if r.status_code == 200:
                print "SVN Entries Found if no file listed check wc.db too"
                data=readsvn(r,url,match,proxy_dict)
                if 'author_list' in globals() and x.userlist:
                    show_list(author_list,"List of Usernames used to commit in svn are listed below")
                    #print author_list
                    exit();
            else:
                if show_debug:
                    print "Status code returned : " + str(r.status_code)
                    print "Full Respose"
                    print r.text
                print ".svn/entries Lookup FAILED"
        print (url + " doesn't contains any SVN repository in it")
    else:
        print "URL returns " + str(r.status_code)
        exit()

	
if __name__ == "__main__":
   main(sys.argv[1:])
