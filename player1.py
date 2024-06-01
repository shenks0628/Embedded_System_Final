import xtools, utime
from machine import RTC, UART, Pin, PWM
from umqtt.simple import MQTTClient
import random

xtools.connect_wifi_led()

ADAFRUIT_IO_USERNAME = "shen115"
ADAFRUIT_IO_KEY      = "aio_djoS46LGpo3MXlmcpWEvA2T7zfMK"
STATUS = "status"
YOUR_NUM = "player1-num"
OPPONENT_NUM = "player2-num"
PLAYER1 = "PLAYER1"
PLAYER2 = "PLAYER2"
WAITING = 0
READY = 1
YOUR_TURN = 2
OPPONENT_TURN = 3
STOP = 4
WAIT_NEXT = 5

# MQTT 客戶端
client = MQTTClient (
    client_id = xtools.get_id(),
    server = "io.adafruit.com",
    user = ADAFRUIT_IO_USERNAME,
    password = ADAFRUIT_IO_KEY,
    ssl = False,
)

uart = UART(2, 9600, tx=17, rx=16)
uart.init(9600)

status_topic = ADAFRUIT_IO_USERNAME + "/feeds/" + STATUS
your_num_topic = ADAFRUIT_IO_USERNAME + "/feeds/" + YOUR_NUM
opponent_num_topic = ADAFRUIT_IO_USERNAME + "/feeds/" + OPPONENT_NUM

mode = WAITING
opponent_ready = False
yours = []
opponents = []
yourHP = 3
opponentHP = 3
current_guess = []

def generate_random_numbers():
    return [random.randint(1, 6) for _ in range(5)]

def gameStart():
    global yourHP, opponentHP
    yourHP = 3
    opponentHP = 3
    yours = generate_random_numbers()
    numStr = ""
    for i in yours:
        numStr += str(i)
    uart.write(numStr)
    uart.sleep(1)
    print("Numbers sent: ", numStr)
    client.publish(your_num_topic, numStr)
    utime.sleep(1)

def roundStart():
    yours = generate_random_numbers()
    numStr = ""
    for i in yours:
        numStr += str(i)
    uart.write(numStr)
    uart.sleep(1)
    print("Numbers sent: ", numStr)
    client.publish(your_num_topic, numStr)
    utime.sleep(1)

def gameEnd():
    global mode, yourHP, opponentHP
    # client.publish(status_topic, b"GAME END")
    print("GAME END")
    print("YOUR HP: ", yourHP)
    print("OPPONENT HP: ", opponentHP)
    uart.write(f"GAME:{yourHP}{opponentHP}\r\n")
    uart.sleep(1)
    utime.sleep(5)
    mode = WAITING

def roundEnd():
    global mode, yourHP, opponentHP
    # client.publish(status_topic, b"ROUND END")
    print("ROUND END")
    print("YOUR HP: ", yourHP)
    print("OPPONENT HP: ", opponentHP)
    uart.write(f"GAME:{yourHP}{opponentHP}\r\n")
    uart.sleep(1)
    utime.sleep(5)
    mode = WAIT_NEXT

def playerTurn():
    global mode
    mode = YOUR_TURN
    uart.write("TURN\r\n")
    uart.sleep(1)

def check_guess(cnt, num):
    checker = 0
    for i in yours:
        if i == num:
            checker += 1
    for i in opponents:
        if i == num:
            checker += 1
    return checker

def win():
    global mode, yourHP, opponentHP
    # client.publish(status_topic, b"PLAYER1 WINS")
    print("PLAYER1 WINS")
    uart.write(f"WIN:{checker}{num}\r\n")
    uart.sleep(1)
    opponentHP -= 1
    if opponentHP == 0:
        gameEnd()
    else:
        roundEnd()

