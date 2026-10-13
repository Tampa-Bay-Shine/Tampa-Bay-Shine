from pathlib import Path
import argparse,json
from PIL import Image,ImageOps
ap=argparse.ArgumentParser(); ap.add_argument("source"); ap.add_argument("--dest",default="cloudflare-site/assets/images/blog"); ap.add_argument("--widths",default="480,768,1200,1600"); ap.add_argument("--quality",type=int,default=78); a=ap.parse_args()
src=Path(a.source); dest=Path(a.dest); dest.mkdir(parents=True,exist_ok=True); widths=sorted({int(x) for x in a.widths.split(",")}); manifest=[]
for p in src.rglob("*"):
 if p.suffix.lower() not in {".jpg",".jpeg",".png",".webp"}: continue
 try:
  with Image.open(p) as z:
   im=ImageOps.exif_transpose(z).convert("RGB")
   for w in widths:
    if w>im.width: continue
    h=round(im.height*w/im.width); r=im.resize((w,h),Image.Resampling.LANCZOS); op=dest/f"{p.stem.lower().replace(' ','-')}-{w}.webp"; r.save(op,"WEBP",quality=a.quality,method=6); manifest.append({"file":str(op),"width":w,"height":h,"bytes":op.stat().st_size})
 except Exception as e: print("WARN",p,e)
(dest/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8"); print(f"Generated {len(manifest)} WebP assets")
