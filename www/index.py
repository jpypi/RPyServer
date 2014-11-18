#!/usr/bin/python
import cgi
import time

def AddMessage(message):
	f=open("messages.txt","a")
	f.write(time.asctime()+": "+message+"\n")
	f.close()

def GetMessages():
	try:
		f=open("messages.txt")
		messages=f.read().rstrip("\n").split("\n")
		messages.reverse()
		f.close()
		return messages
	except IOError: #No file called "messages.txt"
		return ""
	


fields=cgi.FieldStorage()

message=fields.getvalue("message",None)
if message:
	AddMessage(message)

messages="<p>"+("</p><p>".join(GetMessages()))+"</p>"

print """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
	<head>
	    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
		<title>Home</title>
        <link rel="stylesheet" type="text/css" href="/css/main-style.css"/>
		<style type="text/css">
			h1 {
                background: lightgrey;
                color: black;
                text-align: center;
                text-decoration: underline;
                font-size: 18pt;
                
            }
            p {
            	margin: 5px auto;
            }
		</style>
		<!--<script type="text/javascript" src="//ajax.googleapis.com/ajax/libs/jquery/1.8.0/jquery.min.js"></script>-->
		<script type="text/javascript" src="/js/jquery.min-1.8.0.js"></script>
	</head>
	<body>
        <div id="wrapper">
            <h1>This is James' self-hosted website</h1>
            <h2>Hello World! (Literally! :D)</h2>
            <div id="nav">
                <a href="hello.html">The hello page</a>
                <a href="/chat/">Chat</a>
                <a href="login.pye">Login</a>
               <div id="time">%s</div>
            </div>
            <form method="post" action="index.py">
            	<input type="text" name="message"/>
            	<input type="submit" value="Submit"/>
            </form>
            <div id="message">
            %s
            </div>
            
            <script type="text/javascript">/*
            	function UpdateTime(){
					$.get("/time-clock.py",{},function(results){
						$("#time").html(results);
					});
					time_update_loop_timer=window.setTimeout(UpdateTime,4000);
            	}
            	time_update_loop_timer=window.setTimeout(UpdateTime,4000);*/
            </script>
        </div>
	</body>
</html>"""%(time.asctime(),messages)
