#include <reg52.h> //包含標頭檔，一般情況不需要改動，標頭檔包含特殊功能寄存器的定義 
#include "uart.h"
#include "delay.h"
#include "keyscan.h"
typedef unsigned char byte;
typedef unsigned int  word;

#define DataPort P0 //定義資料埠 
#define	KeyPort	P1	//定義鍵盤埠
sbit k1 = P2 ^ 0;
sbit k2 = P2 ^ 1;
sbit SPK = P2 ^ 2;  //定義音樂輸出埠
sbit LATCH1 = P2 ^ 7;	//定義鎖存使能埠 段鎖存
sbit LATCH2 = P2 ^ 6;	//               位鎖存

unsigned char code dofly_DuanMa[] = { 0x3f,0x06,0x5b,0x4f,0x66,0x6d,0x7d,0x07,0x7f,0x6f,
                                     0x77,0x7c,0x39,0x5e,0x79,0x71 };      // 段碼0~F
unsigned char code dofly_WeiMa[] = { 0xfe,0xfd,0xfb,0xf7,0xef,0xdf,0xbf,0x7f };//位碼
byte TempData[10];
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
                 計時器中斷副程式
------------------------------------------------*/
void Timer0_isr(void) interrupt 1
{
    TH0 = (65536 - 2000) / 256;		  //重新賦值 2ms
    TL0 = (65536 - 2000) % 256;
    Display(0, 8);       // 調用數碼管掃瞄
    TF1 = 0;
}

void main(void) {
    word i, j;
    InitUART();
    Init_Timer0();
    ES = 1;                  //打開串口中斷
    while (1) {
        if (rec_flag == 1) {
            for (j = 0;j < 8;j++) TempData[j] = 0; //清屏
            buf[head] = '\0';

            rec_flag = 0;
            head = 0;
        }
    }
}