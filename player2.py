import xtools, utime, urequests, ujson
from machine import RTC, UART, Pin, PWM, Timer
from umqtt.simple import MQTTClient
import random
from sound import play_sound, play_win

xtools.connect_wifi_led()

ADAFRUIT_IO_USERNAME = "shen115"
ADAFRUIT_IO_KEY      = "aio_djoS46LGpo3MXlmcpWEvA2T7zfMK"
STATUS = "status"
YOUR_NUM = "player2-num"
OPPONENT_NUM = "player1-num"
PLAYER1 = "PLAYER1"
PLAYER2 = "PLAYER2"
WAITING = 0
READY = 1
WAIT_CHECK = 2
CHECK = 3
YOUR_TURN = 4
OPPONENT_TURN = 5
STOP = 6
WAIT_CONFIRM = 7
CONFIRM = 8
WAIT_NEXT = 9
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
opponent_confirm = False
current_status = 0
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
    uart.write(numStr + "\r\n")
    print("Numbers sent: ", numStr)
    client.publish(your_num_topic, numStr)

def roundStart():
    global yours
    yours = generate_random_numbers()
    numStr = ""
    for i in yours:
        numStr += str(i)
    uart.write(numStr + "\r\n")
    print("Numbers sent: ", numStr)
    client.publish(your_num_topic, numStr)

def gameEnd():
    global mode, yourHP, opponentHP, opponent_ready, opponent_check, current_status, opponent_confirm
    print("GAME END")
    print("YOUR HP: ", yourHP)
    print("OPPONENT HP: ", opponentHP)
    uart.write(f"GAME:{yourHP}{opponentHP}\r\n")
    opponent_ready = False
    opponent_check = False
    opponent_confirm = False
    current_status = 0
    mode = WAITING

def roundEnd():
    global mode, yourHP, opponentHP, opponent_ready, opponent_check, current_status, opponent_confirm
    print("ROUND END")
    print("YOUR HP: ", yourHP)
    print("OPPONENT HP: ", opponentHP)
    uart.write(f"GAME:{yourHP}{opponentHP}\r\n")
    opponent_ready = False
    opponent_check = False
    opponent_confirm = False
    current_status = 0
    mode = WAIT_NEXT

def playerTurn():
    global mode
    mode = YOUR_TURN
    print("Player2 Turn")
    uart.write("TURN\r\n")

def player2WINDBUPD():
    mes = DATABASE_URL + "/diceGame/player2.json"
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
    mes = DATABASE_URL + "/diceGame/player2.json"
    res = urequests.put(mes, json=data)
    res.close()

def player2LOSEDBUPD():
    mes = DATABASE_URL + "/diceGame/player2.json"
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
    mes = DATABASE_URL + "/diceGame/player2.json"
    res = urequests.put(mes, json=data)
    res.close()

def win(checker, num):
    global mode, yourHP, opponentHP, current_status
    print("PLAYER2 WINS")
    uart.write(f"WIN:{checker}{num}\r\n")
    mode = WAIT_CONFIRM
    current_status = 1

def lose(checker, num):
    global mode, yourHP, opponentHP, current_status
    print("PLAYER1 WINS")
    uart.write(f"LOSE:{checker}{num}\r\n")
    mode = WAIT_CONFIRM
    current_status = -1

