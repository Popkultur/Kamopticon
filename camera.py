# camera.py

import base64
import urllib.request
from urllib.parse import urlparse
from requests.auth import HTTPBasicAuth
import requests
import cv2
import numpy as np
import time
from slugify import slugify

class IpCamera(object):
    
    def __init__(self, url, vsnum, recordpath):
        self.vsnum = vsnum
        self.recordpath = recordpath
        self.bytes=bytes()
        self.url = url
        self.u = urlparse(self.url)       
        if self.u.path[-4:] == '.jpg':
            stream = True 
        else:
            stream = True 
        self.status = 0
        self.tf = cv2.getTickFrequency()
        self.t0 = cv2.getTickCount()
        self.t1 = cv2.getTickCount()
        # self.t = []
        # self.avg = 0
        # self.avgFirst = 0
        self.firstFrame = True
        self.framerate = 30
        self.frameswritten = 0
        self.snapswritten = 0
        self.lastimg = False
        self.video = False
        self.camrec = False
        self.camsnap = False
        self.camsnapsingle = False
        self.camclose = False
           
        try:
            self.r = requests.get(self.url, auth=(self.u.username, self.u.password), stream=stream, timeout=6, verify=False)  
            self.r.raise_for_status()
        except requests.exceptions.RequestException as err:
            self.status = err
            pass

    def get_frame(self):
        if self.u.path[-4:] == '.jpg':
            try:
                self.r = requests.get(self.url, auth=(self.u.username, self.u.password), stream=True, timeout=6, verify=False)  
                self.r.raise_for_status()
            except requests.exceptions.RequestException as err:
                self.status = err
                pass

                        
        # Calculate average framerate
        # self.t.append(cv2.getTickCount())
        # if (not self.firstFrame):
        #     if (self.avgFirst == 0):
        #         self.avg = (self.t[1] - self.t[0]) / self.tf
        #         self.avgFirst = self.avg
        #     else:
        #         diff = self.t[len(self.t)-2] - self.t[len(self.t)-1]
        #         a = 0
        #         for i in range(1, len(self.t)):
        #             a += self.t[i] - self.t[i-1]
        #         self.avg = a / self.tf / (len(self.t))
        #         if 30 < len(self.t):
        #             x = self.t[len(self.t)-1]
        #             self.t = []
        #             self.t.append(x)
        #             print(1/self.avg)
        #             self.framerateest = 1/self.avg
        # self.firstFrame = False  
        # self.t.append(cv2.getTickCount())
        
        while self.status==0:
            if self.camclose==True: 
                break
            try:
                x = self.r.raw.read(1024)
                if x == b'': raise
            except:
                self.status=1
                break
            self.bytes += x
            a = self.bytes.find(b'\xff\xd8')
            b = self.bytes.find(b'\xff\xd9')
            if a!=-1 and b!=-1:
                jpg = self.bytes[a:b+2]
                self.bytes = self.bytes[b+2:]
                self.lastimg = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8),cv2.IMREAD_COLOR)

                # write to disk
                self.t1 = cv2.getTickCount()
                if (type(self.lastimg).__module__ == np.__name__):
                    timediff = self.t1 - self.t0
                    if ((timediff / self.tf) > (1/self.framerate) and self.camrec == True):
                        for i in range(0, round(timediff / self.tf * self.framerate)):
                            # self.frameswritten += 1
                            if not self.video: 
                                timest = str(int(round(time.time() * 1000)))
                                height, width, channels = self.lastimg.shape
                                self.video = cv2.VideoWriter(self.recordpath+'/'+slugify(self.u.netloc)+'-'+timest+'.mkv', cv2.VideoWriter_fourcc('X', 'V', 'I', 'D'), self.framerate, (width, height));
                            else:
                                self.video.write(self.lastimg)
                    if ((self.camrec == False) and (self.video != False)):
                        self.video.release()
                        self.video = False
                    if self.camsnapsingle == True:
                        timest = str(int(round(time.time() * 1000)))
                        cv2.imwrite(self.recordpath+'/'+slugify(self.u.netloc)+'-'+timest+'.jpg',self.lastimg,[int(cv2.IMWRITE_JPEG_QUALITY), 100])
                        self.camsnapsingle = False
                    if self.camsnap == True:
                        timest = str(int(round(time.time() * 1000)))
                        cv2.imwrite(self.recordpath+'/'+slugify(self.u.netloc)+'-'+timest+'.jpg',self.lastimg,[int(cv2.IMWRITE_JPEG_QUALITY), 100])
                    self.t0 = self.t1

                return jpg       
  
  
  
class VideoCamera(object):
    
    def __init__(self):
        self.video = cv2.VideoCapture(0)
        # self.video = cv2.VideoCapture('video.mp4')
    
    def __del__(self):
        self.video.release()
    
    def get_frame(self):
        success, image = self.video.read()
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()



class WebCamera(object):

    def __init__(self, camera=0):
        self.cam = cv2.VideoCapture(camera)
        if not self.cam:
            raise Exception("Camera not accessible")

        self.shape = self.get_frame().shape

    def get_frame(self):
        _, frame = self.cam.read()
        return frame
