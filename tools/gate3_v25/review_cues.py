"""Unadorned, actual post-mux QC frame samples at known film coordinates."""
SAMPLES=(
    ('head_black_F0000',0),('head_fade_F0022',22),('head_full_F0045',45),
    ('spring_warm_cat_pause_F0120',120),('spring_true_turn_F0150',150),
    ('spring_return_F0265',265),('spring_right_pivot_F0315',315),('spring_repeat_F0330',330),
    ('spring_summer_start_F1410',1410),('spring_summer_center_F1440',1440),('spring_summer_end_F1470',1470),
    ('summer_wet_warm_light_F1534',1534),('summer_car_warm_light_F1563',1563),
    ('summer_neon_in_dip_F1604',1604),
    ('summer_autumn_start_F2850',2850),('summer_autumn_center_F2880',2880),('summer_autumn_end_F2910',2910),
    ('autumn_reader_chest_F2945',2945),('autumn_page_rise_F2995',2995),
    ('autumn_page_cross_F3005',3005),('autumn_page_return_F3035',3035),
    ('autumn_curb_and_leaves_F3022',3022),('autumn_lamp_notch_F3055',3055),
    ('autumn_winter_start_F4290',4290),('autumn_winter_center_F4320',4320),('autumn_winter_end_F4350',4350),
    ('winter_banner_F4440',4440),('winter_separate_page_F4455',4455),('winter_lamp_notch_F4495',4495),
    ('tail_start_F5802',5802),('tail_fade_F5870',5870),('tail_black_F5916',5916),
)
CUE_DETAIL={
    'input_picture_scope':'Full resolution final-mux decoded H.264 pixels without overlays or proxies.',
    'picture_loop_origins':{'spring':0,'summer':1410,'autumn':2850,'winter':4290},
    'spring':{'cat_warm_courtyard':[120,150,265,315,330], 'lamp_drop_local_half_open':[138,144]},
    'summer':{'neon_4_windows_film_half_open':[[1602,1607],[1614,1619],[1626,1630],[1639,1644]],'check':[1534,1563,1604]},
    'autumn':{'reader_turn_local':[145,185],'reader_turn_film':[2995,3035],
              'curb_air_anchors':[3022,3055],'reader_pose_and_paper_samples':[2945,2995,3005,3035]},
    'winter':{'check':[4440,4455,4495],'lamp_drop_film_half_open':[4493,4499]},
    'dissolves':[[1410,1440,1470],[2850,2880,2910],[4290,4320,4350]],
    'ends':{'head_last_frame':45,'tail_first':5802,'last_black':5916,'duration_seconds_exact':'5917/30'},
}
