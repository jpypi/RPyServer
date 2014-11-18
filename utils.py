import time
def timeFuture(seconds):
    return time.strftime("%a, %d %b %Y %H:%M:%S GMT",time.gmtime(time.time()+seconds))
