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

import os, time, urllib
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.insert(0,parentdir)
import datetime, sys

if sys.version_info >= (3, 0):
	raw_input = input

from Yowsup.connectionmanager import YowsupConnectionManager

class WhatsappListenerClient:	

	def __init__(self, keepAlive = False, sendReceipts = False):
		self.messages = ''
		self.hold_call = True
		self.connect_Status = ''
		self.sendReceipts = sendReceipts
		
		connectionManager = YowsupConnectionManager()
		connectionManager.setAutoPong(True)

		self.signalsInterface = connectionManager.getSignalsInterface()
		self.methodsInterface = connectionManager.getMethodsInterface()
		
		self.signalsInterface.registerListener("message_received", self.onMessageReceived)
		self.signalsInterface.registerListener("auth_success", self.onAuthSuccess)
		self.signalsInterface.registerListener("auth_fail", self.onAuthFailed)
		self.signalsInterface.registerListener("disconnected", self.onDisconnected)
		self.signalsInterface.registerListener("presence_updated", self.onPresenceUpdated)
		self.signalsInterface.registerListener("image_received", self.onImageReceived)
		self.signalsInterface.registerListener("videoimage_received", self.onVideoReceived)
		self.signalsInterface.registerListener("ping", self.onPing)
		
		self.cm = connectionManager

		self.commandMappings = {"lastseen":lambda: self.methodsInterface.call("presence_request", ( self.jid,)),
				"available": lambda: self.methodsInterface.call("presence_sendAvailable"),
				"unavailable": lambda: self.methodsInterface.call("presence_sendUnavailable")
				 }
	
	def disconnect(self, reason):
		self.cm.readerThread.sendDisconnected(reason)
		#print("Sent disconnnected")

	def getMessages(self):
		return self.messages

	def onPing(self, pingId):
		if self.connect_Status == "SUCCESS":
			self.methodsInterface.call("pong", (pingId,))

	def login(self, username, password):
		self.username = username
		self.methodsInterface.call("auth_login", (username, password))

		while self.hold_call:
			i=0

		return self.connect_Status

	def runCommand(self, command):
		if command[0] == "/":
			command = command[1:].split(' ')
			try:
				self.commandMappings[command[0]]()
				return 1
			except KeyError:
				return 0
		
		return 0

	def onImageReceived(self, messageId, jid, preview, url, size, receiptRequested, isBroadCast):
		messageContent = unicode("[ image: "+url+" , preview: "+preview+"]", "utf-8")
		messageContent = urllib.quote(messageContent)
		self.onMessageReceived(messageId, jid, messageContent, long(time.time()), receiptRequested, None, False)

	def onVideoReceived(self, messageId, jid, preview, url, size, receiptRequested, isBroadCast):
		messageContent = unicode("[ image: "+url+" , preview: "+preview+"]", "utf-8")
		messageContent = urllib.quote(messageContent)
		self.onMessageReceived(messageId, jid, messageContent, long(time.time()), receiptRequested, None, False)

	def onAuthSuccess(self, username):
		self.connect_Status = "SUCCESS"
		self.methodsInterface.call("ready")
		self.hold_call = False
		self.runCommand("/available");
		#self.runCommand("/lastseen");
		#print("Authed %s" % username)		

	def onPresenceUpdated(self, jid, lastSeen):
		formattedDate = datetime.datetime.fromtimestamp(long(time.time()) - lastSeen).strftime('%d-%m-%Y %H:%M')
		self.onMessageReceived(0, jid, "Last Seen On: %s"%formattedDate, long(time.time()), False, None, False)

	def onAuthFailed(self, username, err):
		self.connect_Status = "FAIL"
		self.hold_call = False		
		#print("Auth Failed!")

	def onDisconnected(self, reason):
		self.connect_Status = "FAIL"
		self.hold_call = False
		#print("Disconnected because %s" %reason)

	def onMessageReceived(self, messageId, jid, messageContent, timestamp, wantsReceipt, pushName, isBroadCast):
		formattedDate = datetime.datetime.fromtimestamp(timestamp).strftime('%d-%m-%Y %H:%M')
		messageContent = messageContent.replace('\n', '%0A')
		self.messages = self.messages + jid + "," + formattedDate + "," + messageContent + "\n"

		if wantsReceipt and self.sendReceipts:
			self.methodsInterface.call("message_ack", (jid, messageId))
	