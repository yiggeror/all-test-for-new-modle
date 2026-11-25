"""Actual final-mux evidence coordinates: 30fps film frame indexes."""
SAMPLES=(
 ('head_black_F0000',0),('head_fade_F0022',22),('head_full_F0045',45),
 ('spring_warm_cat_pause_F0120',120),('spring_true_turn_F0150',150),('spring_right_pivot_F0315',315),
 ('spring_summer_start_F1410',1410),('spring_summer_center_F1440',1440),('spring_summer_end_F1470',1470),
 ('summer_wet_warm_light_F1534',1534),('summer_car_warm_light_F1563',1563),('summer_neon_in_dip_F1604',1604),
 ('summer_autumn_start_F2850',2850),('summer_autumn_center_F2880',2880),('summer_autumn_end_F2910',2910),
 ('autumn_lean_cardigan_F2940',2940),('autumn_wind_and_hair_start_F2990',2990),
 ('autumn_girl_page_rise_F2995',2995),('autumn_girl_page_cross_F3005',3005),
 ('autumn_girl_hair_return_F3010',3010),('autumn_girl_page_settle_F3030',3030),
 ('autumn_ground_and_air_F3022',3022),('autumn_lamp_notch_F3055',3055),
 ('autumn_winter_start_F4290',4290),('autumn_winter_center_F4320',4320),('autumn_winter_end_F4350',4350),
 ('winter_banner_F4440',4440),('winter_separate_page_F4455',4455),('winter_lamp_notch_F4495',4495),
 ('tail_start_F5802',5802),('tail_fade_F5870',5870),('tail_black_F5916',5916),
)
CUE_DETAIL={
 'scope':'Final MP4 actual full resolution decoded H.264. Film frame indices are zero-based.',
 'picture_loop_origins':{'spring':0,'summer':1410,'autumn':2850,'winter':4290},
 'locked_v25_preencode_rgb_ranges_inclusive':[[0,2850],[4350,5916]],
 'autumn':{'lean_local':90,'hair_gust_local_inclusive':[140,160],'page_turn_local_inclusive':[145,180],
           'lean_film':2940,'hair_gust_film_inclusive':[2990,3010],'page_turn_film_inclusive':[2995,3030],
           'page_over_hinge_film':3005,'organic_crown_air_and_ground_sample_F3022':3022},
 'summer':{'neon_4_windows_film_half_open':[[1602,1607],[1614,1619],[1626,1630],[1639,1644]]},
 'dissolves':[[1410,1440,1470],[2850,2880,2910],[4290,4320,4350]],
 'ends':{'head_last_frame':45,'tail_first':5802,'last_black':5916,'duration_seconds_exact':'5917/30'},
}
