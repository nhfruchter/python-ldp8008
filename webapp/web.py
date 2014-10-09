from flask import Flask, render_template, request, Response, url_for
from .. import sign as ledsign
# or: import dummysign as ledsign

app = Flask(__name__)
app.debug = True
app.config.update(
    {'sign': ledsign.Sign(),
    'updateLock': False,
    'lockErr': "Oops! Someone else is updating the sign."
    }
)

@app.route("/")
def home():
    msg = app.config['sign'].currentMessage
    return render_template("sign.html", msg=msg)

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
                return render_template("sign.html", msg=msg)

        # Scrolling is also an option
        elif request.form.get('scroll'):
            msg += " "*3
            sign.scrollPut(msg, color)
            sign.scroll()
            app.config['updateLock'] = False # release lock
            return render_template("sign.html", msg=msg)
        
    elif app.config['updateLock']:
        # Can't acquire lock
        return render_template("sign.html", err=app.config['lockErr'])
        
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
        return render_template("sign.html", err="Sign cleared.")
    else:
        return render_template("sign.html", err=app.config['lockErr'])
        

        
