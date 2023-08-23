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
import shutil

# Search location
HB_Output_root = '/storage/Handbrake/Output/'
# Source root
rips_source_root = '/storage/Handbrake/Rips/'
# Converted rips root
converted_rips_root = '/storage/Converted_Rips/'
# Destination root
dest_root = '/storage/Media_'
# Handbrake config/log directory
hb_dir = '/storage/Handbrake_cfg/'
# Disc types
disc_types = ['DVD', 'BD', 'UHD']

# Seach through list of files and remove any that are not .mkv and any that are still being written to
# by comparing the file size to the size of the file 30 seconds ago
def validate_files(search_directory):
    potential_files = []
    # Loop through list of files from search location, save potential files to list as (file, size)
    for file in os.listdir(search_directory):
        if file.endswith('.mkv'):
            potential_files.append((file, os.path.getsize(search_directory + '/' + file)))
    # wait 30 seconds
    time.sleep(30)
    file_list = []
    # Loop through list of potential files, skipping any that are still being written to
    # adding any that are still the same size to the list of valid files
    for file in potential_files:
        if file[1] != os.path.getsize(search_directory + '/' + file[0]):
            print('File still being written to: ' + file[0])
        else:
            file_list.append(file[0])
    return file_list

# Search output for S_VOBSUB tracks
def check_set_forced_subtitles(path_filename='', tracks=[]):
    for track in tracks:
        if track['@type'] == 'Text' and track['CodecID'] == 'S_VOBSUB':
            # Determine if current subtitle track is the default track and forced display
            if track['Default'] == 'Yes' and track['Forced'] == 'Yes':
                # print(output)
                # Run mkvpropedit to remove forced flags
                print('Removing forced subtitles found: ' + file, end='')
                # Use track number instead of track name from mediainfo, track number is more reliable
                mkvpropedit_subtitles = subprocess.Popen(['/usr/bin/mkvpropedit', path_filename, '--edit', 'track:' + track['ID'], '--set', 'flag-forced=0', '--set', 'flag-default=0'], stdout=subprocess.PIPE)
                # Wait for mkvpropedit to finish
                mkvpropedit_subtitles.wait()
                # # Read output from mkvpropedit and convert from bytes to string
                mkvpropedit_subtitles_output = mkvpropedit_subtitles.stdout.read().decode('utf-8')
                if 'Done.' in mkvpropedit_subtitles_output:
                    print(' Done.')
                else:
                    print(' Error: ' + mkvpropedit_subtitles_output)

def check_set_title(path_filename='', track0={}):
    # Get file name from path_filename
    filename = path_filename.split('/')[-1]
    # Determine if file is a movie or a TV show by looking for the pattern SxxExx to determine full title
    if re.search('S\d\dE\d\d', filename):
        # Split file name into parts on ' - ' and remove extension, save 1st and 3rd parts as Show: Episode Name
        # Set title
        title = filename.split(' - ')[0] + ': ' + filename.split(' - ')[2].split('.')[0]
        is_tv = True
    else:
        # Split file name into parts on ' - ' and remove extension, save 1st part as title
        title = filename.split(' - ')[0].split('.')[0]
        is_tv = False
    # Determine if Title property exists and is correct
    if 'Title' in track0 and track0['Title'] == title:
        pass
    else:
        print('Setting title: ' + title, end='')
        # Run mkvpropedit to set title
        mkvpropedit_title = subprocess.Popen(['/usr/bin/mkvpropedit', path_filename, '--edit', 'info', '--set', 'title=' + title], stdout=subprocess.PIPE)
        # Wait for mkvpropedit to finish
        mkvpropedit_title.wait()
        # # Read output from mkvpropedit and convert from bytes to string
        mkvpropedit_title_output = mkvpropedit_title.stdout.read().decode('utf-8')
        if 'Done.' in mkvpropedit_title_output:
            print(' Done.')
        else:
            print(' Error: ' + mkvpropedit_title_output)
    return is_tv, title

def check_set_audio_tracks(path_filename='', tracks=[]):
    # Loop through audio tracks
    for track in tracks:
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
            elif 'DTS' in track_name_codec:
                if 'Format_Commercial_IfAny' in track and 'DTS-HD Master Audio' in track['Format_Commercial_IfAny']:
                    track_name_codec = 'DTS-HD MA'
                else:
                    track_name_codec = 'DTS'
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
            if track['Title'] == track_name:
                pass
            else:
                print('Setting track name for track#: ' + track['ID'] + ' Name: ' + track_name, end='')
                # Run mkvpropedit to set track name
                mkvpropedit_track_name = subprocess.Popen(['/usr/bin/mkvpropedit', path_filename, '--edit', 'track:' + track['ID'], '--set', 'name=' + track_name], stdout=subprocess.PIPE)
                # Wait for mkvpropedit to finish
                mkvpropedit_track_name.wait()
                # # Read output from mkvpropedit and convert from bytes to string
                mkvpropedit_track_name_output = mkvpropedit_track_name.stdout.read().decode('utf-8')
                if 'Done.' in mkvpropedit_track_name_output:
                    print(' Done.')
                else:
                    print(' Error: ' + mkvpropedit_track_name_output)

