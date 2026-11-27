"""Read the real packaged video and verify all frames decode correctly."""
import argparse,json,hashlib,subprocess
from pathlib import Path

def cmd(xs,work=None):
 r=subprocess.run(xs,check=True,capture_output=True,text=True,cwd=work)
 return r.stdout

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('mp4',type=Path);p.add_argument('--first',type=int,default=1);p.add_argument('--last',type=int,default=360);p.add_argument('--record',type=Path);args=p.parse_args()
 video=args.mp4.resolve(); manifest=json.loads(video.with_suffix('.frames.json').read_text())
 expected=args.last-args.first+1
 probe=json.loads(cmd(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(video)]))
 streams=probe['streams'];assert len(streams)==1 and streams[0]['codec_type']=='video',streams
 s=streams[0]; assert (s['codec_name'],s['width'],s['height'],s['pix_fmt'])==('h264',1920,1080,'yuv420p'),s
 assert s['avg_frame_rate']=='30/1' and int(s['nb_read_frames'])==expected,s
 assert abs(float(s['duration'])-expected/30)<.0001, s
 assert s.get('color_space','')=='bt709' and s.get('color_range','')=='tv'
 ids=[j['frame'] for j in manifest['frames']]; assert ids==list(range(args.first,args.last+1))
 framemd5=cmd(['ffmpeg','-hide_banner','-v','error','-xerror','-threads','2','-i',str(video),'-map','0:v:0','-f','framemd5','-'])
 digest_lines=[x.rsplit(', ',1)[-1] for x in framemd5.splitlines() if x and not x.startswith('#')]
 assert len(digest_lines)==expected and len(set(digest_lines))==expected,'duplicate or missing decoded frames'
 out=video.with_suffix('.framemd5');out.write_text(framemd5)
 result={'file':video.name,'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'frame_count':expected,
   'size':[1920,1080],'fps':30,'duration_s':round(expected/30,6),'codec':'H.264','decoded_unique':len(set(digest_lines)),
   'decode_md5_manifest_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'color_matrix':'BT.709','audio_tracks':0,
   'angles_deg':[manifest['frames'][0]['camera_azimuth_degrees'],manifest['frames'][-1]['camera_azimuth_degrees']]}
 if args.record:args.record.write_text(json.dumps(result,indent=2))
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
