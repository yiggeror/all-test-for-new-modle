import subprocess,sys
from pathlib import Path
from PIL import Image

exe,folder=Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve()
for f in sorted(folder.glob('wire_*.bin')):
    mask=f.with_suffix('.pgm')
    subprocess.run([str(exe),str(f),str(mask)],check=True)
    picture=f.with_suffix('.png')
    scene=Image.open(picture).convert('RGB')
    shade=Image.new('RGB',scene.size,(43,48,53))
    matte=Image.open(mask).convert('L')
    Image.composite(shade,scene,matte).save(picture,optimize=True)
