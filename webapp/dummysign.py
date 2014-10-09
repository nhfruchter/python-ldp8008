class Sign(object):
    """Good for testing when the actual sign doesn't exist."""
    RED = 1
    GREEN = 2
    ORANGE = 3
    COLORNAMES = {1: 'red', 2: 'green', 3: 'orange', 4: 'blank'}

    def __init__(self):
        self.currentMessage = ""
        self.displayProcess = False
        self.currentColor = 4

    def getColor(self):
        return self.COLORNAMES[self.currentColor]

    def put(self, text, color=RED):
        if len(text) > 13:
            raise ledsign.SignDisplayError("Too big")
        else:
            self.currentMessage = text
            self.currentColor = color
            print "New message: {}".format(text)

    def static(self):
        print "Display on: static"
        self.displayProcess = True

    def scroll(self):
        print "Display on: scroll"
        self.displayProcess = True

    def stop(self):
        print "Display off"
        self.displayProcess = False
        self.currentMessage = ""

    def clear(self):
        print "Clearing"
