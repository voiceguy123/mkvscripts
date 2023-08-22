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
search_dir = '/storage/Handbrake/Output/DVD'

# Destination location for movies
dest_dir = '/storage/Media_DVD_Movies'

# Destination location for TV shows
dest_dir_tv = '/storage/Media_DVD_Series'

# Location of Converted Source files
rip_dest_dir = '/storage/Converted_Rips'

# Location of DVD rips
rip_source_dir = '/storage/Handbrake/Rips/DVD'

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
    for track in output['media']['track']:
        if track['@type'] == 'Text' and track['CodecID'] == 'S_VOBSUB':
            # Determine if current subtitle track is the default track and forced display
            if track['Default'] == 'Yes' and track['Forced'] == 'Yes':
                # print(output)
                # Run mkvpropedit to remove forced flags
                print('Forced subtitles found: ' + file)
                # Use track number instead of track name from mediainfo, track number is more reliable
                mkvpropedit_subtitles = subprocess.Popen([mkvtoolnix + 'mkvpropedit', search_dir + '/' + file, '--edit', 'track:' + track['ID'], '--set', 'flag-forced=0', '--set', 'flag-default=0'], stdout=subprocess.PIPE)
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
        is_tv = True
    else:
        # Split file name into parts on ' - ' and remove extension, save 1st part as title
        title = file.split(' - ')[0].split('.')[0]
        is_tv = False
    # Determine if Title property exists and is correct
    if 'Title' in output['media']['track'][0] and output['media']['track'][0]['Title'] == title:
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
    # Loop through audio tracks
    for track in output['media']['track']:
        # Determine if track is an audio track
        if track['@type'] == 'Audio':
            # Determine if track name is correct
            # Track name should be in the format: Codec Channels(.1) Codec Name
            # Example: DTS-HD MA 5.1, AC3 2.1 Dolby Surround, AAC Stereo
            # Determine track name codec portion
            # Strip leading A_ from CodecID and if codec contains AAC then codec name = AAC
            track_name_codec = track['CodecID'].replace('A_', '')
            if 'AAC' in track_name_codec:
                track_name_codec = 'AAC'
            # Determine channels
            if track['Channels'] == '2':
                # if Codec AAC then channels = Stereo, else channels = 2.0
                if 'AAC' in track['CodecID']:
                    channels = 'Stereo'
                else:
                    channels = '2.0'
            elif track['Channels'] == '1':
                channels = 'Mono'
            else:
                channels = str(int(track['Channels']) -1) + '.1'
            # Determine if track name is correct
            track_name = track_name_codec + ' ' + channels
            print(track_name)
            if track['Title'] == track_name:
                pass
            else:
                print('Setting track name: ' + file + ' Track: ' + track['ID'] + ' Name: ' + track_name)
                # Run mkvpropedit to set track name
                mkvpropedit_track_name = subprocess.Popen([mkvtoolnix + 'mkvpropedit', search_dir + '/' + file, '--edit', 'track:' + track['ID'], '--set', 'name=' + track_name], stdout=subprocess.PIPE)
                # Wait for mkvpropedit to finish
                mkvpropedit_track_name.wait()
                # # Read output from mkvpropedit and convert from bytes to string
                mkvpropedit_track_name_output = mkvpropedit_track_name.stdout.read().decode('utf-8')
                if 'Done.' in mkvpropedit_track_name_output:
                    print('Done.')
                else:
                    print('Error: ' + mkvpropedit_track_name_output)
    # Move file to destination location on another share
    print('Moving file: ' + file)
    if is_tv:
        # Verify show directory exists and create if it does not
        if not os.path.isdir(dest_dir_tv + '/' + title.split(':')[0]):
            os.mkdir(dest_dir_tv + '/' + title.split(':')[0])
            # Get season number from file name section SxxEyy and extract xx
            season = file.split(' - ')[1].split('E')[0].replace('S', '')
            # Verify season directory exists and create if it does not
            if not os.path.isdir(dest_dir_tv + '/' + title.split(':')[0] + '/Season ' + season):
                os.mkdir(dest_dir_tv + '/' + title.split(':')[0] + '/Season ' + season)
                # Set destination directory to show/season directory
                dest_dir_tv = dest_dir_tv + '/' + title.split(':')[0] + '/Season ' + season
        # Move file to destination location
        print(dest_dir_tv + '/' + file)
        os.shutil.move(search_dir + '/' + file, dest_dir_tv + '/' + file)
    else:
        os.shutil.move(search_dir + '/' + file, dest_dir + '/' + file)
        pass
