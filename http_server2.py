import os
import time
import BaseHTTPServer
import zlib
import urlparse
from socket import gethostname

import session


PYTHON_EMBED=True
COMPRESSED_SUFFIX="-zlc"
nlc="\r\n"

##import StringIO
##import gzip
##def gZipIt(string):
##    out=StringIO.StringIO()
##    gzf=gzip.GzipFile(fileobj=out,mode="wb")
##    gzf.write(string)
##    gzf.close()
##    return out.getvalue()



class HTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        self.CareLessRequest()


    def do_POST(self):
        data=self.rfile.read(int(self.headers.get("Content-Length",0)))
        self.rfile.close()
        self.CareLessRequest(data)


    def do_HEAD(self):
        data=self.rfile.read(int(self.headers.get("Content-Length",0)))
        self.rfile.close()
        self.CareLessRequest(HEAD=True)


    def CareLessRequest(self,post_data="",HEAD=False):
        self.protocol_version="HTTP/1.1"
        self.server_version="JHTTPy/0.5.5"

        DATA=["",post_data]
        #Parse request and add GET data to the DATA variable
        split_path=self.path.split("?",1)
        if len(split_path)>1:
            DATA[0]=split_path[1]

        self.host=self.headers.get("Host","")
        accepted_encodings=map(lambda x:x.lower().strip(),self.headers.get("Accept-Encoding","").split(","))
        self.compression_accepted="deflate" in accepted_encodings or "*" in accepted_encodings

        try:
            self.cookies=dict(map(lambda x:x.split("="),self.headers.get("Cookie","").split(";")))
        except ValueError:
            self.cookies={}
        
        self.response_headers=["Content-Type: text/html","Connection: close"]
        self.session=None
        page=None

        #This is the file we're looking for relative to where the server starts looking for webpages
        request_file=split_path[0]
        #This is the absolute path to the file we're trying to access
        actual_path=self.server.root_directory+request_file

        #Authentication/deny/allow access based on the contents of disallow.txt
        if not self.server.AllowAccess(request_file):
            print "Attempted acces to %s by %s denied"%(self.path,self.client_address)
            self.send_error(401)
            self.wfile.close()
            return
        
        if os.path.exists(actual_path):
            #If the request exists and it's a file not a directory
            if not os.path.isdir(actual_path):
                #Content-Type defaults to text/html if the extention doesn't hav a map
                self.response_headers[0]="Content-Type: "+self.server.extention_type_map.get(request_file.split(".")[-1],"text/html")
                page=self.LoadPage(actual_path,DATA)
            #This is what we do if it's a directory and we know it exists
            else:
                #If there's no ending slash but we're trying to access a directory
                if not actual_path.endswith("/"):
                    self.send_response(303)
##                    logging.info("Redirecting to directory: http://"+host+request_file+"/")
                    self.send_header("Location","http://"+self.host+request_file+"/") #Send the redirect header
                    self.end_headers()
                    self.wfile.close()
                    return

                #If there is an ending slash we need to try to find an index file to serve
                for extension in self.server.file_extensions_resolution:
                    if os.path.exists(actual_path+self.server.default_page_name+extension):
                        self.response_headers[0]="Content-Type: "+self.server.extention_type_map.get(extension.lstrip("."),"text/html")
                        page=self.LoadPage(actual_path+self.server.default_page_name+extension,DATA)
        #Check to see if we're trying to access a file, but by the wrong extension
        else:
            actual_path=self.server.root_directory+request_file.split(".")[0]
            for extension in self.server.file_extensions_resolution:
                if os.path.exists(actual_path+extension):
                    self.send_response(303)
                    #Figure out what we're called and go there.
                    requested_file_name=request_file.split(".")[0]
