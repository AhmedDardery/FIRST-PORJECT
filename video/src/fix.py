import cv2, numpy as np
src = cv2.imread('/root/.claude/uploads/9862076b-b97d-505a-903b-530e22157b6a/3b54a6d4-image.png').astype(np.float32)
panels = [(0,269),(271,524),(526,760),(762,1004),(1006,1253),(1255,1536)]
rng = np.random.default_rng(1)
for i,(y0,y1) in enumerate(panels):
    clean = cv2.imread(f'clean{i}.png').astype(np.float32); h,w = clean.shape[:2]
    fixed = clean.copy(); m = np.zeros((h,w),np.float32)
    # timestamp: copy the band just above it
    fixed[h-48:h, 0:160] = clean[h-96:h-48, 0:160]
    m[h-46:h, 0:156] = 1
    if i == 5:
        orig = cv2.GaussianBlur(src[y0:y1],(0,0),2)
        hole = np.zeros((h,w),np.float32); cv2.circle(hole,(512,110),86,1,-1)
        fill = orig.copy()
        for y in range(h):
            xs = np.where(hole[y]>0)[0]
            if len(xs)==0: continue
            a, b = xs[0]-4, xs[-1]+4
            L = orig[y, a-6:a].mean(0); R = orig[y, b:b+6].mean(0)
            t = ((np.arange(a,b+1)-a)/(b-a))[:,None]
            fill[y,a:b+1] = L*(1-t)+R*t
        fill = cv2.GaussianBlur(fill,(0,0),5) + rng.normal(0,1.5,orig.shape).astype(np.float32)
        fixed = np.where(hole[...,None]>0, fill, fixed)
        m = np.maximum(m, hole)
    m = cv2.GaussianBlur(cv2.dilate(m,np.ones((3,3))),(0,0),4)
    up = cv2.imread(f'up{i}.png').astype(np.float32)
    fu = cv2.resize(fixed,(w*4,h*4),interpolation=cv2.INTER_CUBIC)
    mu = cv2.resize(m,(w*4,h*4),interpolation=cv2.INTER_LINEAR)[...,None]
    out = up*(1-mu)+fu*mu
    cv2.imwrite(f'final{i}.png', np.clip(out,0,255).astype(np.uint8))
    cv2.imwrite(f'prev{i}.jpg', cv2.resize(np.clip(out,0,255).astype(np.uint8),(1024,h)))
