import cv2, numpy as np, json
im=cv2.imread('/mnt/user-data/uploads/1368724a-image.png')
g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).astype(np.int16)
bg=cv2.blur(g.astype(np.uint8),(61,61)).astype(np.int16)
mask=((bg-g)>35).astype(np.uint8)*255
k=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9))
op=cv2.morphologyEx(mask,cv2.MORPH_OPEN,k)
n,lab,st,cen=cv2.connectedComponentsWithStats(op)
S=json.load(open('systems_ocr.json'))
allpts=[p for s in S for p in s['pts']]
extra=[]
for i in range(1,n):
    x,y,w,h,a=st[i]
    if 60<a<600 and 0.6<w/h<1.6:
        cx,cy=cen[i]
        if min((cx-p[0])**2+(cy-p[1])**2 for p in allpts)>20**2:
            extra.append((round(cx),round(cy),int(a),int(g[int(cy),int(cx)])))
print(len(extra))
for e in extra: print(e)
json.dump(extra,open('extra.json','w'))
