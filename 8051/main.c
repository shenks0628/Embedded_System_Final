#include <reg52.h> //包含標頭檔
#include <stdlib.h>
#include <string.h>
#include "uart.h"
#include "delay.h"
#include "keyscan.h"
typedef unsigned char byte;
typedef unsigned int  word;

#define DataPort P0 //定義資料埠 
#define	KeyPort	P1	//定義鍵盤埠
sbit k1 = P3 ^ 0;
sbit k2 = P3 ^ 1;
sbit LATCH1 = P3 ^ 7;	//定義鎖存使能埠 段鎖存
sbit LATCH2 = P3 ^ 6;	//              位鎖存

unsigned char code dofly_DuanMa[] = { 0x3f,0x06,0x5b,0x4f,0x66,0x6d,0x7d,0x07,0x7f,0x6f,
									  0x77,0x7c,0x39,0x5e,0x79,0x71 };      // 段碼0~F
unsigned char code dofly_WeiMa[] = { 0xfe,0xfd,0xfb,0xf7,0xef,0xdf,0xbf,0x7f };//位碼
byte TempData[8];
word mynum[5], myLife, oppoLife;
bit catchable = 0;

// state
#define WAIT 0
#define PREPARE 1
#define GUESS 2
#define END 3

/*------------------------------------------------
			顯示函數，用於動態掃瞄數碼管
------------------------------------------------*/
void Display(unsigned char FirstBit, unsigned char Num) {
	static unsigned char i = 0;
	DataPort = 0;   //清空資料，防止有交替重影
	LATCH1 = 1;     //段鎖存
	LATCH1 = 0;
	DataPort = dofly_WeiMa[i + FirstBit]; //取位碼 
	LATCH2 = 1;     //位鎖存
	LATCH2 = 0;
	DataPort = TempData[i]; //取顯示資料，段碼
	LATCH1 = 1;     //段鎖存
	LATCH1 = 0;
	i++;
	if (i == Num)
		i = 0;
}
/*------------------------------------------------
				計時器初始化副程式
------------------------------------------------*/
void Init_Timer0(void) {
	TMOD |= 0x01;//使用模式1，16位元計時器，使用"|"符號可以在使用多個計時器時不受影響
	EA = 1;      //總中斷打開
	ET0 = 1;     //計時器中斷打開
	TR0 = 1;     //計時器開關打開
}
/*------------------------------------------------
				 計時器中斷副程式
------------------------------------------------*/
void Timer0_isr(void) interrupt 1
{
	TH0 = (65536 - 2000) / 256;		  //重新賦值 2ms
	TL0 = (65536 - 2000) % 256;
	Display(0, 8);       // 調用數碼管掃瞄
	TF1 = 0;
}

char itoc(word x) {//int to char
	if (x == 10) return 'A';
	else return x + '0';
}
int ctoi(char x) {//char to int
	if (x == 'A') return 10;
	else return x - '0';
}

byte wait_input(word x) {//等待輸入
	byte key;
	key = KeyPro();
	while (key == 0xff) {
		TempData[x] = TempData[x] ^ 0x80;
		key = KeyPro();
		DelayMs(30);
	}
	TempData[x] = TempData[x] & 0x7f;
	return key;
}
void clearData() {//清屏
	word i;
	for (i = 0;i < 8;i++) TempData[i] = 0;
}
void switch_show() {
	word i;
	byte key, temp[8];
	for (i = 0;i < 8;i++) temp[i] = TempData[i]; //儲存
	clearData();//清屏
	TempData[0] = dofly_DuanMa[mynum[0]];
	TempData[1] = dofly_DuanMa[mynum[1]];
	TempData[2] = dofly_DuanMa[mynum[2]];
	TempData[3] = dofly_DuanMa[mynum[3]];
	TempData[4] = dofly_DuanMa[mynum[4]];
	TempData[7] = dofly_DuanMa[myLife];
	key = wait_input(7);
	while (key != 13) key = wait_input(7);
	for (i = 0;i < 8;i++) TempData[i] = temp[i]; //還原
}

