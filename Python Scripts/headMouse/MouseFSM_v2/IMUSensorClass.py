#!/usr/bin/python
import serial
import yaml
import os
import time
import sys
from serial.tools import list_ports
import HelperClasses
import acd_file_io_lib as io
import math


# ======================= IMUSensorClass ======================= 
class IMUSensorClass:

  # establish connection
  def __init__(self, params, baudrate = 57600, portName = '/dev/ttyUSB0'):

    # try to connect to the provided portname
    self.ser = io.connectToAvailablePort(baudrate=baudrate, portName=portName, debug=True)

    # assign params
    self.params = params
    


  # get new IMU data
  def getData(self):
    while 1:
      try:
        raw_data = self.ser.readline()
        raw_data = raw_data.rstrip().rsplit(',')

        self.currentYpr = YPRDataClass(-1*float(raw_data[0]), -1*float(raw_data[1]), -1*float(raw_data[2]))
        #self.clickInput = raw_data[12]
        self.clickInput = 0
        return

      except:
        print raw_data
        print "Error getting data. Trying again."
        pass


  # update neutral position
  def updateNeutralYpr(self):
    print "Please hold still for a couple of seconds while the system saves neutral position"

    io.clearSerialBuffer(self.ser)
    self.getData()
    self.neutralYpr = YPRDataClass(self.currentYpr.yaw, self.currentYpr.pitch, self.currentYpr.roll)

    print "Updated Neutral YPR values to "
    self.neutralYpr.prettyPrint()
    
    # initialize optimizedNeutralYpr 
    self.optimizedNeutralYpr = YPRDataClass(self.neutralYpr.yaw, self.neutralYpr.pitch, self.neutralYpr.roll)
    self.cursorDisp = HelperClasses.CursorClass(0.0, 0.0)


  # optimize neutral position
  def optimizeNeutralYpr(self):
    if self.params['mode'] == 'joystick':
      self.optimizedNeutralYpr = YPRDataClass(self.neutralYpr.yaw, self.neutralYpr.pitch, self.neutralYpr.roll)

    elif self.params['mode'] == 'dynamic_neutral_log':
      yaw_disp = (self.optimizedNeutralYpr.yaw - self.currentYpr.yaw) * self.params['gamma']
      pitch_disp = (self.optimizedNeutralYpr.pitch - self.currentYpr.pitch) * self.params['gamma']
     
      x_sign = 1
      y_sign = 1
      if yaw_disp < 0: x_sign = -1
      if pitch_disp < 0: y_sign = -1

      yaw_dip   = x_sign * math.log(abs(yaw_disp   + 1), 10)
      pitch_dip = y_sign * math.log(abs(pitch_disp + 1), 10)
    
      print "*** *** *** ***"
      print yaw_disp
      print pitch_disp

      self.optimizedNeutralYpr.yaw   = self.optimizedNeutralYpr.yaw   - yaw_disp
      self.optimizedNeutralYpr.pitch = self.optimizedNeutralYpr.pitch - pitch_disp


    elif self.params['mode'] == 'dynamic_neutral_basic':
      yaw_disp = self.optimizedNeutralYpr.yaw - self.currentYpr.yaw
      pitch_disp = self.optimizedNeutralYpr.pitch - self.currentYpr.pitch

      print "*** *** *** ***"
      print yaw_disp
      print pitch_disp

      self.optimizedNeutralYpr.yaw   = self.optimizedNeutralYpr.yaw   - self.params['gamma'] * yaw_disp
      self.optimizedNeutralYpr.pitch = self.optimizedNeutralYpr.pitch - self.params['gamma'] * pitch_disp

    else:
      print "mode not chosen correctly"

    #self.optimizedNeutralYpr.yaw   = self.optimizedNeutralYpr.yaw   - self.params['gamma'] * self.cursorDisp.x
    #self.optimizedNeutralYpr.pitch = self.optimizedNeutralYpr.pitch - self.params['gamma'] * self.cursorDisp.y
    return
  


  def calculateCursorDisplacement(self):

    yaw_disp = self.optimizedNeutralYpr.yaw - self.currentYpr.yaw
    pitch_disp = self.optimizedNeutralYpr.pitch - self.currentYpr.pitch
    roll_disp = self.optimizedNeutralYpr.roll - self.currentYpr.roll
    
    #print "*** *** *** ***"
    #print yaw_disp
    #print pitch_disp
    #self.neutralYpr.prettyPrint()
    #self.currentYpr.prettyPrint()
    #self.optimizedNeutralYpr.prettyPrint()
    #print "*** *** *** ***"

    x_sign = 1
    y_sign = 1
    if yaw_disp < 0: x_sign = -1
    if pitch_disp < 0: y_sign = -1
    
    # linear function
    #x_disp = yaw_disp
    #y_disp = pitch_disp

    # x^3 function
    x_disp = (yaw_disp   ** 3 + yaw_disp) * self.params['alpha']
    y_disp = (pitch_disp ** 3 + pitch_disp) * self.params['alpha']

    # quadratic function
    #x_disp = x_sign * (yaw_disp   ** 2) * self.params['alpha']
    #y_disp = y_sign * (pitch_disp ** 2) * self.params['alpha']

    # account for neutral zone
    if abs(x_disp) < self.params['neutralZone']:
      x_disp = 0.0
    else:
      x_disp = x_sign * (abs(x_disp) - self.params['neutralZone'])

    if abs(y_disp) < self.params['neutralZone']:
      y_disp = 0.0
    else:
      y_disp = y_sign * (abs(y_disp) - self.params['neutralZone'])

    self.cursorDisp = HelperClasses.CursorClass(x_disp, y_disp)
    return



  def printData(self):
    self.currentYpr.prettyPrint()



# ======================= IMUDataClass ======================= 
class YPRDataClass:

  def __init__(self, yaw, pitch, roll):
    self.yaw = yaw
    self.pitch = pitch
    self.roll = roll

  def prettyPrint(self):
    print "ypr: " + str(self.yaw) + ", " + str(self.pitch) + ", " + str(self.roll)

