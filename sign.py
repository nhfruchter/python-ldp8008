#!/usr/bin/python
import sys
import time
from multiprocessing import Process, Value
import fontv
import ldp

class SignDisplayError(Exception): pass

class Sign(object):    
    """Class that represents a physical LED sign.
    
    >>> s = sign.Sign()
    >>> # You can scroll an arbitrarily long string.
    >>> s.scrollPut("1234567890abcdefgh  ")
    >>> s.scroll()
    >>> # Or a fixed-width string.
    >>> s.stop()
    >>> s.staticPut("Testing")
    >>> s.static()
    
    """
    
    # Display colors
    RED = 1
    GREEN = 2
    ORANGE = 3
    
    # Display color names
    COLORNAMES = {1: 'red', 2: 'green', 3: 'orange', 4: 'blank'}
    
    def __init__(self, width=80, height=8):
        self.WIDTH, self.HEIGHT = width, height
        self.buffer = [[0 for i in xrange(self.WIDTH)] for i in xrange(self.HEIGHT)]    
        
        self.isOn = False
        self.displayProcess = False
        self._continue = Value('b', 0)
        
        self.currentMessage = ""
        self.currentColor = 4
        
        ldp.init()
        
    def getColor(self):
        return self.COLORNAMES[self.currentColor]
        
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
        
        empty = [[0 for i in xrange(self.WIDTH)] for i in xrange(self.HEIGHT)]    
        
        if self.displayProcess:
            raise SignDisplayError("There is already a display loop running.")
        elif not hasattr(self, "dotArray") or not self.dotArray:
            raise SignDisplayError("Please put text on the sign using scrollPut.")
        else: 
            # Clear the buffer from `put` because the buffer is continually
            # updated during the scroll process.
            if interval == -1:
                self._continue = Value('b', 1) # run flag
                self.displayProcess = Process(target=self.scrollLoop) # create thread
                self.displayProcess.start() # start display        
    
    def static(self, interval=-1):        
        """Push the bitmap in `self.buffer` to the display for `interval` 
        seconds (`interval = -1` is forever). This spawns a separate thread 
        that will display for the specified number of seconds, or until 
        `self.stop` is called."""
        empty = [[0 for i in xrange(self.WIDTH)] for i in xrange(self.HEIGHT)]    
        if self.displayProcess:
            raise SignDisplayError("There is already a display loop running.")
        elif self.buffer == empty:
            # Do nothing, empty sign.
            pass
        else: 
            if interval == -1:
                self._continue = Value('b', 1) # run flag
                self.displayProcess = Process(target=self.staticLoop) # create thread
                self.displayProcess.start() # start display
                
    def stop(self):
        """Clear the buffer, display, and other associated state variables."""
        
        if not self.displayProcess:
            raise Exception("There is no display loop running.")
        else:
            self._continue.value = 0 # stop the loop
            self.displayProcess.join() # stop the thread
            self.displayProcess = False # remove the subprocess pointer
            self.clear() # clear the hardware buffer
            self.currentMessage = "" # clear the current message string
                
    ###### Write functions ######                   
    def drawText(self, text, color):
        """Push the string `text`, to be displayed in `color`, to the software
        bitmap buffer.  This can later be displayed by calling `self.display`."""
        
        # Initialize sign
        text = str(text).encode('ascii', 'ignore')
        self.clearbuffer()
        
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

        return dotArray                
        
    def staticPut(self, text, color=RED):
        """Draw the formatted text bitmap to buffer for a static display."""                            
        dotArray = self.drawText(text, color)
        
        # Width of raw message bitmap, so we can do some bounds checking
        totalWidth = len(dotArray[0])                
        
        if totalWidth > self.WIDTH:
            self.dotArray = dotArray    
            raise ValueError("Message larger than display. Maybe try scrolling instead?")
        
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
                
        self.currentMessage = text        
        self.currentColor = color
        
    def scrollPut(self, text, color=RED):
        """Generate the formatted text bitmap to buffer for a scrolling display.
        Drawing is handled by the display function here as it continually updates 
        for scrolling purposes."""                            
        
        # Place to hand off to display function
        self.dotArray = self.drawText(text, color)
        self.currentMessage = text        
        self.currentColor = color
        