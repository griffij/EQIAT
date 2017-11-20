"""Plot all the figures at once
"""
import sys, os
from glob import glob
from pipes import quote

filelist = glob(os.path.join('outputs', '*.csv'))

bbox_dict = {1699: '104/113/-9/-5',
             1834: '105/110/-8/-5',
             1840: '105/115/-9/-5',
             1847: '104/115/-9/-5',
             1867: '105/115/-9/-5',
             1815: '110/126/-10/-5',
             1818: '110/126/-10/-5',
             1820: '110/126/-10/-5'}

for filename in filelist:
    #outbase = filename.rstrip(r"().csv")
    split = filename.split('_')
    if split[3] != 'mmi':
        continue
    event = split[4][0:4]
    print event
    bbox = bbox_dict[int(event)]
    mmi_obs_file = 'data/' + event + 'HMMI.txt'
    filename = quote(filename) # Deal with nasty () in filename
    cmd = 'python plot_maps.py %s %s %s' %(
        mmi_obs_file, filename, bbox)
    print cmd
    os.system(cmd)