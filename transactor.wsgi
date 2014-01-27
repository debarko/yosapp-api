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

DEFAULT_CONFIG = os.path.expanduser("~")+"/.yowsup/auth"
COUNTRIES_CSV = "countries.csv"


def resultToString(result):
	unistr = str if sys.version_info >= (3, 0) else unicode
	out = []
	for k, v in result.items():
		if v is None:
			continue
		out.append("%s: %s" %(k, v.encode("utf-8") if type(v) is unistr else v))
		
	return "\n".join(out)

def getCredentials(config = DEFAULT_CONFIG):
	if os.path.isfile(config):
		f = open(config)
		
		phone = ""
		idx = ""
		pw = ""
		cc = ""
		
		try:
			for l in f:
				line = l.strip()
				if len(line) and line[0] not in ('#',';'):
					
					prep = line.split('#', 1)[0].split(';', 1)[0].split('=', 1)
					
					varname = prep[0].strip()
					val = prep[1].strip()
					
					if varname == "phone":
						phone = val
					elif varname == "id":
						idx = val
					elif varname =="password":
						pw =val
					elif varname == "cc":
						cc = val

			return (cc, phone, idx, pw);
		except:
			pass

	return 0

def dissectPhoneNumber(phoneNumber):
	try:
		with open(COUNTRIES_CSV, 'r') as csvfile:
			reader = csv.reader(csvfile, delimiter=',')
			for row in reader:
				if len(row) == 3:
					country, cc, mcc = row
				else:
					country,cc = row
					mcc = "000"
				try:
					if phoneNumber.index(cc) == 0:
						print("Detected cc: %s"%cc)
						return (cc, phoneNumber[len(cc):])

				except ValueError:
					continue
				
	except:
		pass
	return False

