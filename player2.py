import xtools, utime, urequests, ujson
from machine import RTC, UART, Pin, PWM, Timer
from umqtt.simple import MQTTClient
import random
from sound import play_sound, play_win, play_lose, play_notify

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

def generate_random_numbers(): # 產生隨機數字
    return [random.randint(1, 6) for _ in range(5)]

def gameStart(): # 遊戲開始
    global yourHP, opponentHP, yours
    yourHP = 3
    opponentHP = 3
    yours = generate_random_numbers()
    numStr = ""
    for i in yours:
        numStr += str(i)
    uart.write(numStr + "\r\n") # 透過 UART 傳送數字
    print("Numbers sent: ", numStr)
    client.publish(your_num_topic, numStr)

def roundStart(): # 回合開始
    global yours
    yours = generate_random_numbers()
    numStr = ""
    for i in yours:
        numStr += str(i)
    uart.write(numStr + "\r\n") # 透過 UART 傳送數字
    print("Numbers sent: ", numStr)
    client.publish(your_num_topic, numStr)

def gameEnd(): # 遊戲結束
    global mode, yourHP, opponentHP, opponent_ready, opponent_check, current_status, opponent_confirm
    print("GAME END")
    print("YOUR HP: ", yourHP)
    print("OPPONENT HP: ", opponentHP)
    uart.write(f"GAME:{yourHP}{opponentHP}\r\n") # 透過 UART 傳送遊戲結果
    # 重置遊戲狀態
    opponent_ready = False
    opponent_check = False
    opponent_confirm = False
    current_status = 0
    mode = WAITING

def roundEnd(): # 回合結束
    global mode, yourHP, opponentHP, opponent_ready, opponent_check, current_status, opponent_confirm
    print("ROUND END")
    print("YOUR HP: ", yourHP)
    print("OPPONENT HP: ", opponentHP)
    uart.write(f"GAME:{yourHP}{opponentHP}\r\n") # 透過 UART 傳送遊戲結果
    # 重置回合狀態
    opponent_ready = False
    opponent_check = False
    opponent_confirm = False
    current_status = 0
    mode = WAIT_NEXT

def playerTurn(): # 玩家回合
    global mode
    mode = YOUR_TURN
    play_notify()
    print("Player2 Turn")
    uart.write("TURN\r\n")

def player2WINDBUPD(): # 更新玩家2勝利次數
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

def player2LOSEDBUPD(): # 更新玩家2失敗次數
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

def win(checker, num): # 玩家勝利
    global mode, yourHP, opponentHP, current_status
    print("PLAYER2 WINS")
    uart.write(f"WIN:{checker}{num}\r\n") # 透過 UART 傳送勝利訊息
    mode = WAIT_CONFIRM
    current_status = 1 # 儲存勝利狀態

def lose(checker, num): # 玩家失敗
    global mode, yourHP, opponentHP, current_status
    print("PLAYER1 WINS")
    uart.write(f"LOSE:{checker}{num}\r\n") # 透過 UART 傳送失敗訊息
    mode = WAIT_CONFIRM
    current_status = -1 # 儲存失敗狀態

