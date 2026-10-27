import numpy as np, wave
SR=48000; DUR=36.5; N=int(SR*DUR); out=np.zeros(N)
rng=np.random.default_rng(7)
def midi(m): return 440*2**((m-69)/12)
def note(t, m, vel, length=4.0):
    f=midi(m); n=int(SR*length); tt=np.arange(n)/SR
    dec = 1.6 + 2.5*(60-min(m,60))/24 if m<60 else 1.3-0.4*(m-60)/24
    s=np.zeros(n)
    for k,a in enumerate([1,.45,.25,.14,.08,.05],1):
        fk=f*k*np.sqrt(1+0.0004*k*k)
        s+=a*np.sin(2*np.pi*fk*tt)*np.exp(-tt*(1/dec)*(1+0.6*(k-1)))
    s*=np.minimum(tt/0.006,1)
    s[:300]+=rng.normal(0,0.02,300)*np.linspace(1,0,300)
    i=int(t*SR); j=min(N,i+n); out[i:j]+=vel*s[:j-i]
# Am - F - C - G ... ending on C ; one chord per 2.5s
prog=[(57,[57,60,64]),(53,[53,57,60]),(48,[48,52,55]),(55,[55,59,62])]
beat=2.5/4
chords=[prog[k%4] for k in range(14)]
chords[-2]=prog[3]; chords[-1]=prog[2]
for c,(root,tri) in enumerate(chords):
    t0=0.3+c*2.5
    note(t0, root-12, 0.55, 6)
    pat=[tri[0]+12, tri[1]+12, tri[2]+12, tri[1]+12]
    for b,m in enumerate(pat):
        note(t0+b*beat+rng.uniform(-.01,.01), m, 0.28 if b else 0.34, 4)
    if c>=4:  # gentle melody enters with the swell
        mel=[tri[2]+24, tri[1]+24]
        note(t0+0.02, mel[0], 0.16, 4); note(t0+1.25, mel[1], 0.12, 4)
# soft string pad from 10s
t=np.arange(N)/SR; pad=np.zeros(N)
for c,(root,tri) in enumerate(chords):
    t0=0.3+c*2.5; i=int(t0*SR); j=min(N,int((t0+2.6)*SR)); tt=t[i:j]-t0
    env=np.minimum(tt/0.6,1)*np.minimum((2.6-tt)/0.4,1)
    for m in tri: pad[i:j]+=0.05*env*np.sin(2*np.pi*midi(m)*tt+0.3*np.sin(2*np.pi*5*tt))
pad*=np.clip((t-9.5)/3,0,1)
out+=pad
# dynamics: quiet start, swell at "لا تلتفت للعمر" (~10.5s), lower at the ending
env=np.interp(t,[0,9.8,13.5,26,30,33.5,35.6,36.5],[0.45,0.5,1.0,0.95,0.65,0.5,0.0,0.0])
out*=env
# reverb via FFT convolution with decaying noise IR
L=int(SR*2.8); ir=rng.normal(0,1,L)*np.exp(-np.arange(L)/SR*2.6); ir[0]=0; ir/=np.abs(ir).sum()/6
M=1<<int(np.ceil(np.log2(N+L))); wet=np.fft.irfft(np.fft.rfft(out,M)*np.fft.rfft(ir,M),M)[:N]
mix=out*0.75+wet*0.55
mix/=np.abs(mix).max()/0.9
st=np.stack([mix,np.roll(mix,240)],1)
with wave.open('music.wav','wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st*32767).astype('<i2').tobytes())
