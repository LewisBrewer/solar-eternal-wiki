import cv2, numpy as np, json, colorsys
from collections import Counter
im=cv2.imread('/mnt/user-data/uploads/1368724a-image.png')
S=json.load(open('systems_named.json'))
H,W=im.shape[:2]
yy,xx=np.mgrid[-80:81,-80:81]; r=np.hypot(xx,yy); ring=(r>35)&(r<80)
for s in S:
    x,y=int(s['x']),int(s['y'])
    p=im[max(0,y-80):y+81, max(0,x-80):x+81]
    m=ring[:p.shape[0],:p.shape[1]]
    px=p[m]; px=px[px.sum(1)>200]
    b,g,rr=np.median(px,0)/255
    h,l,sat=colorsys.rgb_to_hls(rr,g,b)
    h*=360
    if sat<0.12: c='none'
    elif 190<=h<=235: c='usr'
    elif 160<=h<190: c='voor'
    elif 90<=h<160: c='maweer'
    elif 260<=h<=320: c='fevarian'
    elif h>320 or h<20: c='pink'
    else: c='?'
    s['col']=[int(rr*255),int(g*255),int(b*255)]; s['hue']=round(h); s['sat']=round(sat,2); s['region2235']=c
print(Counter(s['region2235'] for s in S))
for s in S:
    if s['region2235'] in('?','pink') or 0.08<s['sat']<0.2: print(s['name'],s['hue'],s['sat'],s['region2235'])
json.dump(S,open('systems_named.json','w'),indent=0)