def lose():
    global mode, yourHP, opponentHP
    # client.publish(status_topic, b"PLAYER2 WINS")
    print("PLAYER2 WINS")
    uart.write(f"LOSE:{checker}{num}\r\n")
    uart.sleep(1)
    yourHP -= 1
    if yourHP == 0:
        gameEnd()
    else:
        roundEnd()

def sub_cb(topic, msg):
    global mode, opponent_ready, current_guess
    msg = msg.decode()
    print(msg)
    msg = str(msg)
    if topic == status_topic:
        if msg == "PLAYER2 READY":
            opponents.clear()
            opponent_ready = True
            if opponent_ready and mode == READY:
                print("GAME START")
                gameStart()
                print("PLAYER1 NUMBERS SENT")
                print("PLAYER1 TURN")
                playerTurn()
        elif msg == "PLAYER2 READY FOR NEXT":
            opponents.clear()
            opponent_ready = True
            if opponent_ready and mode == READY:
                print("ROUND START")
                roundStart()
                print("PLAYER1 NUMBERS SENT")
                print("PLAYER1 TURN")
                playerTurn()
        elif msg[:13] == "PLAYER2 GUESS":
            current_guess.clear()
            current_guess.insert(msg[15])
            current_guess.insert(msg[16])
            print("PLAYER2 GUESS:", msg[15:])
            uart.write(f"OPPO:{msg[15:]}\r\n")
            uart.sleep(1)
            utime.sleep(5)
            playerTurn()
        elif msg == "PLAYER2 CALLS STOP":
            print("PLAYER2 CALLS STOP")
            mode = STOP
            cnt = (current_guess[0] - '0')
            if current_guess[0] == 'A':
                cnt = 10
            num = (current_guess[1] - '0')
            checker = check_guess(cnt, num)
            if checker >= cnt:
                win()
            elif checker < cnt:
                lose()
    elif topic == opponent_num_topic:
        opponents = msg.split(',')
        print("Opponent's Numbers:", msg)

client.set_callback(sub_cb)
client.connect()
client.subscribe(status_topic)
# client.subscribe(your_num_topic)s
client.subscribe(opponent_num_topic)

print('MicroPython Ready...')  # 輸出訊息到終端機
uart.write('MicroPython Ready...')
uart.sleep(1)

while True:
    client.check_msg()
    utime.sleep(1)
    if uart.any() > 0:
        msg = uart.readline()
        if mode == WAITING and msg == b"READY":
            yours.clear()
            client.publish(status_topic, b"PLAYER1 READY")
            print("PLAYER1 READY")
            mode = READY
            if opponent_ready and mode == READY:
                print("GAME START")
                gameStart()
                print("PLAYER1 NUMBERS SENT")
                print("PLAYER1 TURN")
                playerTurn()
        elif mode == WAIT_NEXT and msg == b"READY":
            yours.clear()
            client.publish(status_topic, b"PLAYER1 READY FOR NEXT")
            print("PLAYER1 READY FOR NEXT")
            mode = READY
            if opponent_ready and mode == READY:
                print("ROUND START")
                roundStart()
                print("PLAYER1 NUMBERS SENT")
                print("PLAYER1 TURN")
                playerTurn()
        elif mode == YOUR_TURN:
            if msg == b"STOP":
                client.publish(status_topic, b"PLAYER1 CALLS STOP")
                print("PLAYER1 CALLS STOP")
                mode = STOP
                cnt = (current_guess[0] - '0')
                if current_guess[0] == 'A':
                    cnt = 10
                num = (current_guess[1] - '0')
                checker = check_guess(cnt, num)
                if checker >= cnt:
                    lose()
                elif checker < cnt:
                    win()
            else:
                msg = str(msg)
                if len(msg) != 2:
                    continue
                current_guess.clear()
                current_guess.insert(msg[0])
                current_guess.insert(msg[1])
                client.publish(status_topic, b"PLAYER1 GUESS: " + msg)
                print("PLAYER1 GUESS:", msg)
                mode = OPPONENT_TURN

