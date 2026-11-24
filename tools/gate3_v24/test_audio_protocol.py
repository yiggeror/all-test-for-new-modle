import json, tempfile, unittest
from pathlib import Path

import audio_protocol as a


class Gate34AudioProtocol(unittest.TestCase):
    def packets(self):
        return [{"pts":(i-1)*1024,"dts":(i-1)*1024,"duration":320 if i==9246 else 1024,
                 "size":"384","flags":"KD" if i==0 else "K_","data_hash":f"SHA256:{i:064x}",
                 **({"side_data_list":[{"side_data_type":"Skip Samples","skip_samples":1024,"discard_padding":0,
                                       "skip_reason":0,"discard_reason":0}]} if i==0 else {})} for i in range(9247)]

    def probe(self):
        return {"streams":[{"codec_type":"audio","codec_name":"aac","profile":"LC","sample_rate":"48000","channels":2,
                "time_base":"1/48000","start_pts":0,"duration_ts":9467200,"bit_rate":"248600","extradata_hash":'SHA256:'+'a'*64}],
                "packets":self.packets()}

    def test_full_sample_exact_aac_contract(self):
        r=a.packet_identity(self.probe())
        self.assertEqual(r['effective_samples'],9467200)
        self.assertEqual(r['packet_count'],9247)
        self.assertEqual(r['priming_samples'],1024)
        self.assertEqual(r['last_packet_duration_samples'],320)

    def test_one_shifted_packet_or_suffix_is_not_accepted(self):
        doc=self.probe(); doc['packets'][114]['pts']+=1
        with self.assertRaisesRegex(ValueError,'114'): a.packet_identity(doc)
        d=self.probe();d['packets'][-1]['duration']=319
        with self.assertRaisesRegex(ValueError,'9246'): a.packet_identity(d)

    def test_one_payload_or_config_change_changes_identity(self):
        o=self.probe(); ref=a.packet_identity(o)
        o['packets'][650]['data_hash']='SHA256:'+'9'*64
        self.assertNotEqual(a.packet_identity(o),ref)
        o=self.probe(); o['streams'][0]['extradata_hash']='SHA256:'+'b'*64
        self.assertNotEqual(a.packet_identity(o),ref)

    def test_all_sources_are_path_checked_and_hash_locked(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'prior.mp4';p.write_bytes(b'this is not the full song')
            with self.assertRaisesRegex(ValueError,'原曲'):
                a.acquire_author_track(Path(t)/'not-written.mp3',p)
            self.assertFalse((Path(t)/'not-written.mp3').exists())
            self.assertEqual(p.read_bytes(),b'this is not the full song')

    def test_preserve_all_samples_and_localized_tail_report(self):
        sha='f'*64
        report={
          "source":{"sha256":a.MUSIC_SHA256,"complete_unchanged_samples":9466286,"alignment_zero_pad_samples":914},
          "legacy_recipe_sha256":a.LEGACY_AUDIO_SHA256,
          "prefix_PCM_before_weather_change":{"exact_samples_per_channel":8_880_000,"byte_identical_before_after":True},
          "winter_weather":{"onset_rise_plateau_fade_finish_sample_positions":[8_880_000,9_225_600,9_336_000,9_465_600,9_467_200],
              "raised_db_relative_to_tail_anchor":8.,"measured_plateau_minus_anchor_ungated_dB":7.6},
          "timing":{"audio_samples_per_channel":9467200,"video_frames":5917,"fps":30},
          "encoded_aac":{"sha256":sha,"alignment_lag_samples":0,"decoded_black_peak_dBFS":-123.,
            "meter":{"integrated_lufs":-16.05,"true_peak_dbtp":-4.74}},
        }
        a.validate_mix_report(report,sha)
        report["source"]["complete_unchanged_samples"]-=1
        with self.assertRaisesRegex(ValueError,'全曲'):a.validate_mix_report(report,sha)


if __name__=='__main__':unittest.main()
