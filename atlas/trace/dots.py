import cv2, numpy as np, json
im=cv2.imread('/mnt/user-data/uploads/1368724a-image.png')
g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
mask=(g<60).astype(np.uint8)*255
k=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9))
op=cv2.morphologyEx(mask,cv2.MORPH_OPEN,k)
n,lab,st,cen=cv2.connectedComponentsWithStats(op)
dots=[]
for i in range(1,n):
    x,y,w,h,a=st[i]
    if 60<a<600 and 0.6<w/h<1.6:
        dots.append((float(cen[i][0]),float(cen[i][1]),int(a)))
print(len(dots))
# cluster within 45px
used=[False]*len(dots); systems=[]
for i,d in enumerate(dots):
    if used[i]: continue
    grp=[d]; used[i]=True
    for j in range(i+1,len(dots)):
        if not used[j] and any((dots[j][0]-q[0])**2+(dots[j][1]-q[1])**2<45**2 for q in grp):
            grp.append(dots[j]); used[j]=True
    systems.append({'x':sum(p[0] for p in grp)/len(grp),'y':sum(p[1] for p in grp)/len(grp),'stars':len(grp),'pts':[(p[0],p[1]) for p in grp]})
print(len(systems))
from collections import Counter; print(Counter(s['stars'] for s in systems)); print(Counter(d[2]//50*50 for d in dots))
json.dump(systems,open('systems_raw.json','w'))
