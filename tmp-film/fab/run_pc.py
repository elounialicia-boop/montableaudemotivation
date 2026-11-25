# Rendu du film Moty V5 sur le PC. Usage : python run_pc.py "C:\Users\alyss\Downloads"
import os, sys, subprocess, urllib.request, shutil
DL = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
os.chdir(HERE)
os.makedirs('clips', exist_ok=True)
B = 'https://cdn.hailuoai.video/moss/prod/2026-11-25-04/video/'
URLS = {
 'h_a.mp4': B+'1795551701684730227-1_video_raw_b8d4b9828596a8ec05b4fecb3ece91c2_581730933229826050.mp4',
 'h_b.mp4': B+'1795551812880629157-1_video_raw_4abc7dfbbbe430a07da67a8b92b25daa_581731106689449992.mp4',
 'h_c.mp4': B+'1795551921880700173-1_video_raw_81b8b894b1c1ed71401eb570e7f1e6b8_581731246863065092.mp4',
 'h_d.mp4': B+'1795552074179590337-1_video_raw_7a8c566bb1e113ca756bb72175b75df0_581731404610875395.mp4',
 'mum.mp4': B+'1795552206815968827-1_video_raw_e86d72c0f99ac58c87ba726984cc2d07_581731523276144640.mp4',
}
for n,u in URLS.items():
    if not os.path.exists('clips/'+n): urllib.request.urlretrieve(u,'clips/'+n)
for c in ['moty-clip-chaos.mp4','moty-clip-cafe.mp4']:
    src=os.path.join(DL,c)
    if not os.path.exists(src): sys.exit('MANQUE le fichier '+src+' (telecharge-le dans Telechargements)')
    shutil.copy(src,'clips/'+c)
env = dict(os.environ, PYTHONUTF8='1', IMG=ROOT+os.sep, SCR=os.path.join(ROOT,'ecrans')+os.sep, CLIPS='clips'+os.sep,
           VOIX=os.path.join(DL,'Film Moty','voix')+os.sep, FONT='fredoka-700.ttf')
if not os.path.exists(os.path.join(DL,'Film Moty','voix','moty7.mp3')): sys.exit('MANQUE la voix moty7.mp3')
subprocess.run([sys.executable,'montage.py','cfg_v5.json','film_v5'],env=env,check=True)
out=os.path.join(DL,'Film Moty'); os.makedirs(out,exist_ok=True)
v=os.path.join(out,'Film Moty V5 - vertical 9x16.mp4'); shutil.copy('film_v5.mp4',v)
h=os.path.join(out,'Film Moty V5 - horizontal 16x9.mp4')
subprocess.run(['ffmpeg','-y','-v','error','-i','film_v5.mp4','-filter_complex',
 '[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,gblur=sigma=30,eq=brightness=-0.08[bg];[0:v]scale=-2:1080[fg];[bg][fg]overlay=(W-w)/2:0',
 '-c:v','libx264','-crf','19','-preset','medium','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',h],check=True)
print('OK', v, h)
