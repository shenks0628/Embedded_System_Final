import xtools, utime, urequests, ujson
from machine import RTC, UART, Pin, PWM, Timer
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
CHECK = 2
YOUR_TURN = 3
OPPONENT_TURN = 4
STOP = 5
WAIT_NEXT = 6
DATABASE_URL = "https://embedded-system-final-default-rtdb.asia-southeast1.firebasedatabase.app"

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
opponent_check = False
yours = []
opponents = []
yourHP = 3
opponentHP = 3
current_guess = []

def generate_random_numbers():
    return [random.randint(1, 6) for _ in range(5)]

def gameStart():
    global yourHP, opponentHP, yours
    yourHP = 3
    opponentHP = 3
    yours = generate_random_numbers()
    numStr = ""
    for i in yours:
        numStr += str(i)
    uart.write(numStr)
    utime.sleep(1)
    print("Numbers sent: ", numStr)
    client.publish(your_num_topic, numStr)
    utime.sleep(1)

def roundStart():
    global yours
    yours = generate_random_numbers()
    numStr = ""
    for i in yours:
        numStr += str(i)
    uart.write(numStr)
    utime.sleep(1)
    print("Numbers sent: ", numStr)
    client.publish(your_num_topic, numStr)
    utime.sleep(1)

def gameEnd():
    global mode, yourHP, opponentHP, opponent_ready, opponent_check
    # client.publish(status_topic, b"GAME END")
    print("GAME END")
    print("YOUR HP: ", yourHP)
    print("OPPONENT HP: ", opponentHP)
    uart.write(f"GAME:{yourHP}{opponentHP}\r\n")
    utime.sleep(1)
    utime.sleep(5)
    opponent_ready = False
    opponent_check = False
    mode = WAITING

def roundEnd():
    global mode, yourHP, opponentHP, opponent_ready, opponent_check
    # client.publish(status_topic, b"ROUND END")
    print("ROUND END")
    print("YOUR HP: ", yourHP)
    print("OPPONENT HP: ", opponentHP)
    uart.write(f"GAME:{yourHP}{opponentHP}\r\n")
    utime.sleep(1)
    utime.sleep(5)
    opponent_ready = False
    opponent_check = False
    mode = WAIT_NEXT

def playerTurn():
    global mode
    mode = YOUR_TURN
    print("Player1 Turn")
    uart.write("TURN\r\n")
    utime.sleep(1)

def check_guess(cnt, num):
    checker = 0
    for i in yours:
        if i == num:
            checker += 1
    for i in opponents:
        if i == num:
            checker += 1
    return checker

def player1WINDBUPD():
    mes = DATABASE_URL + "/player1.json"
    res = urequests.get(mes)
    r = res.text
    res.close()
    win = 1
    lose = 0
    if r != "null":
        data = ujson.loads(r)
        win += data["win"]
        lose += data["lose"]
    data = {"win": win, "lose": lose}
    mes = DATABASE_URL + "/player1.json"
    res = urequests.put(mes, json=data)
    res.close()

def player1LoseDBUPD():
    mes = DATABASE_URL + "/player1.json"
    res = urequests.get(mes)
    r = res.text
    res.close()
    win = 0
    lose = 1
    if r != "null":
        data = ujson.loads(r)
        win += data["win"]
        lose += data["lose"]
    data = {"win": win, "lose": lose}
    mes = DATABASE_URL + "/player1.json"
    res = urequests.put(mes, json=data)
    res.close()

def win(checker, num):
    global mode, yourHP, opponentHP
    # client.publish(status_topic, b"PLAYER1 WINS")
    print("PLAYER1 WINS")
    uart.write(f"WIN:{checker}{num}\r\n")
    utime.sleep(1)
    opponentHP -= 1
    if opponentHP == 0:
        gameEnd()
        player1WINDBUPD()
    else:
        roundEnd()

def lose(checker, num):
    global mode, yourHP, opponentHP
    # client.publish(status_topic, b"PLAYER2 WINS")
    print("PLAYER2 WINS")
    uart.write(f"LOSE:{checker}{num}\r\n")
    utime.sleep(1)
    yourHP -= 1
    if yourHP == 0:
        gameEnd()
        player1LoseDBUPD()
    else:
        roundEnd()

def sub_cb(topic, msg):
    global mode, opponent_ready, current_guess, opponents
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
                mode = CHECK
        elif msg == "PLAYER2 READY FOR NEXT":
            opponents.clear()
            opponent_ready = True
            if opponent_ready and mode == READY:
                print("ROUND START")
                roundStart()
                print("PLAYER1 NUMBERS SENT")
                mode = CHECK
        elif msg == "PLAYER2 CHECK":
            opponent_check = True
            if opponent_check and mode == CHECK:
                playerTurn()
        elif msg[:13] == "PLAYER2 GUESS":
            current_guess.clear()
            current_guess.insert(msg[15])
            current_guess.insert(msg[16])
            print("PLAYER2 GUESS:", msg[15:])
            uart.write(f"OPPO:{msg[15:]}\r\n")
            utime.sleep(1)
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
                win(checker, num)
            elif checker < cnt:
                lose(checker, num)
    elif topic == opponent_num_topic:
        opponents.clear()
        for i in msg:
            opponents.insert(i)
        print("Opponent's Numbers:", msg)

client.set_callback(sub_cb)
client.connect()
client.subscribe(status_topic)
# client.subscribe(your_num_topic)s
client.subscribe(opponent_num_topic)

print('MicroPython Ready...')  # 輸出訊息到終端機
uart.write('MicroPython Ready...')
utime.sleep(1)

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
                mode = CHECK
        elif mode == WAIT_NEXT and msg == b"READY":
            yours.clear()
            client.publish(status_topic, b"PLAYER1 READY FOR NEXT")
            print("PLAYER1 READY FOR NEXT")
            mode = READY
            if opponent_ready and mode == READY:
                print("ROUND START")
                roundStart()
                print("PLAYER1 NUMBERS SENT")
                mode = CHECK
        elif mode == CHECK and msg == b"READY":
            client.publish(status_topic, b"PLAYER1 CHECK")
            print("PLAYER1 CHECK")
            if opponent_check and mode == CHECK:
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
                    lose(checker, num)
                elif checker < cnt:
                    win(checker, num)
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