def sub_cb(topic, msg): # 訂閱回調函數
    global mode, opponent_ready, current_guess, opponents, opponent_check, current_status, opponent_confirm, yourHP, opponentHP, yours
    msg = msg.decode()
    print(msg)
    msg = str(msg)
    if topic == b"shen115/feeds/status": # 接收對手狀態
        if msg == "PLAYER1 READY": # 對手準備好
            opponent_ready = True
            if opponent_ready and mode == READY: # 如果對手準備好且遊戲狀態為 READY（自己也準備好）
                print("GAME START")
                gameStart()
                print("PLAYER2 NUMBERS SENT")
                mode = WAIT_CHECK
        elif msg == "PLAYER1 READY FOR NEXT": # 對手準備好下一回合
            opponent_ready = True
            if opponent_ready and mode == READY: # 如果對手準備好且遊戲狀態為 READY（自己也準備好）
                print("ROUND START")
                roundStart()
                print("PLAYER2 NUMBERS SENT")
                mode = WAIT_CHECK
        elif msg == "PLAYER1 CHECK": # 對手確認
            opponent_check = True
            if opponent_check and mode == CHECK: # 如果對手確認且遊戲狀態為 CHECK（自己也確認）
                mode = OPPONENT_TURN
        elif msg[:13] == "PLAYER1 GUESS": # 對手猜測
            # 存入此時猜測數字
            current_guess.clear()
            current_guess.append(msg[15])
            current_guess.append(msg[16])
            print("PLAYER1 GUESS:", msg[15:])
            uart.write(f"OPPO:{msg[15:]}\r\n") # 透過 UART 傳送對手猜測數字
            play_notify() # 播放提示音
            mode = YOUR_TURN
        elif msg == "PLAYER1 CALLS STOP": # 對手喊停
            print("PLAYER1 CALLS STOP")
            mode = STOP
            cnt = 0
            if current_guess[0] == 'A': # 如果猜測的數字為 A，則代表為 10
                cnt = 10
            else: # 否則取第一個字元轉換為整數
                cnt = int(current_guess[0])
            num = int(current_guess[1]) # 取第二個字元轉換為整數
            checker = 0 # 計算猜測的數字是否符合
            for i in yours:
                if i == num:
                    checker += 1
            for i in opponents:
                if i == num:
                    checker += 1
            print(f"CNT: {cnt}, NUM: {num}, CHECKER: {checker}")
            print("YOUR NUMBERS:", yours)
            print("OPPONENT NUMBERS:", opponents)
            if checker >= cnt: # 如果自己猜測的數字符合，自己勝利
                win(checker, num)
            elif checker < cnt: # 如果自己猜測的數字不符合，自己失敗
                lose(checker, num)
        elif msg == "PLAYER1 CONFIRM": # 對手確認
            opponent_confirm = True
            if opponent_confirm and mode == CONFIRM: # 如果對手確認且遊戲狀態為 CONFIRM（自己也確認）
                if current_status == 1: # 如果狀態為勝利
                    opponentHP -= 1
                    if opponentHP == 0: # 如果對手血量為 0，則遊戲結束
                        gameEnd()
                        play_win() # 播放勝利音效
                        player2WINDBUPD()
                    else: # 否則回合結束
                        roundEnd()
                elif current_status == -1: # 如果狀態為失敗
                    yourHP -= 1
                    if yourHP == 0: # 如果自己血量為 0，則遊戲結束
                        gameEnd()
                        play_lose() # 播放失敗音效
                        player2LOSEDBUPD()
                    else: # 否則回合結束
                        roundEnd()
    elif topic == b"shen115/feeds/player1-num": # 接收對手數字
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
    if uart.any() > 0: # 如果 UART 有資料
        msg = uart.readline()
        if mode == WAITING and msg == b"READY": # 如果遊戲狀態為 WAITING 且收到 READY 訊息
            yours.clear()
            client.publish(status_topic, b"PLAYER2 READY") # 發布準備好訊息
            print("PLAYER2 READY")
            mode = READY
            if opponent_ready and mode == READY: # 如果對手準備好且遊戲狀態為 READY（自己也準備好）
                print("GAME START")
                gameStart()
                print("PLAYER2 NUMBERS SENT")
                mode = WAIT_CHECK
        elif mode == WAIT_NEXT and msg == b"READY": # 如果遊戲狀態為 WAIT_NEXT 且收到 READY 訊息
            yours.clear()
            client.publish(status_topic, b"PLAYER2 READY FOR NEXT") # 發布準備好下一回合訊息
            print("PLAYER2 READY FOR NEXT")
            mode = READY
            if opponent_ready and mode == READY: # 如果對手準備好且遊戲狀態為 READY（自己也準備好）
                print("ROUND START")
                roundStart()
                print("PLAYER2 NUMBERS SENT")
                mode = WAIT_CHECK
        elif mode == WAIT_CHECK and msg == b"READY": # 如果遊戲狀態為 WAIT_CHECK 且收到 READY 訊息
            client.publish(status_topic, b"PLAYER2 CHECK") # 發布確認訊息
            print("PLAYER2 CHECK")
            mode = CHECK
            if opponent_check and mode == CHECK: # 如果對手確認且遊戲狀態為 CHECK（自己也確認）
                mode = OPPONENT_TURN
        elif mode == WAIT_CONFIRM and msg == b"READY": # 如果遊戲狀態為 WAIT_CONFIRM 且收到 READY 訊息
            client.publish(status_topic, b"PLAYER2 CONFIRM") # 發布確認訊息
            print("PLAYER2 CONFIRM")
            mode = CONFIRM
            if opponent_confirm and mode == CONFIRM: # 如果對手確認且遊戲狀態為 CONFIRM（自己也確認）
                if current_status == 1: # 如果狀態為勝利
                    opponentHP -= 1
                    if opponentHP == 0: # 如果對手血量為 0，則遊戲結束
                        gameEnd()
                        play_win() # 播放勝利音效
                        player2WINDBUPD()
                    else: # 否則回合結束
                        roundEnd()
                elif current_status == -1: # 如果狀態為失敗
                    yourHP -= 1
                    if yourHP == 0: # 如果自己血量為 0，則遊戲結束
                        gameEnd()
                        play_lose() # 播放失敗音效
                        player2LOSEDBUPD()
                    else: # 否則回合結束
                        roundEnd()
        elif mode == YOUR_TURN:
            if msg == b"STOP": # 喊停
                client.publish(status_topic, b"PLAYER2 CALLS STOP") # 發布喊停訊息
                print("PLAYER2 CALLS STOP")
                mode = STOP
                cnt = 0
                if current_guess[0] == 'A': # 如果對手猜測的數字為 A，則代表為 10
                    cnt = 10
                else: # 否則取第一個字元轉換為整數
                    cnt = int(current_guess[0])
                num = int(current_guess[1]) # 取第二個字元轉換為整數
                checker = 0 # 計算猜測的數字是否符合
                for i in yours:
                    if i == num:
                        checker += 1
                for i in opponents:
                    if i == num:
                        checker += 1
                print(f"CNT: {cnt}, NUM: {num}, CHECKER: {checker}")
                print("YOUR NUMBERS:", yours)
                print("OPPONENT NUMBERS:", opponents)
                if checker >= cnt: # 如果對手猜測的數字符合，對手勝利
                    lose(checker, num)
                elif checker < cnt: # 如果對手猜測的數字不符合，對手失敗
                    win(checker, num)
            else: # 猜測數字
                msg = str(msg)
                if len(msg) != 5:
                    continue
                # 存入此時猜測數字
                current_guess.clear()
                current_guess.append(msg[2])
                current_guess.append(msg[3])
                client.publish(status_topic, b"PLAYER2 GUESS: " + bytes(msg[2], "utf-8") + bytes(msg[3], "utf-8")) # 發布猜測數字
                print(f"PLAYER2 GUESS: {msg[2]}{msg[3]}")
                mode = OPPONENT_TURN

