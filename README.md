A quick rewrite of some code floating around out there for controlling an LDP-8008 LED matrix through a Raspberry PI. It serves as a wrapper around the `ldp` module by [Pete Goss](http://www.embeddedadventures.com/Tutorials/tutorials_detail/184). This provides a `Sign` class that you can use to control a sign.

# Setup
1. Connect the sign to your Raspberry Pi. A recommended pin setup is given in `ldp.py`; if you use something different, change the pin numbers in that file to match.
2. Import the module.
3. You're ready to go!

# Examples
Making the sign display something is a two step process. First, you have to write to the sign's buffer. Second, you have to tell it to display the current text.

    >>> s = sign.Sign()
    >>> # You can scroll an arbitrarily long string.
    >>> s.scrollPut("1234567890abcdefgh  ")
    >>> s.scroll()
    >>> # Or a fixed-width string.
    >>> s.stop()
    >>> s.staticPut("Testing")
    >>> s.static()

The sign also has three colors that you can use, but defaults to red.

    >>> s.staticPut("Hello", s.ORANGE)
	>>> s.stop()
	
Finally, you can display your own custom bitmaps on the sign, which should take the form of an 80x8 2D array.

    >>> s.buffer = [[1 for i in xrange(s.WIDTH)] for i in xrange(s.HEIGHT)] # Light it up!
	>>> s.static()
	>>> s.stop()
	
# Implementation note
Having a separate `stop()` function for the sign is necessary as the sign only seems to be driven when actively being `written` to. (There's no freeze function, so to speak.) Because of this, the buffer display function is run in a separate thread using a `while True` infinite loop. The `stop()` command just kills that thread and resets the sign's buffer. There's probably a better way, so feel free to mess around with the system.


	
