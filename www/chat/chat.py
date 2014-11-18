#!/usr/bin/python

import cgi
import json
import time
from os import path as os_path
from os import sep as os_sep
from sys import argv as sys_argv

def Wrap(value,entity="p"):
	return "<"+entity+">"+value+"</"+entity+">"


fields=cgi.FieldStorage()
send_output=True

get=fields.getvalue("get")
put=fields.getvalue("put")
presence=fields.getvalue("presence","")

data={"lct":0,"messages":[],"ct":0,"present":[]} #lct stands for last chat time; ct stands for count

current_directory=os_path.split(sys_argv[0])[0]+os_sep
chat_file=current_directory+"chat_messages.txt"

users=[]
user_presence_delay=10
try:
	f=open(current_directory+"online_users.txt")
	try:
		users=json.load(f)
		for i,user in enumerate(users):
			if time.time()-user[0]>user_presence_delay:
				users.pop(i) #Remove users that have not been active for 5 seconds
				
	except ValueError: #We couldn't load the list of users online
		pass
except IOError:
	pass
try:
	f.close()
except NameError:
	pass #File wasn't opened :P


user_present_request=cgi.escape(presence.strip())
for user in users:
	if user[1]==user_present_request:
		break
else: #This works because if we break we don't enter this
	users.append((time.time(),user_present_request))

f=open(current_directory+"online_users.txt","w")
json.dump(users,f)
f.close()

	
if put:
	f=open(chat_file,"a")
	# Use <> as separators because user input is sanitized for those
	# The time thing is because we need to adjust how much we adjust time.time() to
	# be UTC time from our current timezone, because time.time() is more accurate than
	# time.gmtime() and the timezone offset changes depending on daylight savings time
	#+(time.daylight and time.altzone or time.timezone)
	f.write("%.6f<>%s<>%s\n"%(time.time(),cgi.escape(presence.strip()),cgi.escape(put.strip())))
	f.close()

if get!=None:
	try:
		get=float(get)
		try:
			f=open(chat_file,"r")
			messages=f.read().strip().split("\n")
			f.close()
			
			send=[]
			lct=0
			
			for message in messages:
				msg=message.split("<>",2)
				if float(msg[0])>get:
					send.append(msg)
					lct=max(float(msg[0]),lct)
						
			data["lct"]=lct
			data["ct"]=len(send)
			data["messages"]=send

		except IOError:
			pass
		users.sort(key=lambda x:x[1])
		data["present"]=users
			
	except ValueError:
		get=None
		send_output=False		
	
	
if send_output: #So we can not send anything if people are trying to hack my server! :/
	print json.dumps(data)