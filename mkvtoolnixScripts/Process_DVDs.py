# Python script for using mediainfo to process a DVD rips
# processing includes: removing forced subtitles, setting title and updating audio track names
# Load list of files in directory and run mediainfo on each valid file, 
# files are valid if they are .mkv and not being written to after 30 seconds
# Subtitles:
# if mediainfo finds S_VOBSUB subtitles that are "Default track" and "Forced display"
# then mkvpropedit is run to remove the forced flags
# Title:
# if mkvinfo does not find the correct title then mkvpropedit is run to set the title
# Audio Tracks:
# if mkvinfo finds audio tracks that are not named correctly then mkvpropedit is run to set the name
# based off of the codec, channels, and bitrate (if available)

import os
import subprocess
import re
import time
import json

# MKVtoolnix location
mkvtoolnix = '/usr/bin/'

# Search location
search_dir = '/storage/Output/DVD'

# Seach through list of files and remove any that are not .mkv and any that are still being written to
# by comparing the file size to the size of the file 30 seconds ago
potential_files = []
# Loop through list of files from search location, save potential files to list as (file, size)
for file in os.listdir(search_dir):
    if file.endswith('.mkv'):
        potential_files.append((file, os.path.getsize(search_dir + '/' + file)))
# wait 30 seconds
time.sleep(30)
file_list = []
# Loop through list of potential files, skipping any that are still being written to
# adding any that are still the same size to the list of valid files
for file in potential_files:
    if file[1] != os.path.getsize(search_dir + '/' + file[0]):
        print('File still being written to: ' + file[0])
    else:
        file_list.append(file[0])

# Loop through list of valid files
for file in file_list:
    # Run mediainfo on file
    mediainfo = subprocess.Popen([mkvtoolnix + 'mediainfo', search_dir + '/' + file, '--Output=JSON'], stdout=subprocess.PIPE)
    # Read output from mediainfo and convert from bytes to string and save JSON to variable
    # Convert JSON to dictionary
    output = json.loads(mediainfo.stdout.read().decode('utf-8'))
    ### Subtitle section ###
    # Search output for S_VOBSUB tracks
    if re.search('S_VOBSUB', output):
        # Search output for "Default track" and "Forced display"
        if re.search('Default track', output) and re.search('Forced display', output):
            # print(output)
            # Run mkvpropedit to remove forced flags
            print('Forced subtitles found: ' + file)
            mkvpropedit_subtitles = subprocess.Popen([mkvtoolnix + 'mkvpropedit', search_dir + '/' + file, '--edit', 'track:s1', '--set', 'flag-forced=0', '--set', 'flag-default=0'], stdout=subprocess.PIPE)
            # Wait for mkvpropedit to finish
            mkvpropedit_subtitles.wait()
            # # Read output from mkvpropedit and convert from bytes to string
            mkvpropedit_subtitles_output = mkvpropedit_subtitles.stdout.read().decode('utf-8')
            if 'Done.' in mkvpropedit_subtitles_output:
                print('Done.')
            else:
                print('Error: ' + mkvpropedit_subtitles_output)
    ### Title section ###
    # Determine if file is a movie or a TV show by looking for the pattern SxxExx to determine full title
    if re.search('S\d\dE\d\d', file):
        # Split file name into parts on ' - ' and remove extension, save 1st and 3rd parts as Show: Episode Name
        # Set title
        title = file.split(' - ')[0] + ': ' + file.split(' - ')[2].split('.')[0]
    else:
        # Split file name into parts on ' - ' and remove extension, save 1st part as title
        title = file.split(' - ')[0].split('.')[0]
    # Determine if Title property exists and is correct
    if re.search('Title: ' + title, output):
        pass
    else:
        print('Setting title: ' + file)
        # Run mkvpropedit to set title
        mkvpropedit_title = subprocess.Popen([mkvtoolnix + 'mkvpropedit', search_dir + '/' + file, '--edit', 'info', '--set', 'title=' + title], stdout=subprocess.PIPE)
        # Wait for mkvpropedit to finish
        mkvpropedit_title.wait()
        # # Read output from mkvpropedit and convert from bytes to string
        mkvpropedit_title_output = mkvpropedit_title.stdout.read().decode('utf-8')
        if 'Done.' in mkvpropedit_title_output:
            print('Done.')
        else:
            print('Error: ' + mkvpropedit_title_output)
    ### Audio Track section ###
    # Search output for audio tracks by parsing the output of mkvinfo line by line starting with "+ Tracks"
    # If line begins with "| + Track" add to a list for the current track
    # Break out of the loop when reaching either "| + Track" or "|+ Tags" as these are the next sections
    # Loop through list of tracks
    for line in output:
        # Look for line that is the start of the Tracks section "| + Tracks"
        if re.search('\| \+ Tracks', line):
            # Create list for current track
            track = []
            # Loop through lines until reaching either "| + Track" or "|+ Tags" as these are the next sections
            while not re.search('\| \+ Track', line) or not re.search('\| \+ Tags', line):
                # Add line to list for current track
                track.append(line)
                # Read next line from output
                line = next(output)
            # Check if current track is an audio track before continuing by looking for "Track type: audio"
            if re.search('Track type: audio', track):
                # Loop through list of lines for current track and save data
                track_object = {}
                for line in track:
                    # Split line on ": " and save as key and value, removing leading and trailing whitespace along with characters before "+ " on the key
                    track_object[line.split(': ')[0].split('+ ')[1].strip()] = line.split(': ')[1].strip()
                # Check if track is named correctly
                # Determing what correct track name should be based off of codec, channels, and bitrate (if available)
                # Example track name: "AC3 5.1" or "DTS-HD MA 7.1"
                # Determine channel value
                if track_object['Channels'] == '6':
                    channel = '5.1'
                elif track_object['Channels'] == '8':
                    channel = '7.1'
                elif track_object['Channels'] == '3':
                    channel = '2.1'
                elif track_object['Channels'] == '2':
                    channel = 'Stereo'
                elif track_object['Channels'] == '1':
                    channel = 'Mono'
                else:
                    channel = 'Unknown'
                if track_object['Codec ID'].startswith('A_DTS'):
                    # Check if track has bitrate to determine if it is DTS or DTS-HD MA
                    if 'Bit depth' in track_object:
                        pass
                correct_track_name = track_object['Codec ID'].split('_')[1].strip() + ' ' + channel
                # Check if track name is correct
                if track_object['Name'] != correct_track_name:
                    # Run mkvpropedit to set track name
                    print('Setting track name: ' + file + ' - ' + track_object['Name'] + ' - ' + correct_track_name)
                    mkvpropedit_track_name = subprocess.Popen([mkvtoolnix + 'mkvpropedit', search_dir + '/' + file, '--edit', 'track:a' + track_object['Track number'], '--set', 'name=' + correct_track_name], stdout=subprocess.PIPE)
                    # Wait for mkvpropedit to finish
                    mkvpropedit_track_name.wait()
                    # # Read output from mkvpropedit and convert from bytes to string
                    mkvpropedit_track_name_output = mkvpropedit_track_name.stdout.read().decode('utf-8')
                    if 'Done.' in mkvpropedit_track_name_output:
                        print('Done.')
                    else:
                        print('Error: ' + mkvpropedit_track_name_output)
