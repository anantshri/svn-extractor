Svn-Extractor
=============

Many a times web application pen-testers are encountered with the presence of .svn folders. For those not aware .svn folder is used by SVN version control system to perform its operations. For a blackbox pentest this folder contains huge amount of information.
Some of the key areas where this can help includes.

1) Uncover hidden files and folder names

2) Access the source code of the files.

3) download files even if the restrictions are in place at htaccess.

How this could be achieved.

1) Uncover hidden files and folder names

There are two ways in which this can be achieved based on the version of SVN in use.  
for <1.6 we had .svn/entries files which contained list of files / folders as well as usernames used for commiting those files.  
for >1.6 we have .svn/wc.db which contains simmilar data but in a sqlite3 format.  
These files could be directly accessible through url.

2) Access the source code / download files even if htaccess blocks its access.

SVN keeps a backup copy of all files in two seperate locations.

1) .svn/text-base/ **"filename"** .svn-base  
2) .svn/pristine/ **"XX"** / **"CHECKSUM"** .svn-base

where

**filename** is actual name of file.

**CHECKSUM** is Sha1 sum of the file

**XX** is first two character of **CHECKSUM**.

first type of entries has one limitations suppose file name is testme.php so path becomes.

*.svn/text-base/testme.php.svn-base*

a large number of servers will execute the file and serve the output.

that's where option 2 shines however this information is available only in case of wc.db (>1.6 SVN version) and this requires that .sv/pristine directory should be web accessible.

However after searching a lot i was not able to find a single code which can do both these things in one go.

so here is a tool which can perform both the operations in one script.

Usage
=====
**minimal**  

svn-extractor.py --url "url with .svn available"

**alloptions**  

```
$ python svnextractor.py --help  
usage: svn_extractor.py [-h] --url TARGET [--debug] [--noextract] [--userlist]
                        [--wcdb] [--entries] [--proxy PROXY] [--match MATCH]

This program is used to extract the hidden SVN files from a webhost
considering either .svn entries file (<1.6) or wc.db (> 1.7) are available
online. This program actually automates the directory navigation and text
extraction process

optional arguments:
  -h, --help     show this help message and exit
  --url TARGET   Provide URL
  --debug        Provide debug information
  --noextract    Don't extract files just show content
  --userlist     show the usernames used for commit
  --wcdb         check only wcdb
  --entries      check only .svn/entries file
  --proxy PROXY  Provide HTTP Proxy in http(s)://host:port format
  --match MATCH  only download files that match regex

Credit (C) Anant Shrivastava http://anantshri.info Greets to Amol Naik, Akash
Mahajan, Prasanna K, Lava Kumar for valuable inputs
```

References
==========
It would be unfair to say that i did all the research myself so here are the links to various resources i used to get the info out.

1) http://pen-testing.sans.org/blog/pen-testing/2012/12/06/all-your-svn-are-belong-to-us (manual technique for wc.db)

2) http://www.adamgotterer.com/post/28125474053/hacking-the-svn-directory-archive (manual technique for .svn/entries)

3) http://www.cirt.net/svnpristine (only automated tool i can find online doing wc.db magic)
