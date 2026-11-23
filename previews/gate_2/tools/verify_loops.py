#!/usr/bin/env python3
"""Read-only media QA for two real 330-frame Rainroji Gate 2 cycles (ffmpeg/Pillow/NumPy)."""
import argparse, hashlib, json, os, subprocess as sp
from collections import Counter
from fractions import Fraction
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

W,H,P,F,GRID=320,180,330,660,6
SEAM=list(range(321,330))+list(range(9))
DECODED_SEAM=list(range(321,339))
ROIS={
 'spring':{'cat':(142,120,175,140),'moths/lamp':(123,72,159,108),'tree':(173,20,242,88),'TV/window':(107,63,133,88),'wallA':(24,70,40,78),'wallB':(277,113,284,123)},
 'summer':{'shelter cat':(160,96,190,124),'red reflection':(219,135,283,164),'sign':(220,34,239,66),'drops':(177,110,220,143),'barber':(140,84,154,118),'wallA':(32,96,50,106),'wallB':(261,73,273,83)},
 'autumn':{'bird corridor':(105,0,205,44),'steam':(70,113,88,139),'lamp/leaves':(105,28,155,82),'falling leaves':(110,78,212,152),'wallA':(30,139,42,145),'wallB':(178,133,190,142)},
 'winter':{'reader':(243,98,272,118),'chimney':(264,58,301,88),'snow/lamp':(41,42,77,91),'stairs':(97,19,125,48),'TV/window':(246,30,274,50),'wallA':(111,73,125,87),'wallB':(292,102,303,116)}
}
FILL='#161d27'; WHITE='#f7f3e7'; AMBER='#ffaa55'; FONTB='#a8bed1'
def R(x):return round(float(x),5)
def sh(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sha(a):return hashlib.sha256(np.ascontiguousarray(a)).hexdigest()
def run(args):return sp.check_output(args)
def gj(args):return json.loads(run(['ffprobe','-v','error']+args+['-of','json']))
def fullprobe(vid):
 s=gj(['-show_streams','-show_format',str(vid)]); v=next(x for x in s['streams'] if x['codec_type']=='video')
 f=gj(['-threads','2','-select_streams','v:0','-show_frames','-show_entries','frame=best_effort_timestamp,duration,key_frame',str(vid)])['frames']; p=[int(x['best_effort_timestamp']) for x in f]; step=Fraction(1,30)/Fraction(v['time_base']); delta=Counter(b-a for a,b in zip(p,p[1:])); counts={str(k):v for k,v in delta.items()}; expected=p[0]==0 and len(p)==F and all(d==step for d in delta)
 return {'stream':{k:v.get(k) for k in ('codec_name','profile','width','height','pix_fmt','r_frame_rate','avg_frame_rate','time_base','start_pts','duration','nb_frames','color_range','color_space','color_transfer','color_primaries','chroma_location')},'duration':s['format']['duration'],'bytes':int(s['format']['size']),'audio_tracks':sum(r['codec_type']=='audio' for r in s['streams']),'decoded_pts_count':len(p),'pts_first_last':p[:1]+p[-1:],'pts_step_counts':counts,'keyframe_indices':[i for i,x in enumerate(f) if int(x.get('key_frame',0))],'passes_1080_30_two_periods_pts':bool(expected and (v['width'],v['height'])==(1920,1080) and Fraction(v['avg_frame_rate'])==30 and abs(float(v['duration'])-22)<0.0001)}
def loadnative(path):
 if path.is_dir():
  ps=sorted(path.glob('*.png')); return np.stack([np.asarray(Image.open(p).convert('RGB')) for p in ps])
 if path.suffix=='.npz':
  d=np.load(path);return d['frames'] if 'frames' in d else d[d.files[0]]
 return np.load(path,mmap_mode='r')
def tstats(arr, period=P):
 # Returned arrays retain only 330 tiny data points, never an entire diff movie.
 rows=[]
 for k in range(period):
  nxt=(k+1)%period; d=np.abs(arr[nxt].astype('i2')-arr[k].astype('i2')); m=d.max(-1)
  rows.append([R(d.mean()),int((m>0).sum()),int((m>=8).sum()),int((m>=24).sum()),int(m.max())])
 q=np.asarray(rows); near=np.r_[q[320:329,0],q[:9,0]]; full=q[:,0]
 return {'metrics':['RGB mean absolute 0..255','count any change','count max channel >=8','count >=24','max channel'],'seam_329_to_0':rows[-1], 'join_neighbor_mad_median':R(np.median(near)),'join_neighbor_mad_range':[R(near.min()),R(near.max())],'native_seam_span':{'src_phase_indices':SEAM,'pair_metrics':[rows[i] for i in SEAM[:-1]]},'seam_mad_percentile_rank':R(100*(full<=full[-1]).mean()),'seam_mad_relative_to_local_median':R(full[-1]/max(np.median(near),.0001)),'all_mad_p05_p50_p95_p99_max':[R(x) for x in np.percentile(full,[5,50,95,99,100])], 'adjacent_identical_count':int((q[:,1]==0).sum()),'periods_330_raw_frame_hash_unique':len({sha(a) for a in arr[:period]})}
def roi_metric(arr,rect):
 x,y,X,Y=rect; roi=arr[:,y:Y,x:X]; minc=roi.min(0);maxc=roi.max(0);span=(maxc-minc).max(-1); delta=np.abs(roi[1:].astype('i2')-roi[:-1].astype('i2')); change=(delta.max(-1)>0).mean((1,2)); return {'rect':rect,'changed_at_least_once_pixel_pct':R(100*(span>0).mean()),'unchanged_all_330_pixel_pct':R(100*(span==0).mean()),'frames_with_any_change_pct':R(100*(change>0).mean()),'max_one_step_changing_area_pct':R(100*change.max()),'permanent_range_gt16_pct':R(100*(span>=16).mean()),'max_rgb_any':int(span.max()),'unique_roi_frames':len({sha(f) for f in roi})}
def data_bg(a):
 # Not a translated crop of a master frame: first-vs-other and temporal movement map.
 lo=np.minimum.reduce(a[:P]);hi=np.maximum.reduce(a[:P]);r=(hi-lo).max(-1); return r
def save_badge(sheet,x,y,string,color=WHITE):
 d=ImageDraw.Draw(sheet);d.text((x,y),string,fill=color)
def sheet_stage(a,base,s,out,stage):
 ids=[0,28,57,88,120,152,185,217,249,282,311,329]
 sheet=Image.new('RGB',(4*248,3*158+30),FILL); save_badge(sheet,7,6,f'{s.upper()} / {stage}: whole-frame progression, native 320x180, 11.0 seconds')
 for j,i in enumerate(ids):
  tile=Image.fromarray(a[i]).resize((240,135),Image.Resampling.NEAREST);x=4+248*(j%4);y=30+158*(j//4); sheet.paste(tile,(x,y));save_badge(sheet,x,y+136,f'phase {i:03} / {i/30:.2f}s',FONTB)
 sheet.save(out/f'{s}_{stage}_progress.png',optimize=True)
 r=data_bg(a); norm=np.clip(np.log1p(r)*255/np.log(96),0,255).astype('uint8');mask=np.stack([norm,np.minimum(norm,180),norm//3],-1); tmp=Image.new('RGB',(640,400),FILL);save_badge(tmp,5,3,'Gate 1.5 locked still');save_badge(tmp,325,3,'Gate 2 phase 0');tmp.paste(base,(0,18));tmp.paste(Image.fromarray(a[0]),(320,18));save_badge(tmp,5,201,'330-frame temporal RGB range (log display)');save_badge(tmp,325,201,'Gate1.5->phase0 abs RGB difference (boost x3)');tmp.paste(Image.fromarray(mask),(0,217));tmp.paste(Image.fromarray(np.clip(3*np.abs(a[0].astype('i2')-np.asarray(base).astype('i2')),0,255).astype('uint8')),(320,217));tmp.save(out/f'{s}_{stage}_motion_map.png')
def sheet_rois(arr,s,out,stage,indices=None):
 rois={k:v for k,v in ROIS[s].items() if not k.startswith('wall')}; phase=indices or list(range(0,330,21)); tilew=154;tileh=95;n=len(phase);keys=list(rois.keys()); sheet=Image.new('RGB',(94+tilew*min(8,n), 27+len(keys)*((n+7)//8)*tileh),FILL);save_badge(sheet,4,4,f'{s} {stage}: native subject crops, nearest neighbor. Column label = native frame.')
 for ind,k in enumerate(keys):
  rect=rois[k];x,y,X,Y=rect;scale=min(tilew//(X-x),(tileh-17)//(Y-y));scale=max(1,min(5,scale));cw=(X-x)*scale;ch=(Y-y)*scale
  for j,f in enumerate(phase):
   row=ind*((n+7)//8)+j//8;left=94+tilew*(j%8);top=27+row*tileh;crop=Image.fromarray(arr[f,y:Y,x:X]).resize((cw,ch),0)
   sheet.paste(crop, (left+(tilew-cw)//2, top+(tileh-18-ch)//2)); save_badge(sheet,left+6,top+tileh-17,f'{f:03} / {f/30:.1f}s',FONTB)
   if j%8==0:save_badge(sheet,4,top+25,k, AMBER)
 sheet.save(out/f'{s}_{stage}_roi.png',optimize=True)
def seam_sheet(a,s,out,stage,original_ids,actual_ids):
 # Small full picture and a running difference beside each picture, not first/last only.
 stepw,steph=234,132; sheet=Image.new('RGB',(stepw*6,30+steph*3),FILL);save_badge(sheet,6,5,f'{s} / {stage} seam continuity. Left scene, right 3x RGB diff to previous. Labels are zero-based.')
 for j,(p,i) in enumerate(zip(original_ids,actual_ids)):
  before=(i-1)%len(a); frame=a[i];dif=np.clip(3*np.abs(frame.astype('i2')-a[before].astype('i2')),0,255).astype('uint8');x=(j%6)*stepw;y=(j//6)*steph+30
  sheet.paste(Image.fromarray(frame).resize((154,87),0),(x,y)); sheet.paste(Image.fromarray(dif).resize((75,42),0),(x+157,y+23));save_badge(sheet,x+2,y+89,f'f {p:03}, phase {p%P:03}',AMBER if p%P==0 else FONTB)
 sheet.save(out/f'{s}_{stage}_seam.png',optimize=True)
def decode_native_rgb(vid):
 # Convert in the same order as a full-size RGB player; only then select NN centers.
 raw=run(['ffmpeg','-v','error','-threads','2','-filter_threads','1','-i',str(vid),'-map','0:v:0','-vf','format=rgb24,scale=320:180:flags=neighbor','-threads','1','-f','rawvideo','-pix_fmt','rgb24','pipe:1'])
 return np.frombuffer(raw,'u1').reshape(-1,H,W,3)
def dec_full_samples(vid,n,pp):
 samples=sorted({*range(321,339),0,83,165,249,659}); filt="select='"+'+'.join(f'eq(n,{i})' for i in samples)+"'"
 proc=sp.Popen(['ffmpeg','-v','error','-threads','2','-filter_threads','1','-i',str(vid),'-map','0:v:0','-vf',filt,'-fps_mode','passthrough','-threads','1','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=sp.PIPE)
 rows=[]
 for i in samples:
  raw=proc.stdout.read(W*H*3*36); assert len(raw)==W*H*108,('short decoded sample',i);im=np.frombuffer(raw,'u1').reshape(H,6,W,6,3); ref=im[:,3,:,3,:];uniform=np.all(im==ref[:,None,:,None,:],axis=(1,3,4));err=np.abs(ref.astype('i2')-n[i%P].astype('i2'));rows.append({'output_frame':i,'nonuniform_blocks':int((~uniform).sum()),'mean_center_vs_native_rgb':R(err.mean()),'channel_p99_max':[R(np.percentile(err,99)),int(err.max())]})
 proc.stdout.close();assert proc.wait()==0
 return rows
def yuv_grid(vid,pix_fmt):
 # Whole encoded picture, all 660: native Y, U and V measurements before chroma upsampling.
 if pix_fmt not in ('yuv420p','yuv444p','yuvj420p','yuvj444p','gbrp'):return {'performed':False,'unsupported_plane_layout':pix_fmt}
 half='420' in pix_fmt; sizes=[(H*6,W*6,6)]+([(H*3,W*3,3)]*2 if half else [(H*6,W*6,6)]*2); nbytes=sum(h*w for h,w,_ in sizes)
 p=sp.Popen(['ffmpeg','-v','error','-threads','2','-i',str(vid),'-map','0:v:0','-threads','1','-f','rawvideo','-pix_fmt',pix_fmt,'pipe:1'],stdout=sp.PIPE)
 bad=[0,0,0];worst=[0,0,0];n=0
 while True:
  raw=p.stdout.read(nbytes)
  if not raw:break
  assert len(raw)==nbytes;offset=0
  for j,(h,w,g) in enumerate(sizes):
   a=np.frombuffer(raw,uint8,count=h*w,offset=offset).reshape(H,g,W,g);offset+=h*w; ref=a[:,0,:,0];eq=np.all(a==ref[:,None,:,None],axis=(1,3))
   fail_count=H*W-int(np.count_nonzero(eq))
   if fail_count:bad[j]+=1;worst[j]=max(worst[j],fail_count)
  n+=1
 p.stdout.close();assert p.wait()==0
 return {'performed':True,'frames_tested':n,'frames_with_any_split_block_per_plane':bad,'max_split_blocks_one_frame_per_plane':worst,'exact_6x6_Y_3x3_UV_or_6x6_444_all_frames':n==F and not any(bad)}
uint8=np.uint8
def dmetric_frame(a,b):
 d=np.abs(a.astype('i2')-b.astype('i2'));z=d.max(-1);return [R(d.mean()),int((z>0).sum()),int((z>=8).sum()),int((z>=24).sum()),int(z.max())]
def metric_pairs(a,b):
 rows=np.array([dmetric_frame(a[i],b[i]) for i in range(len(a))])
 return {'frames_compared':len(rows),'identical_frame_count':int((rows[:,1]==0).sum()),'mean_abs_0_255_over_all':R(rows[:,0].mean()),'max_one_frame_mad':R(rows[:,0].max()),'max_any_pixel_channel':int(rows[:,-1].max()),'max_fraction_pixels_in_any_one_frame_rgb_diff_ge_8':R(rows[:,2].max()/(W*H))}
def find_native_frame_flags(a):
 # Empirically compares every phase's actual source frame, not simply whether is same at join.
 n=len(a);out={'provided_frame_count':n,'size':[W,H],'sha256_content_digest_all_provided_frames':hashlib.sha256(b''.join(bytes.fromhex(sha(x)) for x in a)).hexdigest()}
 if n==2*P:out['provided_two_cycles_equal']=metric_pairs(a[:P],a[P:2*P])
 return out
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('season',choices=ROIS);ap.add_argument('--native',type=Path,required=True);ap.add_argument('--video',type=Path);ap.add_argument('--base',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--omit-all-plane-grid',action='store_true',help='Exploratory only; full validation scans all encoded planes by default');args=ap.parse_args();s=args.season;out=args.out;out.mkdir(parents=True,exist_ok=True)
 n=loadnative(args.native);assert n.ndim==4 and n.shape[1:]==(H,W,3) and n.dtype==np.uint8 and len(n) in (P,F),n.shape
 base=Image.open(args.base).convert('RGB');basearr=np.asarray(base)
 rep={'scene':s,'media_basename':args.video.name if args.video else None,'approved_still_sha256':sh(args.base),'native':find_native_frame_flags(n)}
 rep['native_motion']=tstats(n);rep['native_regions']={k:roi_metric(n[:P],r) for k,r in ROIS[s].items()};rep['approved_to_phase0']=dict(zip(['mad_0_255','pixels_changed','pixels_ge8','pixels_ge24','max'],dmetric_frame(basearr,n[0])))
 out_json=out/f'{s}_native.json';out_json.write_text(json.dumps(rep,indent=2));sheet_stage(n[:P],base,s,out,'native');sheet_rois(n[:P],s,out,'native'); seam_sheet(n[:P],s,out,'native',SEAM,SEAM)
 if not args.video:return
 vid=args.video;rep['mp4_sha256']=sh(vid);rep['probe']=fullprobe(vid); dec=decode_native_rgb(vid);assert len(dec)==F,(len(dec),F);rep['decoded_330_pair_all']=metric_pairs(dec[:P],dec[P:]);rep['native_vs_decoded_center_cycle1']=metric_pairs(n[:P],dec[:P]);rep['native_vs_decoded_center_cycle2']=metric_pairs(n[:P],dec[P:]);rep['decoded_adjacent_321_338']={'actual_indices':DECODED_SEAM,'pair_metrics':[dmetric_frame(dec[i],dec[i+1]) for i in DECODED_SEAM[:-1]]};rep['decoded_regions']={k:roi_metric(dec[:P],r) for k,r in ROIS[s].items() if k.startswith('wall')};rep['rgb_decoded_6x6_samples']=dec_full_samples(vid,n,P)
 pix=rep['probe']['stream']['pix_fmt'];rep['encoded_plane_grid_all_frames']=None if args.omit_all_plane_grid else yuv_grid(vid,pix);seam_sheet(dec,s,out,'encoded',DECODED_SEAM,DECODED_SEAM);sheet_rois(dec[:P],s,out,'encoded');sheet_stage(dec[:P],base,s,out,'encoded')
 (out/f'{s}_verified.json').write_text(json.dumps(rep,indent=2));print(s,json.dumps({'ffprobe':rep['probe']['passes_1080_30_two_periods_pts'],'seam':rep['native_motion']['seam_329_to_0'],'repeat':rep['decoded_330_pair_all'],'grid':rep['encoded_plane_grid_all_frames'],'split_blocks_max_sample':max(z['nonuniform_blocks'] for z in rep['rgb_decoded_6x6_samples'])}),flush=True)
if __name__=='__main__':main()
