import cv2, numpy as np, json, subprocess, sys, os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from mouth import plates, frame as mouth_frame
from screen import put_screen
W,H,FPS=1080,1920,30
IMG=os.environ.get('IMG','/mnt/project-files/film-moty/images/'); SCR=os.environ.get('SCR','/mnt/project-files/film-moty/ecrans/'); CLIPS=os.environ.get('CLIPS','clips/')
VOIX=os.environ.get('VOIX','voix/')
FONT=os.environ.get('FONT','fredoka-700.ttf')
GREEN=(124,194,66); ORANGE=(242,140,40); CREAM=(255,246,229); DARK=(30,58,30)
cfg=json.load(open(sys.argv[1],encoding='utf-8')); cfps=24; FMT=os.environ.get('FMT','9x16')

def audio_env(mp3):
    raw=subprocess.run(['ffmpeg','-v','quiet','-i',mp3,'-ac','1','-ar','16000','-f','s16le','-'],capture_output=True).stdout
    a=np.frombuffer(raw,np.int16).astype(float)/32768
    hop=16000//FPS; n=len(a)//hop
    e=np.array([np.sqrt(np.mean(a[i*hop:(i+1)*hop]**2)) for i in range(n)])
    e=e/(e.max()+1e-9)
    e=np.convolve(e,np.ones(3)/3,'same'); sm=e.copy()
    for i in range(1,len(e)): sm[i]=sm[i-1]+(0.6 if e[i]>sm[i-1] else 0.25)*(e[i]-sm[i-1])
    e=sm/(sm.max()+1e-9); return e, len(a)/16000

