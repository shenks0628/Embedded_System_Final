#include <reg52.h> //包含標頭檔，一般情況不需要改動，標頭檔包含特殊功能寄存器的定義
#include "uart.h"
typedef unsigned char byte;
typedef unsigned int  word;
unsigned int max = 20;
byte buf[20];
byte head = 0;
byte get_0d = 0;
byte rec_flag = 0;
/*------------------------------------------------
/*------------------------------------------------
                    串口初始化
------------------------------------------------*/
void InitUART  (void)
{
    SCON  = 0x50;		        // SCON: 模式 1, 8-bit UART, 使能接收  
    TMOD |= 0x20;               // TMOD: timer 1, mode 2, 8-bit 重裝
    TH1   = 0xFD;               // TH1:  重裝值 9600 串列傳輸速率 晶振 11.0592MHz  
    TR1   = 1;                  // TR1:  timer 1 打開                         
    EA    = 1;                  //打開總中斷
}
/*------------------------------------------------
                    發送一個位元組
------------------------------------------------*/
void UART_SendByte(unsigned char dat)
{
 	SBUF = dat;
 	while(!TI);
    	TI = 0;
}

/*------------------------------------------------
                    發送一個字串
------------------------------------------------*/
void UART_SendStr(unsigned char *s)
{
	while(*s!='\0')// \0 表示字串結束標誌，通過檢測是否字串末尾
  	{
		UART_SendByte(*s);
		if(*s=='\n')	//若結尾是換行符號也跳出
			break;
  		s++;
  	}
}


/*------------------------------------------------
                     串口中斷程式
------------------------------------------------*/
void UART_SER (void) interrupt 4 //串列中斷服務程式
{
    // 0x0d:'\r' 0x0a:'\n'
    unsigned char tmp;              //定義臨時變數 
    if (RI) {                       //判斷是接收中斷產生
	  	RI=0;                      //標誌位元清零
	  	tmp=SBUF;                 //讀入緩衝區的值
        if (get_0d == 0) {
            if (tmp == 0x0d) get_0d = 1;
            else {
                buf[head] = tmp;
                head++;
                if (head == MAX) head = 0;
            }
        }
        else if (get_0d == 1) {
            if (tmp != 0x0a) {
                head = 0;
                get_0d = 0;
            }
            else {
                rec_flag = 1;
                get_0d = 0;
            }
        }
    }
}