def move_file(filename='', is_tv=False, title='', source_dir='', dest_dir=''):
    if is_tv:
        # Get season number from file name section SxxEyy and extract xx, strip leading 0 on season number if present
        show_name = title.split(':')[0]
        season_num = filename.split(' - ')[1].split('E')[0].replace('S', '').lstrip('0')
        # Verify show directory exists and create if it does not
        if not os.path.isdir(dest_dir + '/' + show_name):
            os.mkdir(dest_dir + '/' + show_name)
        # Verify season directory exists and create if it does not
        if not os.path.isdir(dest_dir + '/' + show_name + '/Season ' + season_num):
            os.mkdir(dest_dir + '/' + show_name + '/Season ' + season_num)
            # Set destination directory to show/season directory
            dest_dir = dest_dir + '/' + show_name + '/Season ' + season_num
    # Move file to destination location
    print('Moving file: ' + filename + ' to: ' + dest_dir + '/' + filename, end='')
    shutil.move(source_dir + '/' + filename, dest_dir + '/' + filename)
    print(' Done.')

def move_source_file(filename='', dest_dir=''):
    # Move file to Converted_Rips directory for final storage
    # Add any missing parent directories
    if not os.path.isdir(dest_dir):
        os.makedirs(dest_dir)
    # Move file to destination location
    # Set destination filename by stripping source directory from filename
    dest_filename_w_path = dest_dir + '/' + filename.split('/')[-1]
    print('Moving file: ' + filename + ' to: ' + dest_filename_w_path, end='') 
    shutil.move(filename, dest_filename_w_path)
    print(' Done.')

def get_handbrake_log(search_directory=''):
    # Get handbrake log file from search directory
    # File name format Activity.log.x
    # Get list of files in search directory
    file_list = os.listdir(search_directory)
    # Loop through list of files and find the handbrake log file
    for file in file_list:
        if 'Activity' in file:
            hb_log = file
    return hb_log

def get_json_from_hb_log(hb_log=''):
    # Read handbrake log file and convert to JSON sections for each title
    # Save JSON sections to list
    json_list = []
    # Open handbrake log file
    with open(hb_dir + hb_log, 'r') as hb_log_file:
        # Read handbrake log file
        hb_log_file_contents = hb_log_file.read()
        # Split handbrake log file into sections for each title
        hb_log_file_contents_split = hb_log_file_contents.split('json job:\n')
        # Remove first section of handbrake log file
        hb_log_file_contents_split.pop(0)
        # Loop through list of sections and convert to JSON
        for section in hb_log_file_contents_split:
            temp_json_data = []
            for line in section.split('\n'):
                # if timestamp in line then break out of loop otherwise add line to temp_json_data
                # timestamp is in the format at the beginning of the line: [00:00:00]
                if re.search('^\[\d\d:\d\d:\d\d\]', line):
                    break
                else:
                    temp_json_data.append(line)
            json_list.append(json.loads('\n'.join(temp_json_data)))
    return json_list

def get_json_from_filename(json_list=[], filename=''):
    # Loop through list of JSON sections and get title
    most_recent_json = {}
    for json_section in json_list:
        # Check if filename matches
        if json_section['Destination']['File'].split('/')[-1] == filename:
            most_recent_json = json_section
    return most_recent_json

# Get handbrake log file
hb_log = get_handbrake_log(search_directory=hb_dir)
# Get JSON from handbrake log file
json_list = get_json_from_hb_log(hb_log=hb_log)

# Process files for each disc type
for disc_type in disc_types:
    # Search location
    search_dir = HB_Output_root + disc_type
    # Get list of valid files
    file_list = validate_files(search_dir)
    #
    # Loop through list of valid files
    for file in file_list:
        # Set output filename as source file with full path
        output_filename = search_dir + '/' + file
        # Run mediainfo on file
        print('Running mediainfo on file: ' + file)
        mediainfo = subprocess.Popen(['/usr/bin/mediainfo', output_filename, '--Output=JSON'], stdout=subprocess.PIPE)
        # Read output from mediainfo and convert from bytes to string and save JSON to variable
        # Convert JSON to dictionary
        output = json.loads(mediainfo.stdout.read().decode('utf-8'))
        # Get title from JSON
        hb_json_job = get_json_from_filename(json_list=json_list, filename=file)
        if hb_json_job == {}:
            # Raise error if no JSON found
            raise Exception('No JSON found for file: ' + file)
        ### Subtitle section ###
        # Search for forced subtitles
        check_set_forced_subtitles(path_filename=output_filename, tracks=output['media']['track'])
        ### Title section ###
        # Check title
        is_tv, title = check_set_title(path_filename=output_filename, track0=output['media']['track'][0])
        ### Audio Track section ###
        # Check audio tracks
        check_set_audio_tracks(path_filename=output_filename, tracks=output['media']['track'])
        ## Move file section ##
        # Determine destination location
        if is_tv:
            dest_dir = dest_root + disc_type + '_Series'
        else:
            dest_dir = dest_root + disc_type + '_Movies'
        # Move file to destination location on another share
        move_file(filename=file, is_tv=is_tv, title=title, dest_dir=dest_dir, source_dir=search_dir)
        # Determine storage location
        if is_tv:
            pass
        else:
            # Get subdirectory
            sub_dir = hb_json_job['Source']['Path'].split(disc_type)[1].split('/')[1]
            # Determine source file location, source file is the file that was ripped
            # Source file is in the format: /storage/Handbrake/Rips/DVD/Title/Title.mkv
            # stored in hb_json_job['Source']['path'], split on / and get last item
            source_file = rips_source_root + disc_type + '/' + sub_dir + '/' + hb_json_job['Source']['Path'].split('/')[-1]
            # Move source file to Converted_Rips directory
            move_source_file(filename=source_file, dest_dir=converted_rips_root + disc_type+ '/' + sub_dir)
            # if remove subdirectory from source folder if empty
            if not os.listdir(rips_source_root + disc_type + '/' + sub_dir):
                os.rmdir(rips_source_root + disc_type + '/' + sub_dir)