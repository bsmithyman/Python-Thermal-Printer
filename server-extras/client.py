#!/usr/bin/env python

import sys
import urllib2

posturl = 'http://192.168.48.16:5000/xml'
headers = {
  'Content-Type':	'text/xml',
}

infile = 'testmaterial.xml'

with open(infile, 'r') as fp:
  xml = fp.read()

req = urllib2.Request(posturl)
req.headers.update(headers)
req.data = xml

url = urllib2.urlopen(req)

response = url.read()

print(response)

