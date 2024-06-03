#include <reg52.h> // 包含標頭檔，一般情況不需要改動，標頭檔包含特殊功能寄存器的定義
#include "delay.h"
#include "keyscan.h"

#define KeyPort P1 // 定義鍵盤埠

unsigned char KeyScan(void)  // 鍵盤掃瞄函數，使用行列逐級掃瞄法
{
    unsigned char Val;
    KeyPort = 0xf0; // 高四位置高，低四位拉低
    if (KeyPort != 0xf0) // 表示有按鍵按下
    {
        DelayMs(10); // 去抖
        if (KeyPort != 0xf0) { // 表示有按鍵按下
            KeyPort = 0xfe; // 檢測第一行
            if (KeyPort != 0xfe) {
                Val = KeyPort & 0xf0;
                Val += 0x0e;
                while (KeyPort != 0xfe);
                DelayMs(10); // 去抖
                while (KeyPort != 0xfe);
                return Val;
            }
            KeyPort = 0xfd; // 檢測第二行
            if (KeyPort != 0xfd) {
                Val = KeyPort & 0xf0;
                Val += 0x0d;
                while (KeyPort != 0xfd);
                DelayMs(10); // 去抖
                while (KeyPort != 0xfd);
                return Val;
            }
            KeyPort = 0xfb; // 檢測第三行
            if (KeyPort != 0xfb) {
                Val = KeyPort & 0xf0;
                Val += 0x0b;
                while (KeyPort != 0xfb);
                DelayMs(10); // 去抖
                while (KeyPort != 0xfb);
                return Val;
            }
            KeyPort = 0xf7; // 檢測第四行
            if (KeyPort != 0xf7) {
                Val = KeyPort & 0xf0;
                Val += 0x07;
                while (KeyPort != 0xf7);
                DelayMs(10); // 去抖
                while (KeyPort != 0xf7);
                return Val;
            }
        }
    }
    return 0xff;
}

unsigned char KeyPro(void) {
    switch (KeyScan()) {
    case 0x7e:return 0; break; // 0 按下相應的鍵顯示相對應的碼值
    case 0x7d:return 1; break; // 1
    case 0x7b:return 2; break; // 2
    case 0x77:return 3; break; // 3
    case 0xbe:return 4; break; // 4
    case 0xbd:return 5; break; // 5
    case 0xbb:return 6; break; // 6
    case 0xb7:return 7; break; // 7
    case 0xde:return 8; break; // 8
    case 0xdd:return 9; break; // 9
    case 0xdb:return 10; break; // a
    case 0xd7:return 11; break; // 
    case 0xee:return 12; break; // 
    case 0xed:return 13; break; // 
    case 0xeb:return 14; break; // 
    case 0xe7:return 15; break; // 準備
    default:return 0xff; break;
    }
}