def text_img(txt, size=72, maxw=980):
    txt=txt.replace(' !','\u00a0!').replace(' ?','\u00a0?')
    f=ImageFont.truetype(FONT,size); lines=[]
    for para in txt.split('\n'):
        cur=''
        for w_ in para.split(' '):
            t=(cur+' '+w_).strip()
            if f.getlength(t)>maxw-80 and cur: lines.append(cur); cur=w_
            else: cur=t
        lines.append(cur)
    lh=int(size*1.2); tw=int(max(f.getlength(l) for l in lines))+80; th=lh*len(lines)+50
    im=Image.new('RGBA',(tw+20,th+20),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rounded_rectangle((10+6,10+8,tw+10+6,th+10+8),radius=34,fill=(*DARK,90))
    d.rounded_rectangle((10,10,tw+10,th+10),radius=34,fill=(*GREEN,235))
    y=10+25
    for l in lines:
        x=10+(tw-f.getlength(l))/2
        d.text((x,y),l,font=f,fill=CREAM,stroke_width=3,stroke_fill=(*DARK,255)); y+=lh
    return im

def bubble_img(txt,size=64,maxw=760):
    txt=txt.replace(' !','\u00a0!').replace(' ?','\u00a0?')
    f=ImageFont.truetype(FONT,size); lines=[]
    for para in txt.split('\n'):
        cur=''
        for w_ in para.split(' '):
            t=(cur+' '+w_).strip()
            if f.getlength(t)>maxw-70 and cur: lines.append(cur); cur=w_
            else: cur=t
        lines.append(cur)
    lh=int(size*1.2); tw=int(max(f.getlength(l) for l in lines))+70; th=lh*len(lines)+44
    im=Image.new('RGBA',(tw+20,th+60),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rounded_rectangle((10,10,tw+10,th+10),radius=40,fill=(255,255,255,245),outline=(*GREEN,255),width=6)
    d.polygon([(tw//2-20,th+8),(tw//2+20,th+8),(tw//2-30,th+50)],fill=(255,255,255,245))
    d.line([(tw//2-20,th+10),(tw//2-30,th+50),(tw//2+20,th+10)],fill=(*GREEN,255),width=6)
    y=10+22
    for l in lines:
        d.text((10+(tw-f.getlength(l))/2,y),l,font=f,fill=(40,70,30)); y+=lh
    return im

def paste(canvas, im, cx, cy, scale=1.0, alpha=1.0):
    if scale<=0.01 or alpha<=0.01: return
    if abs(scale-1)>0.01: im=im.resize((max(1,int(im.width*scale)),max(1,int(im.height*scale))),Image.LANCZOS)
    if alpha<1: a=im.split()[3].point(lambda p:int(p*alpha)); im.putalpha(a)
    canvas.alpha_composite(im,(int(cx-im.width/2),int(cy-im.height/2)))

def pop(t):  # 0..1 over 0.25s -> overshoot
    if t>=1: return 1.0
    return 1+ 1.70158*1.3*(t-1)**3 + 1.70158*(t-1)**2 if False else (0.6+0.48*math.sin(t*math.pi*0.75)/math.sin(math.pi*0.75)) if t<0.8 else 1.08-0.08*(t-0.8)/0.2

def cover(img,w,h):
    s=max(w/img.shape[1],h/img.shape[0]); return cv2.resize(img,(int(img.shape[1]*s+0.5),int(img.shape[0]*s+0.5)),interpolation=cv2.INTER_LANCZOS4)

def camera(src, z, cx, cy, w=W, h=H):
    # src already covers WxH; zoom z around normalized center (cx,cy)
    sh,sw=src.shape[:2]; s=z*max(w/sw,h/sh)
    tx=w/2-cx*sw*s; ty=h/2-cy*sh*s
    tx=min(0,max(w-sw*s,tx)); ty=min(0,max(h-sh*s,ty))
    M=np.float32([[s,0,tx],[0,s,ty]])
    return cv2.warpAffine(src,M,(w,h),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)


APPC={}
def app_screen(f, w):
    k=(f,w)
    if k not in APPC:
        if not os.path.exists(SCR+f): print('ecran absent, remplace:',f); f2='missions2.png'
        else: f2=f
        im=Image.open(SCR+f2).convert('RGB')
        if im.width/im.height>0.6: im=im.crop((370,120,1680,2732))   # iPad
        else: im=im.crop((0,int(im.height*0.055),im.width,im.height))  # iPhone: no status bar
        h=int(w*im.height/im.width); APPC[k]=im.resize((w,h),Image.LANCZOS)
    return APPC[k]
def ease(x): x=max(0,min(1,x)); return 1-(1-x)**3
def appdemo(s, t, clipf, cfps, bgsrc):
    # background: blurred plan, slow zoom, darkened
    p=t/s['dur']; fr=camera(bgsrc,1.04+0.12*p,0.5,0.5)
    canvas=Image.fromarray(cv2.cvtColor(fr,cv2.COLOR_BGR2RGB)).convert('RGBA')
    PW=s.get('pw',560); scr=None; seq=s['app']
    cur=[x for x in seq if x[0]<=t][-1]; idx=seq.index(cur)
    img=app_screen(cur[1],PW)
    if idx>0 and t-cur[0]<0.3:   # slide transition from previous screen
        q=ease((t-cur[0])/0.3); prev=app_screen(seq[idx-1][1],PW)
        comp=Image.new('RGB',img.size,(255,255,255)); comp.paste(prev,(int(-PW*q),0)); comp.paste(img,(int(PW*(1-q)),0)); img=comp
    PH=img.height; BZ=26
    phone=Image.new('RGBA',(PW+2*BZ,PH+2*BZ),(0,0,0,0)); d=ImageDraw.Draw(phone)
    d.rounded_rectangle((0,0,PW+2*BZ-1,PH+2*BZ-1),radius=80,fill=(22,22,28,255))
    m=Image.new('L',(PW,PH),0); ImageDraw.Draw(m).rounded_rectangle((0,0,PW-1,PH-1),radius=58,fill=255)
    phone.paste(img,(BZ,BZ),m)
    d=ImageDraw.Draw(phone)
    # check badges on done missions
    for (tt,x,y) in s.get('checks',[]):
        if t>=tt:
            q=min(1,(t-tt)/0.25); r=int(46*pop(q)); cx_,cy_=BZ+x*PW,BZ+y*PH
            d.ellipse((cx_-r,cy_-r,cx_+r,cy_+r),fill=(76,175,80,255),outline=(255,255,255,255),width=6)
            if r>20: d.line([(cx_-r*0.45,cy_),(cx_-r*0.1,cy_+r*0.35),(cx_+r*0.5,cy_-r*0.35)],fill=(255,255,255,255),width=10)
    # taps (finger ripple)
    for (tt,x,y) in s.get('taps',[]):
        dt=t-tt
        if -0.35<=dt<0.45:
            cx_,cy_=BZ+x*PW,BZ+y*PH
            if dt<0: a_=int(200*(1+dt/0.35)); r=40
            else: a_=int(200*(1-dt/0.45)); r=40+dt*160
            d.ellipse((cx_-r,cy_-r,cx_+r,cy_+r),outline=(255,255,255,max(0,a_)),width=8)
            if dt<0.15: d.ellipse((cx_-30,cy_-30,cx_+30,cy_+30),fill=(255,255,255,150))
    ent=ease(t/0.45) if s.get('phone_in',True) else 1
    sc_=0.95+0.08*p
    py=s.get('phone_y',1060)+(1-ent)*900
    paste(canvas,phone,W/2,py,sc_)
    # Moty talking bubble (circle cut from a talking clip)
    va=s.get('voice_at',0.15); ve=s.get('_ve',s['dur'])
    if clipf is not None and va<=t<ve+0.2:
        n=len(clipf); k=int(t*cfps); k=k%(2*n-2) if n>1 else 0; k=k if k<n else 2*n-2-k   # ping-pong
        f_=clipf[k]; hh,ww=f_.shape[:2]; cxn,cyn,dn=s.get('moty_crop',[0.52,0.54,0.5])
        D=int(dn*ww); x0=int(cxn*ww-D/2); y0=int(cyn*hh-D/2)
        x0=max(0,min(ww-D,x0)); y0=max(0,min(hh-D,y0))
        crop=cv2.cvtColor(f_[y0:y0+D,x0:x0+D],cv2.COLOR_BGR2RGB); DS=s.get('moty_d',290)
        face=Image.fromarray(crop).resize((DS,DS),Image.LANCZOS)
        circ=Image.new('RGBA',(DS+24,DS+24),(0,0,0,0)); dd=ImageDraw.Draw(circ)
        dd.ellipse((0,0,DS+23,DS+23),fill=(*GREEN,255)); mm=Image.new('L',(DS,DS),0); ImageDraw.Draw(mm).ellipse((0,0,DS-1,DS-1),fill=255)
        circ.paste(face,(12,12),mm)
        q=min(1,(t-va)/0.3); mx,my=s.get('moty_xy',[175,1500])
        scl=pop(q) if t<ve else 1-ease((t-ve)/0.2)
        paste(canvas,circ,mx,my,scl)
    return canvas

shots=cfg['shots']; frames_total=sum(int(s['dur']*FPS) for s in shots)
out=sys.argv[2]
ff=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','18','-preset','medium','-pix_fmt','yuv420p',out+'_v.mp4'],stdin=subprocess.PIPE)
audio_events=[]; t0=0.0; prev_last=None; last_ve_abs=None
for si,s in enumerate(shots):
    base=cv2.imread(IMG+s['img']) if s.get('img') else None
    bgsrc=None
    if s.get('app'):
        bgsrc=cv2.GaussianBlur(cover(base,W,H),(0,0),18); bgsrc=(bgsrc*0.72).astype(np.uint8)
    clipf=None
    if s.get('clip'):
        cap=cv2.VideoCapture(CLIPS+s['clip']); clipf=[]; cfps=cap.get(cv2.CAP_PROP_FPS) or 24
        while True:
            ok,fr_=cap.read()
            if not ok: break
            clipf.append(fr_)
        cap.release()
        cst=s.get('clip_start',0.0); avail=len(clipf)/cfps-cst
    # voice
    env=None
    if s.get('voice'):
        vs=s.get('voice_at',0.25)
        env,dur=audio_env(VOIX+s['voice']); audio_events.append((t0+vs,VOIX+s['voice']))
        idx=np.where(env>0.08)[0]; s['_ve']=vs+(idx[-1]+1)/FPS
        if s.get('auto_dur') is not None: s['dur']=round(s['_ve']+s['auto_dur'],3)
        print('shot',si,'voice_end',round(s['_ve'],2),'dur',s['dur'])
        last_ve_abs=t0+s['_ve']
    if s.get('wait_voice') is not None and last_ve_abs is not None:
        s['dur']=round(max(s['dur'], last_ve_abs-t0+s['wait_voice']),3); print('shot',si,'waits voice, dur',s['dur'])
        tag=f"m{si}"
        if s.get('mouth'): plates(IMG+s['img'],tuple(s['mouth']),tag)
    if clipf is not None:
        cspeed=s.get('clip_speed', min(1.0, avail/s['dur']))
        if not s.get('app') and s.get('voice') and avail/cspeed < s['_ve']: print('WARN clip shorter than voice', si)
    n=int(s['dur']*FPS)
    if s.get('voice2'):
        env2,_=audio_env(VOIX+s['voice2']); audio_events.append((t0+s['voice2_at'],VOIX+s['voice2']))
    caption_cache={}
    for i in range(n):
        t=i/FPS
        img=base
        if clipf is not None and not s.get('app'):
            img=clipf[min(len(clipf)-1,int((cst+t*cspeed)*cfps))]
        if env is not None:
            a=0.0; k=int((t-s.get('voice_at',0.25))*FPS)
            if 0<=k<len(env): a=env[k]
            if s.get('voice2'):
                k2=int((t-s['voice2_at'])*FPS)
                if 0<=k2<len(env2): a=max(a,env2[k2])
            inwin=0<=k<len(env)
            post=(k-len(env))/FPS if k>=len(env) else -1
            if s.get('mouth') and inwin: img=mouth_frame(IMG+s['img'],tag,0.3+0.7*min(1,a*1.3))
            elif s.get('mouth') and 0<=post<0.2: img=mouth_frame(IMG+s['img'],tag,0.3+0.7*post/0.2)
        # screens: list of [start,end,file,quad,occl]
        for sc in s.get('screens',[]):
            if sc[0]<=t<sc[1]:
                key=sc[2]
                shot=caption_cache.setdefault(key,cv2.imread(SCR+sc[2]))
                img=put_screen(img,shot,sc[3],tuple(sc[4]) if sc[4] else None)
        src=cover(img,W,H) if not s.get('app') or i==0 else src
        p=t/s['dur']; e=p*p*(3-2*p)
        z=s['z0']+(s['z1']-s['z0'])*e; cx=s['c0'][0]+(s['c1'][0]-s['c0'][0])*e; cy=s['c0'][1]+(s['c1'][1]-s['c0'][1])*e
        if s.get('punch') and t<0.5: z*=1+0.12*math.sin(t/0.5*math.pi/2)
        fr=camera(src,z,cx,cy)
        if s.get('sharpen'): fr=cv2.addWeighted(fr,1.4,cv2.GaussianBlur(fr,(0,0),2),-0.4,0)
        if s.get('app'):
            fr=cv2.cvtColor(np.array(appdemo(s,t,clipf,cfps,bgsrc).convert('RGB')),cv2.COLOR_RGB2BGR)
        # transition in: whip from previous last frame
        tr=s.get('trans','cut'); TD=0.25
        if prev_last is not None and t<TD and tr!='cut':
            q=t/TD
            if tr=='whip':
                sh_=int(W*(1-q)); a_=np.roll(prev_last,-int(W*q),axis=1)
                mix=np.concatenate([prev_last[:,int(W*q):],fr[:,:int(W*q)]],axis=1) if q<1 else fr
                fr=cv2.blur(mix,(int(60*(1-abs(2*q-1)))+1,1))
            elif tr=='fadewhite':
                wq=1-abs(2*q-1); fr=cv2.addWeighted(prev_last if q<0.5 else fr,1-wq*0.85,np.full_like(fr,255),wq*0.85,0)
            elif tr=='zoom':
                zz=1+0.3*q; pz=camera(prev_last,zz,0.5,0.5)
                fr=cv2.addWeighted(pz,1-q,fr,q,0)
        if s.get('flash') and abs(t-s['flash'])<0.05:
            fr=cv2.addWeighted(fr,0.6,np.full_like(fr,255),0.4,0)
        # overlays
        canvas=Image.fromarray(cv2.cvtColor(fr,cv2.COLOR_BGR2RGB)).convert('RGBA')
        for ov in s.get('texts',[]):
            st,en,txt,y=ov[0],ov[1],ov[2],ov[3]; kind=ov[4] if len(ov)>4 else 'banner'
            if en<0: en=s['dur']+en
            if st<=t<en:
                im=caption_cache.get(('t',txt,kind))
                if im is None: im=text_img(txt) if kind=='banner' else bubble_img(txt); caption_cache[('t',txt,kind)]=im
                q=(t-st)/0.25; sc_=pop(min(q,1)); al=min(1,q*3)
                if en-t<0.15: al=(en-t)/0.15; sc_=1
                x=ov[5] if len(ov)>5 else W/2
                paste(canvas,im,x,y,sc_,al)
        for st_ in s.get('stars',[]):
            pass
        if s.get('starfx'):
            ts=t-s['starfx']
            if 0<=ts<2.2:
                d=ImageDraw.Draw(canvas); rng=np.random.default_rng(7)
                for k in range(22):
                    ang=rng.uniform(0,2*math.pi); sp=rng.uniform(250,650); x0,y0=s['starxy']
                    x=x0+math.cos(ang)*sp*ts; y=y0+math.sin(ang)*sp*ts+300*ts*ts; r=rng.uniform(14,30)*(1-ts/2.4)
                    pts=[(x+r*math.cos(math.pi/2+j*math.pi/5)*(1 if j%2==0 else 0.45), y-r*math.sin(math.pi/2+j*math.pi/5)*(1 if j%2==0 else 0.45)) for j in range(10)]
                    d.polygon(pts,fill=(255,205,40,int(255*(1-ts/2.2))),outline=(255,255,200,200))
        if s.get('pip') and t>=s['pip'][0]:
            ph=caption_cache.get('phone')
            if ph is None:
                shot=Image.open(SCR+s['pip'][1]).convert('RGB'); pw=s['pip'][3] if len(s['pip'])>3 else 430; phh=int(pw*shot.height/shot.width)
                shot=shot.resize((pw,phh),Image.LANCZOS)
                ph=Image.new('RGBA',(pw+40,phh+40),(0,0,0,0)); d=ImageDraw.Draw(ph)
                d.rounded_rectangle((0,0,pw+39,phh+39),radius=60,fill=(25,25,30,255))
                m=Image.new('L',(pw,phh),0); ImageDraw.Draw(m).rounded_rectangle((0,0,pw-1,phh-1),radius=44,fill=255)
                ph.paste(shot,(20,20),m); caption_cache['phone']=ph
            q=min(1,(t-s['pip'][0])/0.45); q=1-(1-q)**3
            x=W+ph.width/2-(ph.width+40)*q*1.0 - 0
            paste(canvas,ph.rotate(-6,expand=True,resample=Image.BICUBIC),W/2+110+ (1-q)*700, s['pip'][2])
        if s.get('cta') is not None and t>=s['cta']:
            q=1 if s.get('cta_static') else min(1,(t-s['cta'])/0.35)
            logo=caption_cache.get('logo')
            if logo is None:
                logo=Image.new('RGBA',(900,420),(0,0,0,0)); d=ImageDraw.Draw(logo)
                f1=ImageFont.truetype(FONT,104); f2=ImageFont.truetype(FONT,60)
                for i,ln in enumerate(['Mon tableau','de motivation']):
                    tw=f1.getlength(ln); d.text(((900-tw)/2,6+i*118),ln,font=f1,fill=(*GREEN,255),stroke_width=8,stroke_fill=(255,255,255,255))
                l2='App Store  ·  Google Play'; d.rounded_rectangle((50,282,850,402),radius=60,fill=(*ORANGE,255))
                d.text(((900-f2.getlength(l2))/2,304),l2,font=f2,fill=(255,255,255))
                caption_cache['logo']=logo
            paste(canvas,logo,W/2,s.get('cta_y',330),pop(q),min(1,q*2))
        fr=cv2.cvtColor(np.array(canvas.convert('RGB')),cv2.COLOR_RGB2BGR)
        ff.stdin.write(fr.tobytes())
    prev_last=fr; t0+=n/FPS
ff.stdin.close(); ff.wait()
# audio mix
total=t0
inputs=[];flt=[]
for k,(at,f) in enumerate(audio_events):
    inputs+=['-i',f]; flt.append(f'[{k+1}:a]adelay={int(at*1000)}|{int(at*1000)}[a{k}]')
if audio_events:
    mix=''.join(f'[a{k}]' for k in range(len(audio_events)))+f'amix=inputs={len(audio_events)}:normalize=0,apad,atrim=0:{total},loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]'
    subprocess.run(['ffmpeg','-y','-v','error','-i',out+'_v.mp4',*inputs,'-filter_complex',';'.join(flt+[mix]),'-map','0:v','-map','[aout]','-c:v','copy','-ac','2','-c:a','aac','-b:a','160k','-movflags','+faststart',out+'.mp4'],check=True)
else:
    subprocess.run(['ffmpeg','-y','-v','error','-i',out+'_v.mp4','-f','lavfi','-i','anullsrc=r=44100:cl=stereo','-shortest','-c:v','copy','-c:a','aac',out+'.mp4'],check=True)
print('done',total)
