"""PHASE 2 vertical prototype: prompt -> scenes -> audio -> captions -> MP4.

This is intentionally provider-free. It creates deterministic visual cards and a
synthetic WAV track, then assembles them with imageio-ffmpeg. It proves the full
pipeline contract before real AI providers are connected.
"""
from __future__ import annotations
import hashlib, math, subprocess, wave
from pathlib import Path
from textwrap import wrap
from PIL import Image, ImageDraw, ImageFont
from core.models import ContentRequest
from core.workspace import Workspace
DEFAULT_TOPIC = "строительство модульного дома зимой"

def _font(size: int, bold: bool=False):
    candidates=[Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")]
    for p in candidates:
        if p.exists(): return ImageFont.truetype(str(p),size)
    return ImageFont.load_default()

def _make_audio(path: Path, duration: float, sample_rate: int=22050)->None:
    frames=bytearray(); total=int(duration*sample_rate)
    for i in range(total):
        t=i/sample_rate; value=int(4500*math.sin(2*math.pi*180*t)*(0.55+0.45*math.sin(2*math.pi*3*t)**2))
        frames += int(value).to_bytes(2,"little",signed=True)
    with wave.open(str(path),"wb") as wav:
        wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(sample_rate); wav.writeframes(frames)

def _make_card(path: Path,title: str,body: str,index: int,total: int,width: int,height: int)->None:
    digest=hashlib.sha256(f"{title}:{index}".encode()).digest(); base=tuple(30+x%80 for x in digest[:3])
    image=Image.new("RGB",(width,height),base); draw=ImageDraw.Draw(image); accent=tuple(150+x%80 for x in digest[3:6])
    draw.rectangle((60,90,width-60,105),fill=accent); draw.text((70,150),f"СЦЕНА {index}/{total}",font=_font(46,True),fill="white")
    y=360
    for line in wrap(title,width=25): draw.text((70,y),line,font=_font(78,True),fill="white"); y+=95
    y+=80
    for line in wrap(body,width=34): draw.text((70,y),line,font=_font(48),fill="white"); y+=68
    draw.text((70,height-130),"AI Content Agent • MOCK",font=_font(34),fill="white"); image.save(path,"PNG")

def _write_srt(path: Path,scenes:list[tuple[float,float,str]])->None:
    def stamp(seconds:float)->str:
        ms=int(round((seconds-int(seconds))*1000)); total=int(seconds); h,rem=divmod(total,3600); m,s=divmod(rem,60); return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    lines=[]
    for i,(start,end,text) in enumerate(scenes,1): lines += [str(i),f"{stamp(start)} --> {stamp(end)}",text,""]
    path.write_text("\n".join(lines),encoding="utf-8")

def _render_mp4(work:Path,output:Path,duration:float,fps:int)->None:
    try: import imageio_ffmpeg
    except ImportError as exc: raise RuntimeError("imageio-ffmpeg is required; install with: python -m pip install -e .") from exc
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe(); cards=sorted(work.glob("scene_*.png")); scene_duration=duration/len(cards); concat=work/"concat.txt"
    concat.write_text("".join(f"file '{p.name}'\nduration {scene_duration:.6f}\n" for p in cards)+f"file '{cards[-1].name}'\n",encoding="utf-8")
    cmd=[ffmpeg,"-y","-f","concat","-safe","0","-i",str(concat),"-i",str(work/"voice_mock.wav"),"-r",str(fps),"-t",str(duration),"-vf","format=yuv420p","-c:v","libx264","-preset","veryfast","-crf","27","-c:a","aac","-b:a","96k",str(output)]
    subprocess.run(cmd,check=True,capture_output=True,text=True)

def run_demo(topic:str=DEFAULT_TOPIC,duration:int=43,output_dir:str="output")->Path:
    request=ContentRequest(project_id="demo",topic=topic,duration_seconds=duration); workspace=Workspace.create(output=output_dir); work=workspace.project_subdir(request.project_id,"mock")
    cards=[("Зимой строительство продолжается","Модульный дом можно собирать даже при низких температурах."),("Подготовка участка","Главное — основание, логистика и защита рабочих зон от снега."),("Изготовление модулей","Большая часть работ выполняется заранее в контролируемых условиях."),("Доставка и монтаж","Готовые модули быстро устанавливаются на подготовленный фундамент."),("Утепление и инженерия","Контуры утепления и коммуникации закрываются по технологическому плану."),("Работа зимой","Зима требует контроля температуры, но не останавливает весь процесс."),("Результат","Такой подход сокращает время на площадке и ускоряет готовность дома.")]
    scene_duration=duration/len(cards); scenes=[]
    for i,(title,body) in enumerate(cards,1):
        start=(i-1)*scene_duration; end=i*scene_duration; _make_card(work/f"scene_{i:02d}.png",title,body,i,len(cards),request.width,request.height); scenes.append((start,end,title+". "+body))
    _make_audio(work/"voice_mock.wav",duration); _write_srt(work/"captions.srt",scenes)
    output=workspace.output_file(f"demo_{hashlib.sha1(topic.encode()).hexdigest()[:8]}.mp4"); _render_mp4(work,output,duration,request.fps); return output
