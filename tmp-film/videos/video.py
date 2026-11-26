# Video Moty d'un carrousel : python video.py <id> <dossier_voix> <sortie.mp4>
import cv2, numpy as np, json, subprocess, sys, os, math, wave
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE)
from mouth import plates, frame as mouth_frame
W,H,FPS=1080,1920,30
CID,VOIX,OUT=sys.argv[1],sys.argv[2],sys.argv[3]
BRIEF=os.environ.get('BRIEF','/mnt/project-files/carrousels-astuces/BRIEF-VIDEOS.json')
MOTY=os.environ.get('MOTY','/mnt/project-files/livre-joue-avec-moty/fabrication/assets3d/bras.png')
FONT=os.environ.get('FONT',os.path.join(HERE,'..','fab','fredoka-700.ttf'))
TMP=os.environ.get('TMP_DIR','/tmp/vidmoty'); os.makedirs(TMP,exist_ok=True)
brief={c['id']:c for c in json.load(open(BRIEF,encoding='utf-8'))}[CID]

def ease_out_back(x):
    x=max(0,min(1,x)); c1=1.4; c3=c1+1; return 1+c3*(x-1)**3+c1*(x-1)**2
def ease(x): x=max(0,min(1,x)); return 1-(1-x)**3

def audio_env(mp3):
    raw=subprocess.run(['ffmpeg','-v','quiet','-i',mp3,'-ac','1','-ar','16000','-f','s16le','-'],capture_output=True).stdout
    a=np.frombuffer(raw,np.int16).astype(float)/32768; hop=16000//FPS; n=len(a)//hop
    e=np.array([np.sqrt(np.mean(a[i*hop:(i+1)*hop]**2)) for i in range(n)]); e=e/(e.max()+1e-9)
    e=np.convolve(e,np.ones(3)/3,'same'); sm=e.copy()
    for i in range(1,len(e)): sm[i]=sm[i-1]+(0.6 if e[i]>sm[i-1] else 0.3)*(e[i]-sm[i-1])
    return sm/(sm.max()+1e-9)

# ---- talking Moty sprites (mouth opening levels) ----
MW=520
src=Image.open(MOTY).convert('RGBA'); alpha=src.split()[3]
rgb=Image.new('RGB',src.size,(255,255,255)); rgb.paste(src,(0,0),src); rgb.save(TMP+'/moty_rgb.png')
plates(TMP+'/moty_rgb.png',(380,390,730,620),TMP+'/mo')
LEV=[0.16+0.84*i/10 for i in range(11)]; SPR=[]
for a in LEV:
    f=cv2.cvtColor(mouth_frame(TMP+'/moty_rgb.png',TMP+'/mo',a),cv2.COLOR_BGR2RGB)
    im=Image.fromarray(f).convert('RGBA'); im.putalpha(alpha)
    h=int(MW*im.height/im.width); SPR.append(im.resize((MW,h),Image.LANCZOS))
MH=SPR[0].height

