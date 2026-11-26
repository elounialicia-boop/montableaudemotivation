import cv2, numpy as np, sys
from PIL import Image
# make "mouth plates": open (original) and closed (inpainted mouth with a smile line)
def plates(path, box, out):
    im=cv2.imread(path)
    x0,y0,x1,y1=box
    roi=im[y0:y1,x0:x1]
    hsv=cv2.cvtColor(roi,cv2.COLOR_BGR2HSV)
    # mouth interior = not green (hue outside 30-60 or low saturation dark)
    h,s,v=cv2.split(hsv)
    green=((h>25)&(h<55)&(s>60)).astype(np.uint8)
    mask=(1-green)*255
    mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
    # keep largest component
    n,l,st,_=cv2.connectedComponentsWithStats(mask)
    k=1+np.argmax(st[1:,4]); mask=((l==k)*255).astype(np.uint8)
    mask=cv2.dilate(mask,np.ones((9,9),np.uint8))
    full=np.zeros(im.shape[:2],np.uint8); full[y0:y1,x0:x1]=mask
    closed=cv2.inpaint(im,full,9,cv2.INPAINT_TELEA)
    ys,xs=np.where(full>0)
    np.save(out+'_mbox.npy',np.array([xs.min(),ys.min(),xs.max(),ys.max()]))
    cv2.imwrite(out+'_closed.png',closed); cv2.imwrite(out+'_mask.png',full)
    return closed,full
def frame(path, out, a):
    im=cv2.imread(path); closed=cv2.imread(out+'_closed.png'); m=cv2.imread(out+'_mask.png',0)
    x0,y0,x1,y1=np.load(out+'_mbox.npy')
    h=y1-y0+1; nh=max(4,int(h*a))
    patch=im[y0:y1+1,x0:x1+1]; mp=m[y0:y1+1,x0:x1+1]
    patch=cv2.resize(patch,(x1-x0+1,nh)); mp=cv2.resize(mp,(x1-x0+1,nh))
    mp=cv2.GaussianBlur(mp,(7,7),0)/255.0
    res=closed.copy(); reg=res[y0:y0+nh,x0:x1+1].astype(float)
    res[y0:y0+nh,x0:x1+1]=(reg*(1-mp[...,None])+patch*mp[...,None]).astype(np.uint8)
    return res
if __name__=='__main__':
    p=sys.argv[1]; box=tuple(map(int,sys.argv[2:6])); out=sys.argv[6]
    plates(p,box,out)
    for a in (1.0,0.6,0.25):
        cv2.imwrite(f'{out}_a{a}.jpg',frame(p,out,a))
