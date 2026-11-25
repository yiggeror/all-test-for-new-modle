"""30fps zero-based timestamps for full-cut winter evidence and seasonal boundaries."""

WINTER_ORIGIN=4290
WINTER_FOLEY_PHASES=(156,169)
WINDOW_NATIVE_XYWH=(242,98,32,24)
REVIEW_START=4384
REVIEW_FRAMES=330
SAMPLES=(
 ('head_black_F0000',0),('head_fade_F0022',22),('head_full_F0045',45),
 ('spring_cat_F0150',150),
 ('spring_summer_start_F1410',1410),('spring_summer_center_F1440',1440),('spring_summer_end_F1470',1470),
 ('summer_neon_F1604',1604),
 ('summer_autumn_start_F2850',2850),('summer_autumn_center_F2880',2880),('summer_autumn_end_F2910',2910),
 ('autumn_signoff_reader_F3005',3005),
 ('autumn_winter_start_F4290',4290),('autumn_winter_center_F4320',4320),('autumn_winter_end_F4350',4350),
 ('winter_banner_F4440',4440),('winter_reach_F4443',4443),('winter_pinch_F4446',4446),
 ('winter_turn_F4453',4453),('winter_flatten_F4459',4459),('winter_recover_F4482',4482),('winter_lamp_F4495',4495),
 ('tail_start_F5802',5802),('tail_fade_F5870',5870),('tail_black_F5916',5916),
)
CUE_DETAIL={
 'scope':'Stills and review clips decoded from the actual H.264/AAC release candidate on the 30fps zero-based timeline.',
 'picture_loop_origins':{'spring':0,'summer':1410,'autumn':2850,'winter':WINTER_ORIGIN},
 'locked_v27_preencode_rgb_range_inclusive':[0,4290],
 'winter_reader_phase':{'reach_pinch_inclusive':[144,155],'turn_press_inclusive':[156,174],'relax_inclusive':[175,192],
                         'paper_foley_centers':WINTER_FOLEY_PHASES},
 'winter_first_film_foley_frames':list(WINTER_ORIGIN+q for q in WINTER_FOLEY_PHASES),
 'winter_sfx_film_frames_each_complete_pair':[list(WINTER_ORIGIN+k*330+q for q in WINTER_FOLEY_PHASES) for k in range(5) if WINTER_ORIGIN+k*330+169 <5917],
 'full_speed_review_film_frame_half_open':[REVIEW_START,REVIEW_START+REVIEW_FRAMES],
 'full_speed_detail_crop_original_native_xywh':WINDOW_NATIVE_XYWH,
 'dissolves':[[1410,1440,1470],[2850,2880,2910],[4290,4320,4350]],
 'ends':{'head_last_frame':45,'tail_first':5802,'last_black':5916,'duration_seconds_exact':'5917/30'},
}
