import cv2, numpy as np, sys
src = cv2.imread(sys.argv[1])
panels = [(0,269),(271,524),(526,760),(762,1004),(1006,1253),(1255,1536)]
# boxes (x0,y0,x1,y1) in panel coordinates containing baked-in overlays
boxes = {0:[(660,80,960,205)],1:[(675,100,975,160)],2:[(665,50,975,170)],
         3:[(690,25,975,180)],4:[(595,45,975,200)],5:[(660,45,980,160),(435,35,592,185)]}
sr = cv2.dnn_superres.DnnSuperResImpl_create(); sr.readModel("EDSR_x4.pb"); sr.setModel("edsr",4)
for i,(y0,y1) in enumerate(panels):
    p = src[y0:y1].copy(); h = p.shape[0]
    hsv = cv2.cvtColor(p, cv2.COLOR_BGR2HSV)
    b,g,r = [p[...,k].astype(int) for k in range(3)]
    texty = ((hsv[...,2]>185)&(hsv[...,1]<70)) | ((r>200)&(g>140)&(b<110)&(r-b>110))
    mask = np.zeros(p.shape[:2],np.uint8)
    for (a,c,d,e) in boxes[i]:
        mask[c:e,a:d] = texty[c:e,a:d]*255
    if i==5:  # play button: mask whole circle
        cv2.circle(mask,(512,1365-1255),74,255,-1)
    mask[h-42:h-2, 4:152] = 255   # timestamp label
    mask = cv2.dilate(mask, np.ones((5,5),np.uint8), iterations=2)
    p = cv2.inpaint(p, mask, 9, cv2.INPAINT_TELEA)
    cv2.imwrite(f"clean{i}.png", p)
    up = sr.upsample(p)
    cv2.imwrite(f"up{i}.png", up); print(i, up.shape, flush=True)