##                    logging.info("Redirecting to: http://"+host+requested_file_name+extension)
                    self.send_header("Location", "http://"+self.host+requested_file_name+extension)
                    self.end_headers()
                    self.wfile.close()
                    return
        
        if page: #Make sure we did actually get a page loaded, just incase we didn't
            self.send_response(page[0])
            if page[0]==404:
                #Load the 404 page! We didn't find anything interesting to serve!
                page=self.LoadPage(self.server.root_directory+"/lost.html")
                if page[0]==404: #If we didn't find the "lost.html" file then send a pre-made python server one
                    self.send_error(404)
                    self.wfile.close()
                    return
                
            self.wfile.write(nlc.join(self.response_headers)+nlc)
            
            if page[1]:
                self.send_header("Content-Encoding","deflate")
            
            self.send_header("Content-Length",len(page[2]))
            self.end_headers()
            
        else:
            page=self.LoadPage(self.server.root_directory+"/lost.html")
            if page[0]==404: #If we didn't find the "lost.html" file then send a pre-made python server one
                self.send_error(404)
                self.wfile.close()
                return
            else:
                self.send_response(404)
                self.wfile.write(nlc.join(self.response_headers)+nlc)
                
                if page[1]:
                    self.send_header("Content-Encoding","deflate")
                
                self.send_header("Content-Length",len(page[2]))
                self.end_headers()
                

        if page and page[0]!=304 and not HEAD: #If this wasn't an http HEAD request send the page content
            self.wfile.write(page[2])
        self.wfile.close()


    def GetCached(self,path):
        if os.path.exists(path+COMPRESSED_SUFFIX):
            if os.stat(path).st_mtime>os.stat(path+COMPRESSED_SUFFIX).st_mtime:
                #If the file was updated since the cached compressed file was generated update cached file
                f=open(path,"r")
                page=zlib.compress(f.read(),self.server.compression_level)
                f.close()
                self.UpdateCached(path,page)
                return page
            else: 
                f=open(path+COMPRESSED_SUFFIX,"rb")
                return f.read()

        return False


    def UpdateCached(self,path,page):
        try:
            f=open(path+COMPRESSED_SUFFIX,"wb")
            f.write(page)
            f.close()
        except IOError:
            self.send_error(500)


    def LoadPage(self,path,DATA=[]):
        response_code=None #Default to internal server error response code
        page=self.Executable(path,DATA)
        sending_compressed=False
        if type(page) in (list, tuple):
            compress_exe_output=page[1]
            try:
                response_code=page[2]
            except IndexError:
                pass
            page=page[0]
        else:
            compress_exe_output=True
        
        if page==None: #Wasn't a cgi (or an "executable" thingy of some sort)
            self.response_headers.append("Last-Modified: %s"%time.strftime("%a, %d %b %Y %H:%M:%S %Z",time.localtime(os.stat(path).st_mtime)))
            self.response_headers.append("Expires: %s"%time.strftime("%a, %d %b %Y %H:%M:%S %Z",time.localtime(time.time()+30*86400))) #Expires in 1 month
            if self.server.compressed_response and self.compression_accepted:
                page=self.GetCached(path)
                sending_compressed=bool(page)
            if not page: #If we still have no page data... (Because we're not doing cached compression or there wasn't a cached version yet)
                f=open(path,"r")
                page=f.read()
                f.close()
                if self.server.compressed_response and self.compression_accepted:
                    for extension in self.server.no_compress_extensions:
                        if path.lower().endswith(extension): #This means that we don't need to compress the file so just send it normally
                            break
                    else: #If we don't break (aka this file isn't in the "exclude from compression" list) then compress the page
                        page=zlib.compress(page,self.server.compression_level)
                        self.UpdateCached(path,page)
                        sending_compressed=True
                        
        elif self.server.compressed_response and compress_exe_output and self.compression_accepted:
            page=zlib.compress(page,self.server.compression_level)
            sending_compressed=True

        if page!=None and not response_code:
            response_code=200

        modified_since_header=self.headers.get("If-Modified-Since",None)
        if modified_since_header and int(os.stat(path).st_mtime)<=int(time.mktime(time.strptime(modified_since_header,"%a, %d %b %Y %H:%M:%S %Z"))):
            response_code=304

        return response_code,sending_compressed,page


    def Executable(self,path,DATA):
        if PYTHON_EMBED and path.endswith(".pye"):# in (".py",".pyc",".pyw"):
            fields=dict(urlparse.parse_qsl(DATA[0]))
            fields.update(dict(urlparse.parse_qsl(DATA[1])))
            
            script_globals=self.server.loaded_python_scripts.get(path,({},0))
            if script_globals and os.stat(path).st_mtime<=script_globals[1]:
                #If there was a preloaded version and the actual version isn't newer than the loaded version...
                return script_globals[0]["main"](self,path,fields)
            else:
                #Load the script into memory 'cause we either need a newer version or it hasn't bee loaded yet
                self.server.loaded_python_scripts[path]=({},os.stat(path).st_mtime) #Add a value which says what time we loaded this script
                execfile(path,self.server.loaded_python_scripts[path][0])
                return self.server.loaded_python_scripts[path][0]["main"](self,path,fields)

        for extension in self.server.executable_extensions:
            if path.endswith(extension):
                f=os.popen(path+" \"%s\""%"&".join(DATA))
                page=f.read()
                f.close()
                return page

        #For some reason this stuff doesn't work... :/ variable scope something 'r other?
