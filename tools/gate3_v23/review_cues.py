"""Frame evidence points for the approved Round 13 cut."""

SAMPLES = (
    ('head_fade_F022',22),
    ('spring_petals_F180',180),
    ('spring_laundry_F195',195),
    ('spring_summer_F1440',1440),
    ('summer_wet_warm_light_F1534',1534),
    ('summer_car_warm_light_F1563',1563),
    ('summer_neon_stable_F1601',1601),
    ('summer_neon_dip_F1604',1604),
    ('summer_autumn_F2880',2880),
    ('autumn_crosswalk_leaves_F2972',2972),
    ('autumn_birds_F3002',3002),
    ('autumn_tea_steam_F3028',3028),
    ('autumn_winter_F4320',4320),
    ('winter_fixed_facade_F4385',4385),
    ('winter_page_turn_F4455',4455),
    ('winter_snow_F4504',4504),
    ('tail_fade_F5870',5870),
)
CUE_DETAIL={
    'source_film_track':'Actual final mux H.264 decoded at full 1920×1080, no overlays; no compatibility proxy.',
    'source_phases_are_zero_based':True,
    'spring':{'origin':0,'phase_180_film':180,'phase_195_film':195,'checks':['fixed tree','lit petals','visible cloth pose']},
    'summer':{'origin':1410,'phase_124_film':1534,'phase_153_film':1563,
              'neon_4_windows_film_half_open':[[1602,1607],[1614,1619],[1626,1630],[1639,1644]],
              'still_stable_and_dip_film':[1601,1604],
              'checks':['warm ground then car sweep','synchronized net-bar sign, wall and wet road']},
    'autumn':{'origin':2850,'phase_to_film':{'122':2972,'152':3002,'178':3028},
              'checks':['ground leaves','bird wing and sky','steam near tea']},
    'winter':{'origin':4290,'phase_to_film':{'95':4385,'165':4455,'214':4504},
              'checks':['fixed distant windows','separated page and lamp','layered snow and smoke']},
}
