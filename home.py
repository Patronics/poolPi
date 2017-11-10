#!/usr/bin/python
from flask import Flask, render_template, make_response
import datetime, random, time
from threading import Timer, Thread
import RPi.GPIO as GPIO
import serial
import logging, chromalog, re
import random
from serial import SerialException
chromalog.basicConfig(level=logging.DEBUG)     #For colored debug terminal #change from .INFO to .DEBUG for more detail
logger = logging.getLogger()
app = Flask(__name__)

ser=serial.Serial('/dev/serial0',4800, timeout=5)

#Setup GPIO
GPIO.setwarnings(False)   #remove for debugging
GPIO.setmode(GPIO.BCM)
GPIO.setup(23,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(24,GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(27,GPIO.OUT, initial=GPIO.HIGH)  #Relay  default:off   (active low)

#setup serial


	

def update_thread():
	logger.debug( "update thread active")
	line="Default"
	try:
		ser.flushInput()
		time.sleep(0.6)
		line=ser.readline()
	except UnicodeDecodeError:  #never seems to trigger, but supresses warning
		logger.warning("Invalid Unicode Characters recived") 
	except SerialException:
		logger.warning("Serial Exception raised:")
	except KeyboardInterrupt:
		logger.info("Keyboard Exception caught by Serial Thread")
		sys.exit()
	#try:
	line=re.sub(r'[^\x00-\x7f]',r'', line)    #uncomment to try to filter out invalid unicode characters
	logger.debug(line)
	#except UnicodeDecodeError:
	#	print line
	#except Exception:
	#	print ("unexpected exception")
	#linedata = line.split()
	#print linedata
	#if (linedata[2]=="TouchValue:"):
	if "TouchValue: " in line:
		linenum=line.split("TouchValue: ",1)[1]
		try:
			global touchval
			touchval = int(linenum)
			logger.info( "valid number recived: "+str(touchval))
		except ValueError:
			logger.warning( "invalid number: "+linenum)
	else:
		logger.warning ("invalid string recived")
	t=Timer(15.0,update_thread)
	t.start()
def test_callback(channel):                  #inverted PICAXE serial input, no longer needed
	#GPIO.output(24, not GPIO.input(23))
	#print "callback activated"
	pass    #todo: remove function entirely, remove call of it	



if __name__ == "__main__":
#initializing global variables
	global count
	count = 0
	global touchval
	touchval=-1
	global pumpstate
	pumpstate='off (default)'
	global cycleid
	cycleid=0

def timeoff(*mycycleid):
	global touchval
	global secson
	global secsoff
	global pumpstate
	global cycleid
		
	if (cycleid != mycycleid[0]):
		logger.warning("cycle id changed, currently " + str(cycleid) + "; old cycle " + str(mycycleid[0]) + " terminating")
		return 2
	elif (secsoff==0):
		logger.info("time off set to zero, ending cycle")
		GPIO.output(27,GPIO.HIGH)
		pumpstate="off (cycle ended)"
		return 3
	elif ("cycle" not  in pumpstate): #and (touchval>9000)):
		logger.warning("timer cycle terminated; mode not set to cycle")   #todo: specifiy cause of termination (water level or alternate command)
		return 1

	else:
		GPIO.output(27,GPIO.HIGH)
		pumpstate="cycle off"
		logger.info("starting off cycle of " + str(secsoff) + "seconds, with cycleID " + str(mycycleid[0]) + ".")
		t=Timer(secsoff,timeon,[cycleid])
		t.start()
		return 0



def timeon(*mycycleid):
	global touchval
	global secson
	global secsoff
	global pumpstate
	global cycleid
	if (cycleid != mycycleid[0]):
		logger.warning("cycle id changed, currently " + str(cycleid) + "; old cycle " + str(mycycleid[0]) + " terminating")
		return 2
	elif (secson==0):
		logger.info("time on set to zero, ending cycle")
		GPIO.output(27,GPIO.LOW)
		pumpstate="on (cycle ended)"
		return 3
	elif (("cycle" not  in pumpstate) ):#and (touchval>9000)):    # uncomment when in action, commented for testing.
		logger.warning(pumpstate)
		logger.warning("timer cycle terminated; mode no longer set to cycle")   #todo: specifiy cause of termination (water level or alternate command)
		return 1

	else:
		GPIO.output(27,GPIO.LOW)
		pumpstate="cycle on"
		logger.info("starting on cycle of " + str(secson) + "seconds, with cycleID " + str(mycycleid[0]) + ".")
		t=Timer(secson,timeoff,[cycleid])
		t.start()
		return 0



@app.route("/pump/cycle/<hrson>/<hrsoff>")
def pumpduty(hrson,hrsoff):
	global secson
	secson=float(hrson)*60*60
	global secsoff
	secsoff=float(hrsoff)*60*60
	global pumpstate
	global cycleid
	cycleid=random.randrange(10000)
	pumpstate="cycle"
	logger.info("starting timed cycle of "+str(hrson)+" Hours on and "+str(hrsoff)+" hours off with cycleID "+str(cycleid)+".")
	if (secson != 0):
		timeon(cycleid)
	else:
		timeoff(cycleid)
  	templateData = {
        	'state' : 'Cycling'
	
        	}
	return render_template("pumpset.html", **templateData)

@app.route("/pump/cyclem/<hrson>/<hrsoff>")
def pumpdutym(hrson,hrsoff):
	global secson
	secson=float(hrson)*60
	global secsoff
	secsoff=float(hrsoff)*60
	global pumpstate
	pumpstate="cycle"
	global cycleid
	cycleid=random.randrange(10000)
	logger.info("starting timed cycle of "+str(hrson)+" Minutes on and "+str(hrsoff)+" Minutes off with cycleID "+str(cycleid)+".")
	if (secson != 0):
		timeon(cycleid)
	else:
		timeoff(cycleid)
  	templateData = {
        	'state' : 'Cycling'
	
        	}
	return render_template("pumpset.html", **templateData)




@app.route("/pump/on")
def pumpon():
    GPIO.output(27,GPIO.LOW)
    global pumpstate
    pumpstate='on'
    templateData = {
        'state' : 'on'

        }
    return render_template("pumpset.html", **templateData)

@app.route("/pump/off")
def pumpoff():
    GPIO.output(27,GPIO.HIGH)
    global pumpstate
    pumpstate="off"
    templateData = {
        'state' : 'off'

        }
    return render_template("pumpset.html", **templateData)





@app.route("/")
def index():
	now = datetime.datetime.now()
	timeString = now.strftime("%Y-%m-%d %I:%M:%S %p")
	
	#poollevel = random.randrange(100)
	minlevel=8500       #measured value  8400, rounded for simple math
	maxlevel=18500      #measured value 18700, rounded
	global touchval
	poollevel = (touchval-minlevel)/100
	global count
	count=count+1
	global pumpstate
	global cycleid
	templateData = {
		'title' : 'Pool Data',
		'time' : timeString,
		'poollevel' : poollevel,
		'count' : count,
		'touchval' : touchval,
		'pumpstate' : pumpstate,
		'cycleid' : cycleid
	}
	resp=make_response(render_template('index.html', **templateData))
	resp.headers['Cache-Control'] = 'no-cache,no-store,must-revalidate'
	return resp
    

@app.route('/test')
def testpage():
	return "Hello World! <br> Sucessful Test! <br> <a href='/'> Back Home </a>"

#setup GPIO callbacks

GPIO.add_event_detect(23,GPIO.BOTH,callback=test_callback)



try:
	if __name__ == "__main__":
		updateThread = Thread(target = update_thread)
		updateThread.start()
		app.run(debug=True,port=5000, host='0.0.0.0')


except KeyboardInterrupt: 
	GPIO.cleanup()                          #clean up gpio if ctrl+c exited
	logger.info("Recived Keyboard interrupt, quitting threads.")
	raise
GPIO.cleanup()                                 #clean up GPIO if normally exited
