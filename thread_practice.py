# client8_final.py


import socket
import threading
import sys
import time
import RPi.GPIO as GPIO
import smtplib
from email.mime.text import MIMEText



GPIO.setmode(GPIO.BCM)

# led setting
led_pin1 = 14
led_pin2 = 15
GPIO.setup(led_pin1, GPIO.OUT)
GPIO.setup(led_pin2, GPIO.OUT)


# piezo setting
gpio_pin = 13
scale = [523, 493]
GPIO.setup(gpio_pin, GPIO.OUT)

# jogswitch setting
gpio = [5, 6, 16, 20, 21]
stat = [0, 0, 0, 0, 0]
for i in range(5):
    GPIO.setup(gpio[i], GPIO.IN)

# Lcd setting
# (1) Define GPIO to LCD mapping
LCD_RS = 23
LCD_RW = 24
LCD_E = 26
LCD_D4 = 17
LCD_D5 = 18
LCD_D6 = 27
LCD_D7 = 22
# (2) Define some device constants
LCD_WIDTH = 16  # Maximum characters per line
LCD_CHR = True
LCD_CMD = False
LCD_LINE_1 = 0x80  # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0  # LCD RAM address for the 2nd line
# (3) Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)  # Use BCM GPIO numbers
GPIO.setup(LCD_E, GPIO.OUT)  # E
GPIO.setup(LCD_RS, GPIO.OUT)  # RS
GPIO.setup(LCD_D4, GPIO.OUT)  # DB4
GPIO.setup(LCD_D5, GPIO.OUT)  # DB5
GPIO.setup(LCD_D6, GPIO.OUT)  # DB6
GPIO.setup(LCD_D7, GPIO.OUT)  # DB7

# (4)
def lcd_init():
    # Initialise display
    lcd_byte(0x33, LCD_CMD)  # 00110011 Initialise
    lcd_byte(0x32, LCD_CMD)  # 00110010 Initialise
    lcd_byte(0x06, LCD_CMD)  # 00000110 Cursor move direction
    lcd_byte(0x0C, LCD_CMD)  # 00001100 Display On,Cursor Off, Blink Off
    lcd_byte(0x28, LCD_CMD)  # 00101000 Data length, number of lines, font size
    lcd_byte(0x01, LCD_CMD)  # 00000001 Clear display
    time.sleep(E_DELAY)


def lcd_toggle_enable():
    time.sleep(E_DELAY)
    GPIO.output(LCD_E, True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_E, False)
    time.sleep(E_DELAY)


def lcd_byte(bits, mode):
    # Send byte to data pins
    # bits = data
    # mode = True for character
    # False for command
    GPIO.output(LCD_RS, mode)  # RS

    # High bits
    GPIO.output(LCD_D4, False)
    GPIO.output(LCD_D5, False)
    GPIO.output(LCD_D6, False)
    GPIO.output(LCD_D7, False)
    if bits & 0x10 == 0x10:
        GPIO.output(LCD_D4, True)
    if bits & 0x20 == 0x20:
        GPIO.output(LCD_D5, True)
    if bits & 0x40 == 0x40:
        GPIO.output(LCD_D6, True)
    if bits & 0x80 == 0x80:
        GPIO.output(LCD_D7, True)
    # Toggle 'Enable' pin
    lcd_toggle_enable()

    # Low bits
    GPIO.output(LCD_D4, False)
    GPIO.output(LCD_D5, False)
    GPIO.output(LCD_D6, False)
    GPIO.output(LCD_D7, False)
    if bits & 0x01 == 0x01:
        GPIO.output(LCD_D4, True)
    if bits & 0x02 == 0x02:
        GPIO.output(LCD_D5, True)
    if bits & 0x04 == 0x04:
        GPIO.output(LCD_D6, True)
    if bits & 0x08 == 0x08:
        GPIO.output(LCD_D7, True)
    # Toggle 'Enable' pin
    lcd_toggle_enable()


def lcd_string(message, line):
    # Send string to display
    message = message.ljust(LCD_WIDTH, " ")  # left-align
    lcd_byte(line, LCD_CMD)
    for i in range(LCD_WIDTH):
        lcd_byte(ord(message[i]), LCD_CHR)

# led function
def blink(run_event):
    try:
        while run_event.is_set():
            GPIO.output(led_pin1, True)
            GPIO.output(led_pin2, False)  # Off 27
            for i in range(0, 10): # Wait one second
                if (run_event.is_set()):
                    time.sleep(0.1)
                else:
                    GPIO.output(led_pin1, False)
                    GPIO.output(led_pin2, False)  # Off 27
                    return
            # time.sleep(1)  # Wait one second
            GPIO.output(led_pin1, False)  # Off 17
            GPIO.output(led_pin2, True)  # On 27
            for i in range(0, 10): # Wait one second
                if (run_event.is_set()):
                    time.sleep(0.1)
                else:
                    GPIO.output(led_pin1, False)
                    GPIO.output(led_pin2, False)  # Off 27
                    return
            # time.sleep(1)  # Wait one second
        GPIO.output(led_pin1, False)
        GPIO.output(led_pin2, False)  # Off 27
    except:
        print("blink terminate")
        sys.exit()

# piezo function
def alert(run_event):
    try:
        p = GPIO.PWM(gpio_pin, 100)
        GPIO.output(gpio_pin, True)
        p.start(100)
        p.ChangeDutyCycle(20)

        while run_event.is_set():
            p.ChangeFrequency(scale[0])
            for i in range(0, 5):
                if (run_event.is_set()):
                    time.sleep(0.1)
                else:
                    return
            p.ChangeFrequency(scale[1])
            for i in range(0, 5):
                if (run_event.is_set()):
                    time.sleep(0.1)
                else:
                    return
    except:
        print("piezo terminate")
        sys.exit()

