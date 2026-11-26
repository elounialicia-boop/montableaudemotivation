# Cree les voix de Moty pour les 10 videos. Usage : python gen_voix.py "C:\\Users\\alyss\\Downloads"
import os, sys, json, subprocess, asyncio
OUT=os.path.join(sys.argv[1],'Videos Moty','voix'); os.makedirs(OUT,exist_ok=True)
try: import edge_tts
except ImportError:
    subprocess.run([sys.executable,'-m','pip','install','-q','edge-tts'],check=True); import edge_tts
L=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'lignes.json'),encoding='utf-8'))
async def main():
    for k,v in L.items():
        f=os.path.join(OUT,k+'.mp3')
        if os.path.exists(f) and os.path.getsize(f)>1000: continue
        for essai in range(3):
            try: await edge_tts.Communicate(v,'fr-FR-EloiseNeural',rate='+5%',pitch='+8Hz').save(f); break
            except Exception as e: print('nouvel essai',k,e)
        print('ok',k)
asyncio.run(main())
print('FINI :',len(L),'voix dans',OUT)