# ---- sfx ----
SR=44100
def _w(name,x,peak):
    x=x/(np.abs(x).max()+1e-9)*peak; fn=os.path.join(TMP,name+'.wav')
    with wave.open(fn,'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x*32767).astype(np.int16).tobytes())
    return fn
def _t(d): return np.arange(int(SR*d))/SR
r=np.random.default_rng(3)
t_=_t(0.3); f_=300+2700*(t_/0.3)**1.5
WHOOSH=_w('whoosh',np.convolve(r.standard_normal(len(t_))*np.sin(2*np.pi*np.cumsum(f_)/SR),np.ones(6)/6,'same')*np.sin(np.pi*t_/0.3)**2,0.13)
t_=_t(0.08); POP=_w('pop',np.sin(2*np.pi*np.cumsum(500+600*t_/0.08)/SR)*np.exp(-t_/0.025),0.2)
t_=_t(0.7); DING=_w('ding',(np.sin(2*np.pi*1568*t_)+0.7*np.sin(2*np.pi*2093*t_))*np.exp(-t_/0.18),0.17)

# ---- slides ----
SW=1000; SH=1250; SY=150   # slide box
slides=[]; t0=0.6; audio=[]
for i,d in enumerate(brief['diapos']):
    im=Image.open(d['image']).convert('RGB')
    bg=im.getpixel((8,8))
    k=f"{CID}-{i+1:02d}"; mp3=os.path.join(VOIX,k+'.mp3')
    env=audio_env(mp3); idx=np.where(env>0.08)[0]; vend=(idx[-1]+1)/FPS
    va=0.35; dur=max(2.4,va+vend+0.55)
    if i==len(brief['diapos'])-1: dur+=1.2
    slides.append(dict(im=im.resize((SW,SH),Image.LANCZOS),bg=bg,env=env,va=va,vend=va+vend,t0=t0,dur=dur))
    audio.append((t0+va,mp3)); audio.append((t0,WHOOSH if i else POP))
    t0+=dur
total=t0
def rounded(im,rad=46):
    m=Image.new('L',im.size,0); ImageDraw.Draw(m).rounded_rectangle((0,0,im.width-1,im.height-1),radius=rad,fill=255)
    o=im.convert('RGBA'); o.putalpha(m); return o
for s in slides: s['card']=rounded(s['im'])
shadow=Image.new('RGBA',(SW+80,SH+80),(0,0,0,0)); ImageDraw.Draw(shadow).rounded_rectangle((40,48,SW+40,SH+48),radius=46,fill=(0,0,0,70)); shadow=shadow.filter(ImageFilter.GaussianBlur(18))

GRC={}
def background(col,t):
    if col in GRC: im=GRC[col].copy()
    else:
        GRC[col]=_grad(col); im=GRC[col].copy()
    d=ImageDraw.Draw(im)
    for j,(x,y,rr) in enumerate([(120,300,90),(960,520,130),(180,1500,150),(900,1700,80),(540,90,60)]):
        yy=y+18*math.sin(t*0.8+j*1.7); xx=x+12*math.cos(t*0.6+j)
        d.ellipse((xx-rr,yy-rr,xx+rr,yy+rr),fill=(255,255,255,60))
    return im
def _grad(col):
    c=np.array(col,float); top=np.clip(c*1.04+8,0,255); bot=np.clip(c*0.93,0,255)
    g=np.linspace(0,1,H)[:,None,None]; arr=(top*(1-g)+bot*g)*np.ones((1,W,1))
    return Image.fromarray(arr.astype(np.uint8)).convert('RGBA')

ff=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','20','-preset','medium','-pix_fmt','yuv420p',OUT+'_v.mp4'],stdin=subprocess.PIPE)
N=int(total*FPS); bgcache={}
def cur_slide(t):
    for j,s in enumerate(slides):
        if s['t0']<=t<s['t0']+s['dur']: return j
    return len(slides)-1 if t>=slides[-1]['t0'] else 0
for fi in range(N):
    t=fi/FPS; j=cur_slide(t); s=slides[j]; lt=t-s['t0']
    key=(j, fi//2)
    can=background(s['bg'],t)
    # previous slide leaving
    TR=0.4
    if j>0 and lt<TR:
        p=slides[j-1]; q=ease(lt/TR)
        x=W/2-q*(W*1.1); paste_x=int(x-SW/2)
        can.alpha_composite(shadow,(paste_x-40,SY-40)); can.alpha_composite(p['card'],(paste_x,SY))
    # current slide entering + slow zoom
    if t<0.6: q=ease_out_back(t/0.6) if True else 1; xoff=0; sc=0.6+0.4*q
    else:
        q=ease_out_back(lt/TR) if j>0 else 1; xoff=(1-q)*W*1.1 if j>0 else 0; sc=1.0
    zz=0.06*ease(lt/s['dur']); sc*=1+zz
    card=s['card'] if abs(sc-1)<0.003 else s['card'].resize((int(SW*sc),int(SH*sc)),Image.BILINEAR)
    cx=W/2+xoff; cy=SY+SH/2+zz*SH*0.35
    can.alpha_composite(shadow.resize((card.width+80,card.height+80)) if card.width!=SW else shadow,(int(cx-card.width/2-40),int(cy-card.height/2-40)))
    can.alpha_composite(card,(int(cx-card.width/2),int(cy-card.height/2)))
    # talking Moty, bottom right
    k=int((lt-s['va'])*FPS); a=0.0
    if 0<=k<len(s['env']) and lt<s['vend']+0.05: a=min(1,s['env'][k]*1.35)
    spr=SPR[int(round(a*10))]
    ent=ease_out_back(min(1,max(0,(t-0.25)/0.6)))
    bob=6*math.sin(t*2*math.pi*0.7)-(55*math.sin(math.pi*lt/0.4) if j>0 and lt<0.4 else 0); squash=1+0.035*a
    sw_=int(MW*(1/squash**0.5)); sh_=int(MH*squash)
    sp=spr.resize((sw_,sh_),Image.BILINEAR) if a>0.02 else spr
    mx=W-MW/2-10; my=H-sh_/2+40+bob+(1-ent)*700
    sp=sp.rotate(3*math.sin(t*1.3),resample=Image.BICUBIC,expand=False)
    can.alpha_composite(sp,(int(mx-sp.width/2),int(my-sp.height/2)))
    # progress dots
    d=ImageDraw.Draw(can); n=len(slides); gx=W/2-(n-1)*14
    for m in range(n):
        x=gx+m*28; r_=9 if m==j else 6
        d.ellipse((x-r_,SY+SH+38-r_,x+r_,SY+SH+38+r_),fill=(124,194,66,255) if m<=j else (255,255,255,200))
    ff.stdin.write(np.array(can.convert('RGB')).tobytes())
ff.stdin.close(); ff.wait()
inp=[]; flt=[]
for m,(at,f) in enumerate(audio):
    inp+=['-i',f]; flt.append(f'[{m+1}:a]adelay={int(at*1000)}|{int(at*1000)}[a{m}]')
mix=''.join(f'[a{m}]' for m in range(len(audio)))+f'amix=inputs={len(audio)}:normalize=0,apad,atrim=0:{total},loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[aout]'
subprocess.run(['ffmpeg','-y','-v','error','-i',OUT+'_v.mp4',*inp,'-filter_complex',';'.join(flt+[mix]),'-map','0:v','-map','[aout]','-c:v','copy','-ac','2','-c:a','aac','-b:a','160k','-movflags','+faststart',OUT],check=True)
os.remove(OUT+'_v.mp4'); print('ok',OUT,round(total,1),'s')
