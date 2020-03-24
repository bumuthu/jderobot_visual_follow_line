#!/usr/bin/python
#-*- coding: utf-8 -*-
import threading
import time
from datetime import datetime

import math
import cv2
import numpy as np
import matplotlib.pyplot as plt

time_cycle = 80

class MyAlgorithm(threading.Thread):

    def __init__(self, camera, motors):
        self.camera = camera
        self.motors = motors
        self.threshold_image = np.zeros((640,360,3), np.uint8)
        self.color_image = np.zeros((640,360,3), np.uint8)
        self.stop_event = threading.Event()
        self.kill_event = threading.Event()
        self.lock = threading.Lock()
        self.threshold_image_lock = threading.Lock()
        self.color_image_lock = threading.Lock()
        self.error = 0
        self.last_error = 0
        threading.Thread.__init__(self, args=self.stop_event)
    
    def getImage(self):
        self.lock.acquire()
        img = self.camera.getImage().data
        self.lock.release()
        return img

    def set_color_image (self, image):
        img  = np.copy(image)
        if len(img.shape) == 2:
          img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        self.color_image_lock.acquire()
        self.color_image = img
        self.color_image_lock.release()
        
    def get_color_image (self):
        self.color_image_lock.acquire()
        img = np.copy(self.color_image)
        self.color_image_lock.release()
        return img
        
    def set_threshold_image (self, image):
        img = np.copy(image)
        if len(img.shape) == 2:
          img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        self.threshold_image_lock.acquire()
        self.threshold_image = img
        self.threshold_image_lock.release()
        
    def get_threshold_image (self):
        self.threshold_image_lock.acquire()
        img  = np.copy(self.threshold_image)
        self.threshold_image_lock.release()
        return img

    def run (self):

        while (not self.kill_event.is_set()):
            start_time = datetime.now()
            if not self.stop_event.is_set():
                self.algorithm()
            finish_Time = datetime.now()
            dt = finish_Time - start_time
            ms = (dt.days * 24 * 60 * 60 + dt.seconds) * 1000 + dt.microseconds / 1000.0
            #print (ms)
            if (ms < time_cycle):
                time.sleep((time_cycle - ms) / 1000.0)

    def stop (self):
        self.stop_event.set()

    def play (self):
        if self.is_alive():
            self.stop_event.clear()
        else:
            self.start()

    def kill (self):
        self.kill_event.set()

    def algorithm(self):
        #GETTING THE IMAGES
        image_in = self.getImage()        
    
        #image_in = cv2.cvtColor(image_in, cv2.COLOR_BGR2RGB)        
      
        lower_range = np.array([20,0,0])
        upper_range = np.array([100,30,10])
                
        mask = cv2.inRange(image_in, lower_range, upper_range)
                
        center_x = mask.shape[1] / 2
        
        ret, thresh = cv2.threshold(mask, 127, 255, 0)
        im2, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
        kp = 5 * 0.001
        kd = 12 * 0.001 
        
        if len(contours) > 0:
            c = max(contours, key=cv2.contourArea)
            M = cv2.moments(c)
            try: 
                cx = int(M['m10']/M['m00'])
                cy = int(M['m01']/M['m00'])
            except:
                cx = center_x
                cy = 0
                
            cv2.line(image_in,(cx,0),(cx,720),(255,0,0),1)
            cv2.line(image_in,(0,cy),(1280,cy),(255,0,0),1)
            cv2.drawContours(image_in, contours, -1, (0,255,0), 1)
            
            mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)
            cv2.drawContours(mask, contours, -1, (255,0,0), 2)
            
            self.error = center_x - cx
            diff = self.error - self.last_error
            self.last_error = self.error
            
            angular = kp*self.error + kd*diff
            
            print self.error
        
        else:
            angular = 0   
        
                
        
             
       
        print "Runing"

        #EXAMPLE OF HOW TO SEND INFORMATION TO THE ROBOT ACTUATORS
        self.motors.sendV(5)
        self.motors.sendW(angular)

        #SHOW THE FILTERED IMAGE ON THE GUI
        self.set_threshold_image(mask)
