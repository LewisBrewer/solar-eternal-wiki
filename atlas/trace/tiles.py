import cv2, json
im=cv2.imread('/mnt/user-data/uploads/1368724a-image.png')
S=json.load(open('systems_ocr.json'))
for i,s in enumerate(S):
    x,y=int(s['x']),int(s['y'])
    cv2.circle(im,(x,y),26,(0,0,255),3)
    cv2.putText(im,str(i),(x-30,y-30),cv2.FONT_HERSHEY_SIMPLEX,1.3,(0,0,255),4)
W,H=1750,1225
for r in range(4):
  for c in range(4):
    t=im[r*H:(r+1)*H, c*W:(c+1)*W]
    cv2.imwrite(f't{r}{c}.jpg', cv2.resize(t,(1400,980)), [cv2.IMWRITE_JPEG_QUALITY,85])
