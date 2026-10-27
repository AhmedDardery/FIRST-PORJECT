import numpy as np, cv2, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H,FPS,DUR=1080,1920,30,35.0
FG_Y0, FG_H = 120, 1450          # sharp image band; feathered into blurred fill
WHITE=(255,255,255); GOLD=(244,193,79)
def ease(x): x=min(max(x,0),1); return x*x*(3-2*x)

imgs=[cv2.cvtColor(cv2.imread(f'final{i}.png'),cv2.COLOR_BGR2RGB).astype(np.float32) for i in range(6)]
# scene: (start, end, img, (cx,cy,h) start, (cx,cy,h) end, exposure start/end)
S=[(0,5.3,0,(1350,538,1076),(1520,430,700),(0.85,0.95)),       # zoom slowly into the face
   (4.7,10.3,1,(1150,600,640),(1300,506,1012),(0.9,1.0)),      # pull back
   (9.7,15.3,2,(980,468,936),(1200,500,860),(0.95,1.0)),       # slow track on the feet
   (14.7,21.3,3,(1060,484,968),(1230,470,880),(0.45,1.08)),    # dark -> light
   (20.7,28.3,4,(1120,640,720),(1230,440,880),(0.95,1.05)),    # camera rises
   (27.7,35.0,5,(1560,562,1124),(1470,500,960),(1.0,1.05))]    # final push, then fade
XF=0.6
fg_w=W; aspect=fg_w/FG_H

def crop(img,cx,cy,h,ow,oh):
    w=h*ow/oh; Hh,Ww=img.shape[:2]
    h=min(h,Hh); w=h*ow/oh
    cx=min(max(cx,w/2),Ww-w/2); cy=min(max(cy,h/2),Hh-h/2)
    s=ow/w
    M=np.float32([[s,0,-(cx-w/2)*s],[0,s,-(cy-h/2)*s]])
    return cv2.warpAffine(img,M,(ow,oh),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT)

