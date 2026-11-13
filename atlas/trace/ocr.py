import cv2, json, pytesseract, numpy as np
im=cv2.imread('/mnt/user-data/uploads/1368724a-image.png')
g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
S=json.load(open('systems_raw.json'))
for s in S:
    xs=[p[0] for p in s['pts']]; x0=int(max(xs))+12; y=int(s['y'])
    crop=g[max(0,y-34):y+34, x0:x0+900]
    # binarise: dark text
    b=np.where(crop<100,0,255).astype(np.uint8)
    b=cv2.copyMakeBorder(b,20,20,20,20,cv2.BORDER_CONSTANT,value=255)
    t=pytesseract.image_to_string(b,config='--psm 7').strip()
    s['ocr']=t
    print(round(s['x']),round(s['y']),s['stars'],repr(t))
json.dump(S,open('systems_ocr.json','w'))
