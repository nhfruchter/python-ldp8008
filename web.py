# TODO Fix error handling
# TODO Color chooser
# TODO Scroll if too long

from flask import Flask, render_template, request, Response, url_for
import sign as ledsign

# class DummySign(object):
#     """Good for testing when the actual sign doesn't exist."""
#     RED = 1
#     GREEN = 2
#     ORANGE = 3
#     COLORNAMES = {1: 'red', 2: 'green', 3: 'orange', 4: 'blank'}
#
#     def __init__(self):
#         self.currentMessage = ""
#         self.displayProcess = False
#         self.currentColor = 4
#
#     def getColor(self):
#         return self.COLORNAMES[self.currentColor]
#
#     def put(self, text, color=RED):
#         if len(text) > 13:
#             raise ledsign.SignDisplayError("Too big")
#         else:
#             self.currentMessage = text
#             self.currentColor = color
#             print "New message: {}".format(text)
#
#     def static(self):
#         print "Display on: static"
#         self.displayProcess = True
#
#     def scroll(self):
#         print "Display on: scroll"
#         self.displayProcess = True
#
#     def stop(self):
#         print "Display off"
#         self.displayProcess = False
#         self.currentMessage = ""
#
#     def clear(self):
#         print "Clearing"

app = Flask(__name__)
app.debug = True
app.config.update(
    {'sign': ledsign.Sign(),
    # 'sign': DummySign(),
    'updateLock': False,
    'lockErr': "Oops! Someone else is updating the sign."
    }
)

@app.route("/")
def home():
    msg = app.config['sign'].currentMessage
    return render_template("sign.html", msg=msg, color=app.config['sign'].getColor())

@app.route("/update", methods=["POST"])
def updateSign():
    msg = request.form.get('msg')
    color = int(request.form.get('color'))
    sign = app.config['sign']

    if msg and not app.config['updateLock']:
        app.config['updateLock'] = True # take lock so we don't get conflicts
        msg = msg.encode('ascii', 'ignore')
        
        # There is already a message up, so clear it first
        if sign.displayProcess: 
            sign.stop()

        # Try and update bitmap
        if request.form.get('static'):
            try:
                # Put bitmap to buffer
                sign.staticPut(msg, color)
                sign.static()
            except ValueError:
                # Too long, so we'll scroll it instead.
                msg += " "*3
                sign.scrollPut(msg, color)
                sign.scroll()
            finally:
                # Either way, we release the lock and update the page.
                app.config['updateLock'] = False # release lock
                return render_template("sign.html", msg=msg, color=app.config['sign'].getColor())

        # Scrolling is also an option
        elif request.form.get('scroll'):
            msg += " "*3
            sign.scrollPut(msg, color)
            sign.scroll()
            app.config['updateLock'] = False # release lock
            return render_template("sign.html", msg=msg, color=app.config['sign'].getColor())
        
    elif app.config['updateLock']:
        # Can't acquire lock
        return render_template("sign.html", err=app.config['lockErr'], msg=app.config['sign'].currentMessage, color=app.config['sign'].getColor())
        
@app.route("/clear")
def clear():
    sign = app.config['sign']
    if not app.config['updateLock']:
        app.config['updateLock'] = True
        
        if sign.displayProcess: 
            sign.stop()
        else:
            sign.clear()        
        app.config['updateLock'] = False
        return render_template("sign.html", err="Sign cleared.", msg=app.config['sign'].currentMessage, color=app.config['sign'].getColor())
    else:
        return render_template("sign.html", err=app.config['lockErr'], msg=app.config['sign'].currentMessage, color=app.config['sign'].getColor())    
        
if __name__ == '__main__':
    app.run(host='0.0.0.0')