def sub_cb(topic, msg):
    global mode, opponent_ready, current_guess, opponents, opponent_check, current_status, opponent_confirm, yourHP, opponentHP, yours
    msg = msg.decode()
    print(msg)
    msg = str(msg)
    if topic == b"shen115/feeds/status":
        if msg == "PLAYER1 READY":
            # opponents.clear()
            opponent_ready = True
            if opponent_ready and mode == READY:
                print("GAME START")
                gameStart()
                print("PLAYER2 NUMBERS SENT")
                mode = WAIT_CHECK
        elif msg == "PLAYER1 READY FOR NEXT":
            # opponents.clear()
            opponent_ready = True
            if opponent_ready and mode == READY:
                print("ROUND START")
                roundStart()
                print("PLAYER2 NUMBERS SENT")
                mode = WAIT_CHECK
        elif msg == "PLAYER1 CHECK":
            opponent_check = True
            if opponent_check and mode == CHECK:
                mode = OPPONENT_TURN
        elif msg[:13] == "PLAYER1 GUESS":
            current_guess.clear()
            current_guess.append(msg[15])
            current_guess.append(msg[16])
            print("PLAYER1 GUESS:", msg[15:])
            uart.write(f"OPPO:{msg[15:]}\r\n")
            mode = YOUR_TURN
        elif msg == "PLAYER1 CALLS STOP":
            print("PLAYER1 CALLS STOP")
            mode = STOP
            cnt = 0
            if current_guess[0] == 'A':
                cnt = 10
            else:
                cnt = int(current_guess[0])
            num = int(current_guess[1])
            checker = 0
            for i in yours:
                if i == num:
                    checker += 1
            for i in opponents:
                if i == num:
                    checker += 1
            print(f"CNT: {cnt}, NUM: {num}, CHECKER: {checker}")
            print("YOUR NUMBERS:", yours)
            print("OPPONENT NUMBERS:", opponents)
            if checker >= cnt:
                win(checker, num)
            elif checker < cnt:
                lose(checker, num)
        elif msg == "PLAYER1 CONFIRM":
            opponent_confirm = True
            if opponent_confirm and mode == CONFIRM:
                if current_status == 1:
                    opponentHP -= 1
                    if opponentHP == 0:
                        gameEnd()
                        play_win()
                        player2WINDBUPD()
                    else:
                        roundEnd()
                elif current_status == -1:
                    yourHP -= 1
                    if yourHP == 0:
                        gameEnd()
                        player2LOSEDBUPD()
                    else:
                        roundEnd()
    elif topic == b"shen115/feeds/player1-num":
        opponents.clear()
        for i in msg:
            opponents.append(int(i))
        print("Opponent's Numbers:", msg)

client.set_callback(sub_cb)
client.connect()
client.subscribe(status_topic)
client.subscribe(opponent_num_topic)

print('MicroPython Ready...')  # 輸出訊息到終端機

while True:
    client.check_msg()
    if uart.any() > 0:
        msg = uart.readline()
        if mode == WAITING and msg == b"READY":
            yours.clear()
            client.publish(status_topic, b"PLAYER2 READY")
            print("PLAYER2 READY")
            mode = READY
            if opponent_ready and mode == READY:
                print("GAME START")
                gameStart()
                print("PLAYER2 NUMBERS SENT")
                mode = WAIT_CHECK
        elif mode == WAIT_NEXT and msg == b"READY":
            yours.clear()
            client.publish(status_topic, b"PLAYER2 READY FOR NEXT")
            print("PLAYER2 READY FOR NEXT")
            mode = READY
            if opponent_ready and mode == READY:
                print("ROUND START")
                roundStart()
                print("PLAYER2 NUMBERS SENT")
                mode = WAIT_CHECK
        elif mode == WAIT_CHECK and msg == b"READY":
            client.publish(status_topic, b"PLAYER2 CHECK")
            print("PLAYER2 CHECK")
            mode = CHECK
            if opponent_check and mode == CHECK:
                mode = OPPONENT_TURN
        elif mode == WAIT_CONFIRM and msg == b"READY":
            client.publish(status_topic, b"PLAYER2 CONFIRM")
            print("PLAYER2 CONFIRM")
            mode = CONFIRM
            if opponent_confirm and mode == CONFIRM:
                if current_status == 1:
                    opponentHP -= 1
                    if opponentHP == 0:
                        gameEnd()
                        player2WINDBUPD()
                    else:
                        roundEnd()
                elif current_status == -1:
                    yourHP -= 1
                    if yourHP == 0:
                        gameEnd()
                        player2LOSEDBUPD()
                    else:
                        roundEnd()
        elif mode == YOUR_TURN:
            if msg == b"STOP":
                client.publish(status_topic, b"PLAYER2 CALLS STOP")
                print("PLAYER2 CALLS STOP")
                mode = STOP
                cnt = 0
                if current_guess[0] == 'A':
                    cnt = 10
                else:
                    cnt = int(current_guess[0])
                num = int(current_guess[1])
                checker = 0
                for i in yours:
                    if i == num:
                        checker += 1
                for i in opponents:
                    if i == num:
                        checker += 1
                print(f"CNT: {cnt}, NUM: {num}, CHECKER: {checker}")
                print("YOUR NUMBERS:", yours)
                print("OPPONENT NUMBERS:", opponents)
                if checker >= cnt:
                    lose(checker, num)
                elif checker < cnt:
                    win(checker, num)
            else:
                msg = str(msg)
                if len(msg) != 5:
                    continue
                current_guess.clear()
                current_guess.append(msg[2])
                current_guess.append(msg[3])
                client.publish(status_topic, b"PLAYER2 GUESS: " + bytes(msg[2], "utf-8") + bytes(msg[3], "utf-8"))
                print(f"PLAYER2 GUESS: {msg[2]}{msg[3]}")
                mode = OPPONENT_TURN

