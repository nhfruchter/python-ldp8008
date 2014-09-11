#!/usr/bin/python
import sys
import time
from multiprocessing import Process, Value

import fontv
import ldp

class SignDisplayError(Exception): pass

class Sign(object):
    """Class that represents a physical LED sign."""
    
    # Display colors
    RED = 1
    GREEN = 2
    ORANGE = 3
    
    def __init__(self, width=80, height=8):
        self.WIDTH, self.HEIGHT = width, height
        self.buffer = [[0 for i in xrange(self.WIDTH)] for i in xrange(self.HEIGHT)]    
        
        self.isOn = False
        self.displayProcess = False
        self._continue = Value('b', 0)
        
        ldp.init()
        
    ###### Sign hardware functions: general ######
        
    def on(self): 
        """Turn display on."""
        self.isOn = True
        ldp.displayon()
        
    def off(self): 
        """Turn display off."""
        self.isOn = False
        ldp.displayoff()    
        
    def clear(self):
        """Zero out hardware buffer so that no LEDs will be on."""
        ldp.clear()
        
    ###### Local bitmap buffer management functions ######    
    
    def clearbuffer(self):
        """Zero out the buffer for this class."""
        self.buffer = [[0 for i in xrange(self.WIDTH)] for i in xrange(self.HEIGHT)]    

    def shiftbuffer(self):
        """function to shift left all the vaules of the matrix array 
        this allows us to put new data in the first column"""
    	for row in range(self.HEIGHT):
    		for col in range(self.WIDTH-1,0,-1):
    			self.buffer[row][col] = self.buffer[row][col-1]
                            
                
    ###### Display functions ######    
                
    def showbuffer(self):
        """function to read the matrix array and output the values to the display device"""    
        self.off()
        
        hscope, wscope = xrange(self.HEIGHT), xrange(self.WIDTH)
                
    	for row in range(self.HEIGHT):
    		for col in range(self.WIDTH):
    			ldp.colourshift(self.buffer[row][col])
    		ldp.showrow(row)
        
    def showbufferRev(self):
    	for row in reversed(range(self.HEIGHT)):
    		for col in reversed(range(self.WIDTH)):
    			ldp.colourshift(self.buffer[row][col])
    		ldp.showrow(row)
                    
    def staticLoop(self):
        """Main display loop (static). Usually run inside a thread; don't call this
        directly unless you're testing."""
        
        while self._continue.value == 1:
            self.showbuffer()
            
    def scrollLoop(self):   
        """Continually updates bitmap to scroll left to right. Usually run in a
        thread; don't call directly unless you're testing."""     
        
        while self._continue.value == 1:
            for col in range(len(self.dotArray[0])):
                for row in range(self.HEIGHT):
                    self.buffer[row][0] = (self.dotArray[row][col])
                self.showbufferRev()  # display  
                self.shiftbuffer() # lshift the buffer
            
    def scroll(self, interval=-1):        
        """Scroll the bitmap in `self.buffer` to the display for `interval` 
        seconds (`interval = -1` is forever). This spawns a separate thread 
        that will display for the specified number of seconds, or until 
        `self.stop` is called."""
        
        if self.displayProcess:
            raise SignDisplayError("There is already a display loop running.")
        else: 
            # Clear the buffer from `put` because the buffer is continually
            # updated during the scroll process.
            self.clearbuffer()
            if interval == -1:
                self._continue = Value('b', 1) # run flag
                self.displayProcess = Process(target=self.scrollLoop) # create thread
                self.displayProcess.start() # start display        
    
    def static(self, interval=-1):        
        """Push the bitmap in `self.buffer` to the display for `interval` 
        seconds (`interval = -1` is forever). This spawns a separate thread 
        that will display for the specified number of seconds, or until 
        `self.stop` is called."""
        
        if self.displayProcess:
            raise SignDisplayError("There is already a display loop running.")
        else: 
            if interval == -1:
                self._continue = Value('b', 1) # run flag
                self.displayProcess = Process(target=self.staticLoop) # create thread
                self.displayProcess.start() # start display
                
    def stop(self):
        if not self.displayProcess:
            raise Exception("There is no display loop running.")
        else:
            self._continue.value = 0 # stop the loop
            self.displayProcess.join() # stop the thread
            self.displayProcess = False # remove the subprocess pointer
            self.clear() # clear the hardware buffer
                
    ###### Write functions ######                   

    def put(self, text, color=RED, center=True):
        """Push the string `text`, to be displayed in `color`, to the software
        bitmap buffer.  This can later be displayed by calling `self.display`."""
        
        # Initialize sign
        text = str(text)
        
        # Get the ascii values to lookup bitmap letters in the font
        inputArray = [ord(char) for char in text]
        dotArray = [ [] for row in xrange(self.HEIGHT) ]
        
        # Build the bitmap that we want to display on the sign
        # by filling the array with the relevant color digits
        for row in range(self.HEIGHT):
            for asciiChr in inputArray:
                # Width of character (number of LEDs lit)
                width = fontv.array[asciiChr][0]
                chrBitmap = fontv.array[asciiChr][row+1]
                binary = '{0:{fill}{align}{width}{base}}'.format(chrBitmap, base='b', fill='0', align='>', width=width)

                # Populate the array
                for digit in range(width):
                    if binary[digit] == '0':
                        dotArray[row].append(0)
                    else:
                        dotArray[row].append(color)
        
        # Width of raw message bitmap, so we can do some bounds checking
        totalWidth = len(dotArray[0])                
        if totalWidth > self.WIDTH:
            raise SignDisplayError("Message larger than display.")
        else:
            # Needed for scrolling calculations.
            self.dotArray = dotArray    
        
        # Create offset to center message if we want
        offset = int((self.WIDTH - totalWidth) / 2)

        # Fill the matrix with spaces to center
        for col in range(offset):
        	for row in range(self.HEIGHT):
        		self.buffer[row][col] = 0
                                
        # Fill the display matrix with the bitmap
        for col in range(totalWidth):
        	for row in range(self.HEIGHT):
        		# copy the current dotarray column values to the first column in the matrix
        		self.buffer[row][offset+col] = (dotArray[row][col])