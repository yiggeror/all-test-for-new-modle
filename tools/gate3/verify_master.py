#!/usr/bin/env python3
"""Compare whole licensed original, printed stems and AAC by executing independent PCM checks."""
import argparse,json,subprocess as sp,hashlib
from pathlib import Path
import numpy as np, scipy.signal as sg

def decode(p,filter=None):
    cmd=['ffmpeg','-v','error','-i',str(p),'-map','0:a:0','-ar','48000','-ac','2']
    if filter:cmd.extend(['-af',filter])
    cmd.extend(['-f','f32le','-']);return np.frombuffer(sp.check_output(cmd),'<f4').reshape(-1,2)

def sha(p):
    with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def rmsdb(a):
    return float(20*np.log10(max(1e-12,np.sqrt(np.mean(np.square(a,dtype=np.float64))))))

def delay(a,b):
    z=sg.correlate(a.astype(np.float64),b.astype(np.float64),mode='full',method='fft');return int(np.argmax(z)-len(b)+1)

def main():
    p=argparse.ArgumentParser();p.add_argument('--music',type=Path,required=True);p.add_argument('--delivery',type=Path,required=True);a=p.parse_args();d=a.delivery
    m=decode(d/'stems/music_full.flac'); a0=decode(d/'stems/ambience_full.flac'); z=decode(d/'stems/mix_full.flac'); aa=decode(d/'green_tea_gate3.m4a')
    x=decode(a.music,'aresample=48000,bass=g=-1.5:f=150:w=0.7');n=len(x);s=len(m)
    proj=(np.sum(m[:n]*x,dtype=np.float64)/np.sum(x**2,dtype=np.float64));r=m[:n]-proj*x
    mismatch=z-(m+a0);audible=aa[:s];lag_records={}
    for t in [.08,2.,13.,24.,36.,47.,48.,49.,63.,95.,96.,97.,120.,143.,144.,145.,159.6,169.3,177.,185.,189.5,190.4]:
        i=round(48000*t);j=i+12000
        lag_records[str(t)]={'source_to_music_stem_sampling_lag':delay(x[i:j,0],m[i:j,0]),'lossless_mix_to_aac_sampling_lag':delay(audible[i:j,0],z[i:j,0]),'music_i_sample_rms_dbfs':round(rmsdb(m[i:j]),3),'audible_aac_rms_dbfs':round(rmsdb(audible[i:j]),3)}
    assert n==9466286 and s==9467200 and sha(a.music)=='f6feac60dc29b89ea1513e04d0b30addf86f9c8576827e7566e27b5abd522e71'
    assert np.max(abs(r))<1.0e-6 and np.max(abs(m[n:]))==0 and np.max(abs(mismatch))<1.e-6
    assert all(x['source_to_music_stem_sampling_lag']==0 and abs(x['lossless_mix_to_aac_sampling_lag'])<=1 for x in lag_records.values());assert np.max(abs(aa))<1
    report={'whole_original_match_samples':n,'music_stem_gain_db_fit':round(float(20*np.log10(proj)),7),'music_stem_eq_and_gain_residual_peak':float(np.max(abs(r))),'zero_silence_padding_frames':s-n,'print_master_compare_for_stem_sum_peak_residual':float(np.max(abs(mismatch))),'aac_decode_whole_len':len(aa),'aac_input_peak':float(np.max(abs(aa))),'aac_decoded_vs_lossless_print_snr_db':round(rmsdb(z)-rmsdb(audible-z),4),'test_22_independent_quarter_second_checkpoints':lag_records}
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