# Lcd function
def alertLcd(run_event):
    try:
        lcd_init()

        while run_event.is_set():
            lcd_string("Emergency!!", LCD_LINE_1)
            lcd_string("Please call 119!", LCD_LINE_2)


            for i in range(0, 15): # Wait 1.5 second
                if (run_event.is_set()):
                    time.sleep(0.1)
                else:
                    lcd_string("status:", LCD_LINE_1)
                    lcd_string("safe", LCD_LINE_2)
                    time.sleep(0.2)
                    return

            if (run_event.is_set()): # 버튼 누르면 빠른 종료를 위해 한번 더 체크
                lcd_string("After call 119,", LCD_LINE_1)
                lcd_string("Press red switch", LCD_LINE_2)

            for i in range(0, 15): # Wait 1.5 second
                if (run_event.is_set()):
                    time.sleep(0.1)
                else:
                    lcd_string("status:", LCD_LINE_1)
                    lcd_string("safe", LCD_LINE_2)
                    time.sleep(0.2)
                    return

        lcd_string("status:", LCD_LINE_1)
        lcd_string("safe", LCD_LINE_2)
        time.sleep(0.2)
    except:
        lcd_init()
        time.sleep(0.1)
        # print("lcd terminate")
        sys.exit()

# Send email function
def mail():
    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    smtp.starttls()
    smtp.login('sn990908a@gmail.com', 'tlbltzbaajurkhzb')
    msg = MIMEText("Emergency!! Check the current situation and this person's condition and take prompt action.")
    msg['Subject'] = 'Emergency Mail'
    # Send mail - public official
    # smtp.sendmail('sn990908a@gmail.com', 'sn990908a@gmail.com', msg.as_string())
    smtp.sendmail('sn990908a@gmail.com', 'c6mfthb2g@moakt.cc', msg.as_string())
    # Send mail - protector
    # smtp.sendmail('sn990908a@gmail.com', 'sn990908a@gmail.com', msg.as_string())
    smtp.sendmail('sn990908a@gmail.com', 'xejeg22876@pxjtw.com', msg.as_string())
    smtp.quit()

# main function
def emergencyAlarm(run_event):
    try:

        # 쓰레드 생성
        t1 = threading.Thread(target=blink, args = [run_event])
        t2 = threading.Thread(target=alert, args = [run_event])
        t3 = threading.Thread(target=alertLcd, args = [run_event])
        t4 = threading.Thread(target=mail)

        # 쓰레드 실행
        t1.start()
        t2.start()
        t3.start()
        t4.start()

        while run_event.is_set():
            for i in range(5):
                state = GPIO.input(gpio[i])
                if state != stat[i]:
                    stat[i] = state
            if (stat[4] == 1):
                # 쓰레드한테 종료 신호 보냄
                run_event.clear()

                # 모든 쓰레드가 종료되길 기다림
                t1.join()
                t2.join()
                t3.join()

                print("emergency Alarm Quit")

                send("emergencyEnd")
                # 현재 쓰레드 종료
                break

    except:
        print("alarm finish")


# 서버의 맥어드레스 설정
serverMACAddress = 'B8:27:EB:83:3E:F0' #RPi(미니파이)의 Bluetooth MAC Address
# serverMACAddress = ' B8:27:EB:46:4C:C7' #원래 보드의 Bluetooth MAC Address

# 블루투스 연결
port = 2
s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
s.connect((serverMACAddress,port))


# 쓰레드 제어를 위한 객체
run_event = threading.Event()
run_event.set()



# 서버가 보낸 data를 받고 실행시킬 동작
def service(data):
    quitThread = False
    # 프로세스 종료
    if data == "App is terminated!!":
        quitThread = True # 쓰레드 생성 못하게 막기
        run_event.clear()
        lcd_init()
        GPIO.cleanup()
        print("\nbye")
        sys.exit()

    # 새로운 리스닝 쓰레드 생성
    if quitThread == False:
        th = threading.Thread(target=recv)
        th.start()

    # 서버가 보낸 데이터에 따라 각기 다른 동작
    # 서버와 연결
    if data == "hello! this is server!":
        lcd_init()
        lcd_string("status:", LCD_LINE_1)
        lcd_string("safe", LCD_LINE_2)
        time.sleep(0.2)


    # emergency 동작 실행
    if data == "emergency":
        print("~~~~~~~~~~~~~~~~~~~~~~server sended emergency!!!!!!!")
        run_event.set()
        emergencyAlarm(run_event)

    # 터치 -> emergency 동작 해제
    if data == "touch":
        run_event.clear()

# send string to server
def send(msg):
    print("send to server: "+msg)
    msg = msg+"\n"
    # client.send(msg.encode())
    s.send(bytes(msg, 'UTF-8'))

# 리스닝 함수
# receive a message form the server
def recv():
    try:
        # 서버로부터 받은 메시지 출력
        byte_data = s.recv(1024)
        data = byte_data.decode().strip()
        print("server sended data: "+str(data))

        # 워커 쓰레드 생성
        worker= threading.Thread(target=service, args = [data])
        worker.start()

        return data
    except:
        print("recv terminate")
        sys.exit()

def main():
    try:
        recv()
    except:
        s.close()
        print("terminate main")

main()