# blurred full-frame fill per scene (precomputed, small, upscaled per frame)
blur=[]
for img in imgs:
    sm=cv2.resize(img,(img.shape[1]//8,img.shape[0]//8),interpolation=cv2.INTER_AREA)
    blur.append(cv2.GaussianBlur(sm,(0,0),6)*0.55)
yy=np.arange(H)[:,None].astype(np.float32)
fe=180
band=np.clip(np.minimum((yy-FG_Y0)/fe,(FG_Y0+FG_H-yy)/(fe*1.6)),0,1)
band=(band*band*(3-2*band))[...,None]
# vignette
xx=np.arange(W)[None,:]; r=np.sqrt(((xx-W/2)/(W*0.75))**2+((yy-H*0.42)/(H*0.62))**2)
vig=np.clip(1-0.55*r**2.2,0.25,1)[...,None].astype(np.float32)
grain=[np.random.default_rng(k).normal(0,4.5,(H//2,W//2,1)).astype(np.float32) for k in range(8)]

def scene_frame(k,t):
    t0,t1,i,a,b,ex=S[k]; u=ease((t-t0)/(t1-t0))
    cx,cy,h=[a[j]+(b[j]-a[j])*u for j in range(3)]
    fg=crop(imgs[i],cx,cy,h,W,FG_H)
    full=np.empty((H,W,3),np.float32)
    bs=blur[i]; bh,bw=bs.shape[:2]
    # cover-fit blurred fill centered on the subject
    sc=H/bh*1.15; cw=W/sc; x0=min(max(cx/8-cw/2,0),bw-cw)
    full=crop(bs,x0+cw/2,bh/2,bh/1.15,W,H)
    canvas=full.copy()
    canvas[FG_Y0:FG_Y0+FG_H]=fg*band[FG_Y0:FG_Y0+FG_H]+full[FG_Y0:FG_Y0+FG_H]*(1-band[FG_Y0:FG_Y0+FG_H])
    e=ex[0]+(ex[1]-ex[0])*ease((t-t0)/(t1-t0)*1.2)
    canvas*=e
    if i==3:   # light breaking in from the right as he walks toward it
        g=np.exp(-(((xx-W*0.95)/(W*0.7))**2+((yy-H*0.35)/(H*0.35))**2))[...,None]
        canvas+=g*np.array([255,190,110],np.float32)*0.35*ease((t-t0-1.5)/4)
    if i==5:   # sunrise glow
        g=np.exp(-(((xx-W*0.92)/(W*0.55))**2+((yy-H*0.36)/(H*0.22))**2))[...,None]
        canvas+=g*np.array([255,200,120],np.float32)*(0.25+0.2*ease((t-t0)/5))
    return canvas

def grade(img,t):
    w=ease((t-3)/26)   # cold blue/grey -> warm gold
    lum=img.mean(2,keepdims=True)
    sat=0.6+0.55*w
    img=lum+(img-lum)*sat
    cold=np.array([0.86,0.95,1.12],np.float32); warm=np.array([1.10,1.00,0.82],np.float32)
    img=img*(cold*(1-w)+warm*w)
    img=img+np.array([0,4,14],np.float32)*(1-w)*(1-np.clip(lum/255,0,1))  # blue shadows early
    # gentle filmic curve
    x=np.clip(img/255,0,1.4); img=255*(x*(1.6*x+0.06))/(x*(1.38*x+0.32)+0.08)
    return img

# ---------- text ----------
def font(sz):
    f=ImageFont.truetype('Cairo.ttf',sz,layout_engine=ImageFont.Layout.RAQM)
    f.set_variation_by_name('Bold'); return f
def block(lines):
    """lines: list of (size, [(text,color),...]); returns RGBA image W x h"""
    hts=[int(s*1.45) for s,_ in lines]; Ht=sum(hts)+40
    im=Image.new('RGBA',(W,Ht),(0,0,0,0)); d=ImageDraw.Draw(im)
    sh=Image.new('L',(W,Ht),0); ds=ImageDraw.Draw(sh)
    y=10
    for (sz,segs),lh in zip(lines,hts):
        f=font(sz); gap=sz*0.28
        ws=[f.getlength(tx,direction='rtl') for tx,_ in segs]
        tot=sum(ws)+gap*(len(segs)-1); xr=W/2+tot/2
        for (tx,col),wd in zip(segs,ws):
            x=xr-wd
            d.text((x,y),tx,font=f,fill=col,direction='rtl')
            ds.text((x+2,y+4),tx,font=f,fill=210,direction='rtl')
            xr=x-gap
        y+=lh
    sh=sh.filter(ImageFilter.GaussianBlur(9))
    base=Image.new('RGBA',(W,Ht),(0,0,0,0)); base.putalpha(sh)
    return np.asarray(Image.alpha_composite(base,im)).astype(np.float32)/255

TEXT_Y=1385
T=[(0.7,4.9,[(96,[("لستَ جاهزًا",WHITE)]),(80,[("أن تُجابِهَ العالم",GOLD)])]),
   (5.6,9.9,[(96,[("ما زلتَ",WHITE),("صغيرًا..",GOLD)])]),
   (10.4,14.9,[(88,[("لا تلتفت للعمر",WHITE)]),(76,[("إنه لا يعني",WHITE),("الكثير..",GOLD)])]),
   (15.3,20.9,[(76,[("فكم من رجلٍ كَبُرَ عمرُه",WHITE)]),(70,[("وما زال في داخله",WHITE),("طفلٌ",GOLD)]),(70,[("يبحث عن الأمان..",WHITE)])]),
   (21.4,27.4,[(74,[("وكم من روحٍ أتعبتها الحياة",WHITE)]),(70,[("وما زالت تتعلّم",WHITE)]),(80,[("كيف تقف من جديد",GOLD)])]),
   (27.7,32.5,[(92,[("لا بأس..",GOLD)]),(70,[("لستَ مُطالَبًا بأن تكون",WHITE)]),(70,[("قويًّا طوال الوقت",WHITE)])]),
   (32.8,34.75,[(80,[("لا بأس أن تتأخر قليلًا..",WHITE)]),(96,[("المهم ألا تتوقف.",GOLD)])])]
TB=[block(l) for _,_,l in T]
FADE=0.6

def frame(n):
    t=n/FPS
    act=[k for k,s in enumerate(S) if s[0]<=t<s[1]]
    if len(act)==1: img=scene_frame(act[0],t)
    else:
        a,b=act[0],act[-1]; u=ease((t-S[b][0])/XF)
        img=scene_frame(a,t)*(1-u)+scene_frame(b,t)*u
    img=grade(img,t)*vig
    img+=cv2.resize(grain[n%8],(W,H),interpolation=cv2.INTER_NEAREST)[...,None]
    # fade from black / image fades out before the last line
    img*=ease(t/0.9)*(1-0.85*ease((t-33.6)/1.2))
    for (t0,t1,_),tb in zip(T,TB):
        if t0<=t<=t1:
            al=ease((t-t0)/FADE)*ease((t1-t)/FADE)
            dy=int(14*(1-ease((t-t0)/0.9)))
            th=tb.shape[0]; y0=TEXT_Y+dy+(300-th)//2 if th<300 else TEXT_Y+dy-40
            reg=img[y0:y0+th]; a_=tb[...,3:4]*al
            img[y0:y0+th]=reg*(1-a_)+tb[...,:3]*255*a_
    return np.clip(img,0,255).astype(np.uint8)

if __name__=='__main__':
    if sys.argv[1]=='stills':
        for t in map(float,sys.argv[2:]):
            Image.fromarray(frame(int(t*FPS))).save(f'still_{t:05.1f}.jpg',quality=88)
    else:
        p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
            '-i','mix.wav','-c:v','libx264','-preset','slow','-crf','18','-pix_fmt','yuv420p','-profile:v','high',
            '-c:a','aac','-b:a','192k','-movflags','+faststart','-shortest',sys.argv[2]],stdin=subprocess.PIPE)
        for n in range(int(DUR*FPS)):
            p.stdin.write(frame(n).tobytes())
            if n%150==0: print(n,flush=True)
        p.stdin.close(); p.wait()
