#!/usr/bin/python

'''
Copyright (c) <2012> Tarek Galal <tare2.galal@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this 
software and associated documentation files (the "Software"), to deal in the Software 
without restriction, including without limitation the rights to use, copy, modify, 
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to 
permit persons to whom the Software is furnished to do so, subject to the following 
conditions:

The above copyright notice and this permission notice shall be included in all 
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR 
A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF 
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

__author__ = "Debarko De"
__version__ = "0.1"
__email__ = "debarko89@gmail.com"
__license__ = "MIT"

import argparse, sys, os, csv
import random
import urllib
import unicodedata
from Yowsup.Common.utilities import Utilities
from Yowsup.Common.debugger import Debugger
from Yowsup.Common.constants import Constants
from Examples.CmdClient import WhatsappCmdClient
from Examples.EchoClient import WhatsappEchoClient
from Examples.ListenerClient import WhatsappListenerClient
from Yowsup.Registration.v2.existsrequest import WAExistsRequest as WAExistsRequestV2
from Yowsup.Registration.v2.coderequest import WACodeRequest as WACodeRequestV2
from Yowsup.Registration.v2.regrequest import WARegRequest as WARegRequestV2
from Yowsup.Contacts.contacts import WAContactsSyncRequest

import threading,time, base64

def resultToString(result):
	unistr = str if sys.version_info >= (3, 0) else unicode
	out = []
	for k, v in result.items():
		if v is None:
			continue
		out.append("%s: %s" %(k, v.encode("utf-8") if type(v) is unistr else v))
		
	return "\n".join(out)

def application(environ, start_response):
    Debugger.enabled = False
    qry = environ.get('QUERY_STRING', 0)
    qry_string = qry.split('&')
    username = ''
    password = ''
    method = ''
    message = ''
    to=''
    via=''
    cc=''
    code=''
    id_user=''
    output=''
    contact=''
    for x in range(0, len(qry_string)):
    	param = qry_string[x]
    	param = param.split('=',1)
    	if param[0]=="username":
    		username = param[1]
    	if param[0]=="password":
    		password = param[1]
    	if param[0]=="method":
    		method = param[1]
    	if param[0]=="message":
            message = param[1]
            message = urllib.unquote(message).decode('utf8')
            message = unicodedata.normalize('NFKD', message).encode('ascii','ignore')
    	if param[0]=="to":
    		to = param[1]
    	if param[0]=="via":
    		via = param[1]
    	if param[0]=="cc":
    		cc = param[1]
    	if param[0]=="code":
    		code=param[1]
    	if param[0]=="id_user":
    		id_user=param[1]
        if param[0]=="contacts":
            contact=param[1]
        if param[0]=="debug":
            Debugger.enabled = True
    password = base64.b64decode(bytes(password.encode('utf-8')))
    if method=="send":
    	wa = WhatsappEchoClient(to, message, False)
    	wa.login(cc+username, password)
        output = "sent"
    if method=="register":
    	wc = WACodeRequestV2(cc, username, id_user, via)
    	result = wc.send()
    	output = resultToString(result)

    if method=="sendcode":
    	code = "".join(code.split('-'))
    	wr = WARegRequestV2(cc, username, code, id_user)
    	result = wr.send()
    	output=resultToString(result)

    if method=="listen":
    	wa = WhatsappListenerClient(False, True)
    	status = wa.login(cc+username, password)
    	if status=="SUCCESS":
    		time.sleep(2)
    		output = wa.getMessages()
    	else:
    		output = "FAIL"
    	wa.disconnect("graceful")

    if method=="status":
        output = "fine"

    if method=="sync":
        output = "yay"
        wsync = WAContactsSyncRequest(cc+username, password, contact)
        result = wsync.send()
        output = resultToString(result)

    status = '200 OK'
    response_headers = [('Content-type', 'text/html'),('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    return [output]