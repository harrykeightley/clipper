import os
import sys
import argparse
import subprocess
from datetime import datetime, timedelta

def check_paths(video, input_file, output_folder):
    return os.path.isfile(video) and os.path.isfile(input_file) and os.path.isdir(output_folder)

def truncate_seconds(time):
    x = time.split(':')
    x[-1] = str(round(float(x[-1])))
    return ':'.join(x)

def parse_clip_line(line):
    try:
        start, end = line.split('-')
    except ValueError:
        print('ERROR: invalid input file', file=sys.stderr)
        exit(2)

    start = truncate_seconds(start)
    end = truncate_seconds(end)

    format_str = "%H:%M:%S"
    start = datetime.strptime(start, format_str)
    end = datetime.strptime(end, format_str)

    # start = timedelta(hours=start.hour, minutes=start.minute, seconds=start.second)
    # end = timedelta(hours=end.hour, minutes=end.minute, seconds=end.second)

    return (start, end)


def get_clips_from_file(input_file):
    result = []
    with open(input_file) as info:
        for line in info:
            if line.strip() == '':
                continue
            result.append(parse_clip_line(line.strip()))
            
    return result

def get_keyframes(frame_output):
    # filter irrelevant lines
    keyframes = [x.split('=')[-1].strip() for x in frame_output.split('\n') if x.startswith('pkt_pts')]

    # convert to time deltas
    keyframes = [timedelta(seconds=float(x)) for x in keyframes]
    keyframes = [str(x) for x in keyframes]
    print(keyframes)

    # properly pad all keyframes
    padded_keyframes = []
    for frame in keyframes:
        x = frame.split(':')
        x[0] = x[0].zfill(2)
        padded_keyframes.append(':'.join(x))

    keyframes = [datetime.strptime(str(x), '%H:%M:%S.%f') for x in padded_keyframes if '.' in str(x)]

    # edge case
    if '.' not in str(padded_keyframes[0]):
        keyframes = [datetime.strptime('00:00:00', '%H:%M:%S')] + keyframes

    return keyframes

def get_previous_keyframe(keyframes, time, index=0):
    while keyframes[index] < time:
        index += 1
    
    return keyframes[index - 1] - timedelta(milliseconds=34), index


def main(args):
    # get clip timings from input file
    clips = get_clips_from_file(args.input_file)

    print("Generating keyframes")
    command = f'ffprobe -select_streams v -skip_frame nokey -show_frames -show_entries frame=pkt_pts_time,pict_type {args.video}'
    out = subprocess.Popen(command.split(), 
           stdout=subprocess.PIPE, 
           stderr=subprocess.STDOUT)
    a, b = out.communicate()
    key_frames = get_keyframes(a.decode('ascii'))

    print("Reading clip info")
    
    # replace all starts with the nearest previous keyframe
    adjusted_clips = []
    index = 0
    for (start, end) in clips:
        key, index = get_previous_keyframe(key_frames, start, index)
        adjusted_clips.append((key, end))
    
    # call ffmpeg on those clips and store them in output_folder
    for i, (start, end) in enumerate(adjusted_clips, start=1):
        print(start, end)
        delta = (end - start).seconds
        print(delta)
        out = os.path.join(args.output, f"clip{i}.mp4")
        start_time = start.strftime("%H:%M:%S.%f")
        print(start)
        command = f'ffmpeg -i {args.video} -ss {start_time} -t {delta} -c copy {out}'
        os.system(command)
        


    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Split file into clips based on an input file')
    parser.add_argument('video', type=str,
                        help='a video to split up')
    parser.add_argument('input_file',
                        help='file containing clip split information')
    parser.add_argument('-o', '--out', dest='output', default=os.getcwd(),
                        help='The output folder to populate with clips. Defaults to cwd')
    #parser.add_argument('--version', action='version', version='%(prog)s 0.1')
    args = parser.parse_args()

    if not check_paths(args.video, args.input_file, args.output):
        parser.print_help()
        parser.exit(status=1, message='ERROR: Invalid path for one of arguments\n')

    main(args)
