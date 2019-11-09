import math
import socket

import motor
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import turn

status     = 1          #Motor rotation
forward    = 1          #Motor forward
backward   = 0          #Motor backward

left_spd   = 100         #Speed of the car
right_spd  = 100         #Speed of the car

# Don't forget to change the variables for the MQTT broker!
mqtt_username = "visoni"
mqtt_password = "password"
mqtt_topic = "aucovei"

def setup():
    motor.setup()
    turn.turn_middle()

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

def turn_head(angle):
    print('')
    turn.turn_to_angle(angle)

def get_angle_from_coords(x,y):
    angle = 0.0
    #if x==0.0 and y==0.0:
    if 0 <= abs(x) <= 0.1 and 0 <= abs(y) <= 0.1:
        angle = 90.0
    elif x>=0.0 and y>=0.0:
        # first quadrant
        angle = math.degrees(math.atan(y/x)) if x!=0.0 else 90.0
    elif x<0.0 and y>=0.0:
        # second quadrant
        angle = math.degrees(math.atan(y/x))
        angle += 180.0
    elif x<0.0 and y<0.0:
        # third quadrant
        angle = math.degrees(math.atan(y/x))
        angle += 180.0
    elif x>=0.0 and y<0.0:
        # third quadrant
        angle = math.degrees(math.atan(y/x)) if x!=0.0 else -90.0
        angle += 360.0
    
    return round(angle, 2)

def get_motor_direction(x,y):
    if 0 <= abs(x) <= 0.2 and 0 <= abs(y) <= 0.2:
        return "stop"
    elif y > 0.1:
        return "forward"
    
    return "backward"

def drive_motor(direction, speed):
    if direction == "forward":
        motor.motor_left(status, forward,left_spd*abs(speed))
        motor.motor_right(status,backward,right_spd*abs(speed))
    elif direction == "backward":
        motor.motor_left(status, backward, left_spd*abs(speed))
        motor.motor_right(status, forward, right_spd*abs(speed))
    else:
        motor.motorStop()

# These functions handle what happens when the MQTT client connects
# to the broker, and what happens then the topic receives a message
def on_connect(client, userdata, flags, rc):
    # rc is the error code returned when connecting to the broker
    print ("Connected!", str(rc))
    
    # Once the client has connected to the broker, subscribe to the topic
    client.subscribe(mqtt_topic)
    
def on_message(client, userdata, msg):
    try:    
        data = str(msg.payload.decode("utf-8"))
        data = data.rstrip('\x00')
        #print ("Topic: ", msg.topic + "\nMessage: " + data)
        values = data.split('|') 
        if(len(values) > 1):
            x = float(values[0])
            y = float(values[1])

            angle = get_angle_from_coords(x,y)
            if angle > 180:
                angle = round(360 - angle,2)
            
            ## some correction to handle frequent movement
            if 90 < abs(angle) <= 120 and 60 <= abs(angle) < 90:
                angle = 90

            turn_head(angle)
            direction = get_motor_direction(x,y)
            drive_motor(direction,y)
            print('X:', x, " Y:", y, " angle:", angle, " direction: ", direction, end="\r")
    except Exception as e:
        print("Error occured " + str(e))


    # The message itself is stored in the msg variable
    # and details about who sent it are stored in userdata

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected disconnection.", str(rc))

if __name__ == "__main__":
    ip_address = get_ip_address()
    print("Host IP: ", ip_address)

    client = mqtt.Client()
    # Set the username and password for the MQTT client
    client.username_pw_set(mqtt_username, mqtt_password)

    # Here, we are telling the client which functions are to be run
    # on connecting, and on receiving a message
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect =  on_disconnect

    try:
        setup()
        # Once everything has been set up, we can (finally) connect to the broker
        # 1883 is the listener port that the MQTT broker is using
        client.connect(ip_address, 1883,60)

        # Once we have told the client to connect, let the client object run itself
        client.loop_forever()
        client.disconnect()
        motor.destroy()
    except Exception as e:
        print("Error occured " + str(e))
    finally:
        GPIO.cleanup()
        print("Done..")
