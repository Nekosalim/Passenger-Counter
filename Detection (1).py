from abc import abstractmethod
import cv2
from cv2 import findContours
from cv2 import resize
from matplotlib.pyplot import contour
import numpy as np
import Person
import RPi.GPIO as GPIO
import time

#inisialisasi hitungan masuk dan keluar
cnt_up   = 0
cnt_down = 0

#inisialisasi switch pada pin GPIO
switch = 3

activator = 1

GPIO.setmode(GPIO.BOARD)
GPIO.setup(switch,GPIO.IN)


h = 480
w = 640


#cap = cv2.VideoCapture('Test Files/example_01.mp4')
cap = cv2.VideoCapture(0)
areaTH = 22500 # ukuran besaran hijau
objek_detector = cv2.createBackgroundSubtractorMOG2(history=3000,varThreshold=80)#th50

line_up = int(2*(h/5))
line_down   = int(3*(h/5))

up_limit =   int(1*(h/5))
down_limit = int(4*(h/5))

print( "Red line y:",str(line_down))
print( "Blue line y:", str(line_up))
line_down_color = (255,0,0)
line_up_color = (0,0,255)
pt1 =  [0, line_down];
pt2 =  [w, line_down];
pts_L1 = np.array([pt1,pt2], np.int32)
pts_L1 = pts_L1.reshape((-1,1,2))
pt3 =  [0, line_up];
pt4 =  [w, line_up];
pts_L2 = np.array([pt3,pt4], np.int32)
pts_L2 = pts_L2.reshape((-1,1,2))

pt5 =  [0, up_limit];
pt6 =  [w, up_limit];
pts_L3 = np.array([pt5,pt6], np.int32)
pts_L3 = pts_L3.reshape((-1,1,2))
pt7 =  [0, down_limit];
pt8 =  [w, down_limit];
pts_L4 = np.array([pt7,pt8], np.int32)
pts_L4 = pts_L4.reshape((-1,1,2))

font = cv2.FONT_HERSHEY_SIMPLEX
persons = []
max_p_age = 5
pid = 1
kernel=None

#########################
#####     SWITCH    #####
#########################
while True:
    #Pintu terbuka dan mengaktifkan program counter
    waktu = str(time.time())
    head, sep, tail = waktu.partition('.')
    waktu = head
    
    #if GPIO.input(switch) == 0:
     #   activator = 1
      #  f = open("./log/doorCounting.txt", 'w')
       # f.write(str(waktu)+"_")
        #f.flush()
    #########################
    ##### PINTU TERBUKA #####
    #########################

    while (activator == 1):
        _,frame = cap.read()
        
        #print( height, width)
       
        roi = frame[0: 480,90: 500]#roi = frame[panjang frame: batas panjang frame, posisi frame lebar: ujung frame lebar]
        blurred_frame = cv2.blur(roi, (20, 20), cv2.BORDER_DEFAULT)
        #image = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY )
        #Fullscreen
        cv2.namedWindow("frame", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("frame", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        
        #membuat file teks
        log = open("./log/door1.txt", 'w')
        log.write('0')
        
        for i in persons:
            i.age_one()
    
        mask = objek_detector.apply(blurred_frame)
        
        _, mask = cv2.threshold(mask, 250,255, cv2.THRESH_BINARY)
        
        mask = cv2.erode(mask, kernel, iterations = 1)
        mask = cv2.dilate(mask, kernel, iterations = 2)
        
        contours,_= cv2.findContours (mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
            
        for cnt in contours:
            
            area = cv2.contourArea (cnt)

            if area>areaTH:
                
                M=cv2.moments (cnt)
                cx=int (M['m10']/M['m00'])
                cy=int (M['m01']/M['m00'])
                x,y,w,h = cv2.boundingRect (cnt)
                new = True
                if cy in range(up_limit,down_limit):
                    for i in persons:
                        if abs(x-i.getX()) <= w and abs(y-i.getY()) <= h:
                            new = False
                            i.updateCoords(cx,cy)
                        
                        #jika terdeteksi lewat masuk, maka hitungan bertambah 1
                        if i.going_UP(line_down,line_up) == True:
                            cnt_up += 1;
                            #print( "Passenger:",i.getId(),'enter at',time.strftime("%c"))
                            #print("ENTER : "+ str(cnt_up) + '\n')
                        
                        #jika terdeteksi lewat keluar, maka hitungan bertambah 1
                        elif i.going_DOWN(line_down,line_up) == True:
                            cnt_down += 1;
                            #print( "Passenger:",i.getId(),'exit at',time.strftime("%c"))
                            #print("EXIT : "+ str(cnt_down) + '\n')
                            break
                    
                        if i.getState() == '1':
                            if i.getDir() == 'exit' and i.getY() > down_limit:
                                i.setDone()
                            elif i.getDir() == 'enter' and i.getY() < up_limit:
                                i.setDone()
                        if i.timedOut():
                            index = persons.index(i)
                            persons.pop(index)
                            del i
                    
                    
                    if new == True:
                        p = Person.MyPerson(pid,cx,cy, max_p_age)
                        persons.append(p)
                        pid += 1
                    
                #########################
                ###  MENGGAMBAR KOTAK ###
                #########################
                cv2.circle(roi,(cx,cy),5,(0, 0,255), 5)
                img=cv2.rectangle(roi, ( x, y), ( x+w, y+h), ( 0, 255, 0), 5)


        for i in persons:
            if len(i.getTracks()) >= 2:
                pts = np.array(i.getTracks(), np.int32)
                pts = pts.reshape((-1,1,2))
                roi = cv2.polylines(roi,[pts],False,i.getRGB())
           
        
        #########################
        ### MENAMPILKAN TEKS  ###
        ###    PADA LAYAR     ###
        #########################
        str_up = 'ENTER: '+ str(cnt_up)
        str_down = 'EXIT: '+ str(cnt_down)
        frame = cv2.polylines(frame,[pts_L1],False,line_down_color,thickness=2)
        frame = cv2.polylines(frame,[pts_L2],False,line_up_color,thickness=2)
        frame = cv2.polylines(frame,[pts_L3],False,(255,255,255),thickness=1)
        frame = cv2.polylines(frame,[pts_L4],False,(255,255,255),thickness=1)
        cv2.putText(frame, str_up ,(10,40),font,0.5,(255,255,255),2,cv2.LINE_AA)
        cv2.putText(frame, str_up ,(10,40),font,0.5,(0,0,255),1,cv2.LINE_AA)
        cv2.putText(frame, str_down ,(10,90),font,0.5,(255,255,255),2,cv2.LINE_AA)
        cv2.putText(frame, str_down ,(10,90),font,0.5,(255,0,0),1,cv2.LINE_AA)
        
        #cv2.imshow("screen",roi)
        cv2.imshow("frame", frame)
        #cv2.imshow("mask",mask)

        key = cv2.waitKey(1)
        if key == 27:
            break
        #########################
        #### PINTU TERTUTUP #####
        #########################
        waktu = str(time.time())
        head, sep, tail = waktu.partition('.')
        waktu = head
    
        #if GPIO.input(switch)==1:
         #   f = open("./log/doorCounting.txt", 'a')
          #  f.write(str(waktu)+"_"+str(cnt_up)+"_"+str(cnt_down))
           # log = open("./log/door1.txt", 'w')
           # activator = 0
           # log.write('1')
           # f.flush()
           # log.flush()
        
    

cap.release()
cv2.destroyAllWindows()