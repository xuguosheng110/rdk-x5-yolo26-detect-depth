#!/usr/bin/env python3
"""Generate public reference QR codes with OpenCV (no board IP encoded)."""
from pathlib import Path
import cv2
ROOT=Path(__file__).resolve().parents[1]
URLS=[
 'https://github.com/xuguosheng110/rdk-x5-yolo26-detect-depth',
 'https://forum.d-robotics.cc/t/topic/35680',
 'https://github.com/D-Robotics/rdk_model_zoo/tree/rdk_x5',
]
encoder=cv2.QRCodeEncoder_create()
for index,url in enumerate(URLS,1):
 qr=encoder.encode(url)
 qr=cv2.copyMakeBorder(qr,4,4,4,4,cv2.BORDER_CONSTANT,value=255)
 qr=cv2.resize(qr,None,fx=6,fy=6,interpolation=cv2.INTER_NEAREST)
 assert cv2.imwrite(str(ROOT/'web'/f'qr{index}.png'),qr)