def application(environ, start_response):
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
    password = base64.b64decode(bytes(password.encode('utf-8')))
    if method=="send":
    	wa = WhatsappEchoClient(to, message, False)
    	wa.login(cc+username, password)
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
    	wa.login(username, password)
    status = '200 OK'
    response_headers = [('Content-type', 'text/html'),('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    return [output]

parser = argparse.ArgumentParser(description='yowsup-cli Command line options')

clientsGroup = parser.add_argument_group("Client options")

regGroup = parser.add_argument_group("Registration options")


modes = clientsGroup.add_mutually_exclusive_group()
modes.add_argument('-l','--listen', help='Listen to messages', action="store_true", required=False, default=False)
modes.add_argument('-s','--send', help="Send message to phone number and close connection. Phone is full number including country code, without '+' or '00'", action="store",  nargs=2, metavar=('<phone>','<message>'), required=False)
modes.add_argument('-i','--interactive', help="Start an interactive conversation with a contact. Phone is full number including country code, without '+' or '00'", action="store", metavar='<phone>', required=False)
modes.add_argument('-b','--broadcast', help="Broadcast message to multiple recepients, comma seperated", action="store", nargs=2, metavar=('<jids>', '<message>'), required=False)

#modes.add_argument('-b','--bot', help='Bot', action="store_true", required=False, default=False)


clientsGroup.add_argument('-w','--wait', help='If used with -s, then connection will not close until server confirms reception of the message', action="store_true", required=False, default=False)
clientsGroup.add_argument('-a','--autoack', help='If used with -l or -i, then a message received ack would be automatically sent for received messages', action="store_true", required=False, default=False)
clientsGroup.add_argument('-k','--keepalive', help="When used with -l or -i, Yowsup will automatically respond to server's ping requests to keep connection alive", action="store_true", required=False, default=False)


regSteps = regGroup.add_mutually_exclusive_group()
regSteps.add_argument("-r", '--requestcode', help='Request the 3 digit registration code from Whatsapp.', action="store", required=False, metavar="(sms|voice)")
regSteps.add_argument("-R", '--register', help='Register account on Whatsapp using the provided 3 digit code', action="store", required=False, metavar="code")
regSteps.add_argument("-e", '--exists', help='Check if account credentials are valid. WARNING: Whatsapp now changes your password everytime you use this. Make sure you update your config file if the output informs about a password change', action="store_true", required=False)





contactOptions = parser.add_argument_group("Contacts options").add_mutually_exclusive_group();

contactOptions.add_argument('--sync', help='Sync provided numbers. Numbers should be comma-separated. If a number is not in international format, Whatsapp will assume your own country code for it. Returned data indicate which numbers are whatsapp users and which are not. For Whatsapp users, it will return some info about each user, like user status.', metavar="numbers", action="store", required=False)



debugTools = parser.add_argument_group("Debug tools").add_mutually_exclusive_group();

debugTools.add_argument('--generatepassword', help="Generate password from given string in same way Whatsapp generates it from a given IMEI or MAC Address", action="store", metavar="input")
debugTools.add_argument('--decodestring', help="Decode byte arrays found in decompiled version of Whatsapp. Tested with S40 version. Input should be comma separated without the enclosing brackets. Example: ./yowsup-cli --decodestring 112,61,100,123,114,103,96,114,99,99,61,125,118,103", action="store", metavar="encoded_array")


parser.add_argument("--help-config", help="Display info about configuration format", action="store_true")
parser.add_argument('-c','--config', help="Path to config file containing authentication info. For more info about config format use --help-config", action="store", metavar="file", required=False, default=False)
#parser.add_argument('-D','--dbus', help='Start DBUS interface', action="store_true", required=False, default=False)
parser.add_argument("--ignorecached", help="Don't use cached token if exists", action="store_true", required=False, default=False)
parser.add_argument('-d','--debug', help='Enable debug messages', action="store_true", required=False, default=False)
parser.add_argument('-v', '--version', help="Print version info and exit", action='store_true', required=False, default=False)


args = vars(parser.parse_args())
if len(sys.argv) == 1:
	#parser.print_help()
	a=0
elif args["version"]:
	print("yowsup-cli %s, using Yowsup %s"%(__version__, Constants.v))
else:
	credentials = getCredentials(args["config"] or DEFAULT_CONFIG)
	
	if credentials:

		countryCode, login, identity, password = credentials

		identity = Utilities.processIdentity(identity)
		password = base64.b64decode(bytes(password.encode('utf-8')))

		if countryCode:
			phoneNumber = login[len(countryCode):]
		else:
			dissected = dissectPhoneNumber(login)
			if not dissected:
					sys.exit("ERROR. Couldn't detect cc, you have to manually place it your config")
			countryCode, phoneNumber = dissected
				
		Debugger.enabled = args['debug']

		if args["ignorecached"]:
			Utilities.tokenCacheEnabled = False

		if args["interactive"]:
			val = args["interactive"]
			wa = WhatsappCmdClient(val, args['keepalive'] ,args['autoack'])
			wa.login(login, password)
		elif args['send']:
			phone = args["send"][0]
			message = args["send"][1]
			wa = WhatsappEchoClient(phone, message, args['wait'])
			wa.login(login, password)
		elif args['listen']:
			wa = WhatsappListenerClient(args['keepalive'], args['autoack'])

			wa.login(login, password)
			
		elif args['broadcast']:
			
			phones = args["broadcast"][0]
			message = args["broadcast"][1]
			
			wa = WhatsappEchoClient(phones, message, args['wait'])
			wa.login(login, password)

		elif args["requestcode"]:

			method = args["requestcode"]
			if method not in ("sms","voice"):
				print("coderequest accepts only sms or voice as a value")
			else:

				wc = WACodeRequestV2(countryCode, phoneNumber, identity, method)
					
				result = wc.send()
				print(resultToString(result))
				
		elif args["register"]:
			code = args["register"]
			code = "".join(code.split('-'))
			wr = WARegRequestV2(countryCode, phoneNumber, code, identity)
			
			
			result = wr.send()
			print(resultToString(result))
			
		elif args["exists"]:

			we = WAExistsRequestV2(countryCode, phoneNumber, identity)
			result = we.send()
			print(resultToString(result))

			if result["pw"] is not None:
				print("\n=========\nWARNING: %s%s's has changed by server to \"%s\", you must update your config file with the new password\n=========" %(countryCode, phoneNumber, result["pw"]))
	
		elif args["sync"]:

			contacts = args["sync"].split(',')
			wsync = WAContactsSyncRequest(login, password, contacts)
			
			print("Syncing %s contacts" % len(contacts))
			result = wsync.send()
			
			print(resultToString(result))

	elif args["generatepassword"]:
		print(Utilities.processIdentity(args["generatepassword"]));
	elif args["decodestring"]:
		print(Utilities.decodeString(map(int, "".join(args["decodestring"].split(' ')).split(','))))
	else:
		print("Error: config file is invalid")
