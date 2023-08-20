# Python script for using mkvinfo to remove forced subtitles from a DVD rip
# Load list of files in directory and run mkvinfo on each file
# if mkvinfo finds S_VOBSUB subtitles that are "Default track" and "Forced display"
# then mkvpropedit is run to remove the forced flags

import os
import subprocess
import re

# MKVtoolnix location
mkvtoolnix = '/usr/bin/'

# Search location
search_dir = '/storage/Output/DVD'

# Get list of files in directory
file_list = os.listdir(search_dir)

# Loop through list of files
for file in file_list:
    # Run mkvinfo on file
    mkvinfo = subprocess.Popen([mkvtoolnix + 'mkvinfo', search_dir + '/' + file], stdout=subprocess.PIPE)
    # Read output from mkvinfo and convert from bytes to string
    output = mkvinfo.stdout.read().decode('utf-8')
    # Determine if file is a movie or a TV show by looking for the pattern SxxExx to determine full title
    if re.search('S\d\dE\d\d', file):
        # Split file name into parts on ' - ' and remove extension, save 1st and 3rd parts as Show: Episode Name
        show, episode = file.split(' - ')[0], file.split(' - ')[2].split('.')[0]
        # Set title
        title = show + ': ' + episode
    else:
        # Split file name into parts on ' - ' and remove extension, save 1st part as title
        title = file.split(' - ')[0].split('.')[0]
    # Determine if Title property exists and is correct
    if re.search('Title: ' + title, output):
        set_title = False
    else:
        set_title = True
    # Search output for S_VOBSUB tracks
    if re.search('S_VOBSUB', output):
        # Search output for "Default track" and "Forced display"
        if re.search('Default track', output) and re.search('Forced display', output):
            # print(output)
            # Run mkvpropedit to remove forced flags
            if set_title:
                print('Forced subtitles and incorrect title found: ' + file)
                title_value = 'title=' + title
                mkvpropedit = subprocess.Popen([mkvtoolnix + 'mkvpropedit', search_dir + '/' + file, '--edit', 'track:s1', '--set', 'flag-forced=0', '--set', 'flag-default=0', '--edit', 'info', '--set', title_value], stdout=subprocess.PIPE)
                set_title = False
            else:
                print('Forced subtitles found: ' + file)
                mkvpropedit = subprocess.Popen([mkvtoolnix + 'mkvpropedit', search_dir + '/' + file, '--edit', 'track:s1', '--set', 'flag-forced=0', '--set', 'flag-default=0'], stdout=subprocess.PIPE)
            # Wait for mkvpropedit to finish
            mkvpropedit.wait()
            # # Read output from mkvpropedit and convert from bytes to string
            mkvpropedit_output = mkvpropedit.stdout.read().decode('utf-8')
            if 'Done.' in mkvpropedit_output:
                print('Done.')
            else:
                print('Error: ' + mkvpropedit_output)
        else:
            print('No forced subtitles found: ' + file)
    else:
        print('No subtitles found in file: ' + file)
    # if title still needs to be set
    if set_title:
        print('Setting title: ' + file)
        # Run mkvpropedit to set title
        mkvpropedit = subprocess.Popen([mkvtoolnix + 'mkvpropedit', search_dir + '/' + file, '--edit', 'info', '--set', 'title=' + title], stdout=subprocess.PIPE)
        # Wait for mkvpropedit to finish
        mkvpropedit.wait()
        # # Read output from mkvpropedit and convert from bytes to string
        mkvpropedit_output = mkvpropedit.stdout.read().decode('utf-8')
        if 'Done.' in mkvpropedit_output:
            print('Done.')