##        print "Session: "
##        print self.session
##        if self.session:
##            print "Ending session"
##            self.session.end()
            
        return None


    def SetCookie(self,name,value,expires="",path="",domain=""):
        hv="Set-Cookie: %s=%s;"%(name,value)\
        +(domain and "Domain=")+domain+(domain and ";")\
        +(path and "Path=")+path+(path and ";")\
        +(expires and "Expires=")+expires+(expires and ";")
        self.response_headers.append(hv)


    def StartSession(self):
        self.session=self.server.session_manager.getSession(self,self.cookies)
        return self.session



class Server(BaseHTTPServer.HTTPServer):
    def __init__(self,server_address,request_handler_class,compressed=True):
        BaseHTTPServer.HTTPServer.__init__(self,server_address,request_handler_class)
        self.root_directory="www"
        self.default_page_name="index"
        self.executable_extensions=[".py",".php",".cgi",".pyc",".pyw"]
        self.file_extensions_resolution=[".html",".htm"]+self.executable_extensions+[".pye"]
        self.extention_type_map={"css":"text/css","html":"text/html","txt":"text/plain","js":"text/javascript",
                                 "mp3":"audio/mpeg","png":"image/png","jpg":"image/jpeg","zip":"application/zip"}

        self.no_compress_extensions=(".png",".jpg",".mp3",".zip",".doc",".odt")
        self.compressed_response=compressed
        self.compression_level=7
        self.compression_cache_enable=True

        self.loaded_python_scripts={}

        self.session_manager=session.SessionManager("pyserver_session_data.db")

##        self.restrict_access=open("disallow.txt").read().split("\n")
        
        try:
            f=open("ignore.txt")
            data=f.read().strip().split("\n")
            f.close()
        except IOError:
            data=[]
        self.no_log_files=data


    def AllowAccess(self,location):
        restricted=open("disallow.txt").read().strip().split("\n")
        for path in restricted:
            if path.lstrip("/").endswith("/") and location.lstrip("/").startswith(path):
                return False
            elif location==path:
                return False

        return True


        
##import multiprocessing       
import sys

if "-noep" in sys.argv:
    print "Will NOT use embedded Python..."
    PYTHON_EMBED=False
    
print "Initializings server..."
#The port=... statement makes the server use port 8000 when I'm testing on my mac
port=(gethostname()=="Jamess-MacBook-Pro.local" and 8000) or 80
http=Server(("",port),HTTPHandler)

if "-noc" in sys.argv:
    print "Disabling compression..."
    http.compressed_response=False

if "-drop-tables" in sys.argv:
    print "Dropping session tables..."
    http.session_manager.dropTables()
    http.session_manager.makeTables()

print "Starting server..."   
http.serve_forever()