void main(void) {
	char guess[5];
	byte key;
	word state = PREPARE, guess_cnt = 0, guess_num = 0;
	word oppo_guess_cnt = 0, oppo_guess_num = 1;
	InitUART();
	Init_Timer0();
	ES = 1;// 打開串口中斷
	while (1) {
		if (state == PREPARE) {
			key = wait_input(7);
			while (key != 16) key = wait_input(7);
			UART_SendStr("READY");// 準備完成
			state = WAIT;
		}
		else if (state == WAIT) {// 等待UART輸入
			if (TempData[0] != 0x38) {
				clearData();//清屏
				// 顯示LOAd...
				TempData[0] = 0x38, TempData[1] = 0x3f;
				TempData[2] = 0x77, TempData[3] = 0x5e;
				TempData[4] = 0x80, TempData[5] = 0x80;
				TempData[6] = 0x80;
			}
			if (rec_flag == 1) {// UART輸入
				clearData();//清屏
				buf[head] = '\0';
				if (buf[0] == 'W') {// 猜對
					// 顯示TrUE
					TempData[0] = 0x78, TempData[1] = 0x50;
					TempData[2] = 0x3e, TempData[3] = 0x79;
					state = PREPARE;
				}
				else if (buf[0] == 'L') {// 猜錯
					// 顯示FALSE
					TempData[0] = 0x71, TempData[1] = 0x77;
					TempData[2] = 0x38, TempData[3] = 0x6d;
					TempData[4] = 0x79;
					state = PREPARE;
				}
				else if (buf[0] == 'G') {// 每輪結束
					// 顯示End  X-Y
					myLife = ctoi(buf[5]);
					oppoLife = ctoi(buf[6]);
					TempData[0] = 0x79, TempData[1] = 0x54;
					TempData[2] = 0x5e, TempData[5] = dofly_DuanMa[ctoi(buf[5])];
					TempData[6] = 0x40, TempData[7] = dofly_DuanMa[ctoi(buf[6])];
					if (ctoi(buf[5]) <= 0 || ctoi(buf[6]) <= 0)state = END;
					else state = PREPARE;
				}
				else if (buf[0] == 'T') {// 輪到我猜
					oppo_guess_cnt = 0, oppo_guess_num = 1;
					state = GUESS;
				}
				else if (buf[0] == 'O') {// 接收對方猜「X個Y」
					// 顯示OPPO X Y
					TempData[0] = 0x3f, TempData[1] = 0x73;
					TempData[2] = 0x73, TempData[3] = 0x3f;
					oppo_guess_cnt = ctoi(buf[5]), oppo_guess_num = ctoi(buf[6]);
					TempData[5] = dofly_DuanMa[oppo_guess_cnt];
					TempData[7] = dofly_DuanMa[oppo_guess_num];
					key = wait_input(7);
					while (key != 16) key = wait_input(7);
					clearData();//清屏
					catchable = 1;//可以抓
					state = GUESS;
				}
				else {// 得到我的數字
					// 顯示我的數字
					mynum[0] = ctoi(buf[0]);
					mynum[1] = ctoi(buf[1]);
					mynum[2] = ctoi(buf[2]);
					mynum[3] = ctoi(buf[3]);
					mynum[4] = ctoi(buf[4]);
					TempData[0] = dofly_DuanMa[mynum[0]];
					TempData[1] = dofly_DuanMa[mynum[1]];
					TempData[2] = dofly_DuanMa[mynum[2]];
					TempData[3] = dofly_DuanMa[mynum[3]];
					TempData[4] = dofly_DuanMa[mynum[4]];
					state = PREPARE;
				}
				rec_flag = 0;
				head = 0;
			}
		}
		else if (state == GUESS) {// 猜測階段
			while (state == GUESS) {
				if (TempData[0] != 0x6f) {
					clearData();
					// 顯示GUESS 
					TempData[0] = 0x6f, TempData[1] = 0x3e;
					TempData[2] = 0x79, TempData[3] = 0x6d;
					TempData[4] = 0x6d;
				}
				key = KeyPro();
				if (key >= 1 && key <= 10) {
					while (key != 16) {
						if (key >= 1 && key <= 10) guess_cnt = key;
						else if (key == 13) switch_show();
						TempData[5] = dofly_DuanMa[guess_cnt];
						key = KeyPro();
						while (key == 0xff) key = wait_input(5);
					}
					TempData[6] = 0x40;
					key = KeyPro();
					while (!(key >= 1 && key <= 6)) {
						key = KeyPro();
						if (key == 13) switch_show();
					}
					while (key != 16) {
						if (key >= 1 && key <= 6) guess_num = key;
						else if (key == 13) switch_show();
						TempData[7] = dofly_DuanMa[guess_num];
						key = wait_input(7);
						while (key == 0xff) key = wait_input(7);
					}
					guess[0] = itoc(guess_cnt);
					guess[1] = itoc(guess_num);
					guess[2] = '\0';
					if ((guess_cnt == oppo_guess_cnt && guess_num <= oppo_guess_num) || (guess_cnt < oppo_guess_cnt)) {
						//顯示Error
						TempData[0] = 0x79, TempData[1] = 0x50;
						TempData[2] = 0x50, TempData[3] = 0x5c;
						TempData[4] = 0x50;
						key = wait_input(7);
						while (key != 16) key = wait_input(7);
						clearData();
						// 顯示OPPO X Y
						TempData[0] = 0x3f, TempData[1] = 0x73;
						TempData[2] = 0x73, TempData[3] = 0x3f;
						oppo_guess_cnt = ctoi(buf[5]), oppo_guess_num = ctoi(buf[6]);
						TempData[5] = dofly_DuanMa[oppo_guess_cnt];
						TempData[7] = dofly_DuanMa[oppo_guess_num];
						key = wait_input(7);
						while (key != 16) key = wait_input(7);
						continue;
					}
					UART_SendStr(guess);// 傳送猜測
					state = WAIT;
				}
				else if (key == 16 && catchable) {// 抓
					UART_SendStr("STOP");
					catchable = 0;
					state = WAIT;
				}
				else if (key == 13) switch_show();
			}
		}
		else if (state == END) {
			key = wait_input(7);
			while (key == 0xff) key = wait_input(7);
			state = PREPARE;
			if (key == 16) clearData();// 清屏
			else break;
		}
		DelayMs(10);
	}
}