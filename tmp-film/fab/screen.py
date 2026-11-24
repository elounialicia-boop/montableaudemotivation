import cv2, numpy as np
def put_screen(base, shot, quad, occl_box=None, glare=0.06, radius=14):
    """base: BGR image; shot: BGR screenshot; quad: TL,TR,BR,BL in base coords."""
    h,w=shot.shape[:2]
    # rounded corners on the screenshot
    src=np.float32([[0,0],[w,0],[w,h],[0,h]]); dst=np.float32(quad)
    M=cv2.getPerspectiveTransform(src,dst)
    warped=cv2.warpPerspective(shot,M,(base.shape[1],base.shape[0]),flags=cv2.INTER_AREA)
    m=np.zeros((h,w),np.uint8); r=int(radius*w/ (dst[1][0]-dst[0][0]))
    cv2.rectangle(m,(r,0),(w-r,h),255,-1); cv2.rectangle(m,(0,r),(w,h-r),255,-1)
    for cx,cy in ((r,r),(w-r,r),(r,h-r),(w-r,h-r)): cv2.circle(m,(cx,cy),r,255,-1)
    wm=cv2.warpPerspective(m,M,(base.shape[1],base.shape[0]))
    wm=cv2.GaussianBlur(wm,(3,3),0).astype(float)/255
    # keep occluders (finger) from base
    if occl_box is not None:
        x0,y0,x1,y1=occl_box
        b=base[y0:y1,x0:x1].astype(int); B,G,R=b[...,0],b[...,1],b[...,2]
        skin=((R-B>35)&(G>B-5)&(G<R)&(R>90))|((B<90)&(G<90)&(R<90))
        sk=np.zeros(base.shape[:2],np.uint8); sk[y0:y1,x0:x1]=skin*255
        sk=cv2.morphologyEx(sk,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
        sk=cv2.GaussianBlur(sk,(5,5),0).astype(float)/255
        wm=wm*(1-sk)
    # slight screen glow + glare
    warped=warped.astype(float)*0.97+ 255*glare
    out=base.astype(float)*(1-wm[...,None])+warped*wm[...,None]
    return np.clip(out,0,255).astype(np.uint8)
if __name__=='__main__':
    base=cv2.imread('/mnt/project-files/film-moty/images/plan4.jpg')
    shot=cv2.imread('/mnt/project-files/film-moty/ecrans/missions.png')
    out=put_screen(base,shot,[(407,558),(580,552),(612,845),(433,862)],occl_box=(505,690,615,800))
    cv2.imwrite('p4_screen.jpg',out)
    cv2.imwrite('p4_crop.jpg',out[480:900,330:700])
