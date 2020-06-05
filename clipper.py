import os
import sys
import argparse
from datetime import datetime, timedelta

def check_paths(video, input_file, output_folder):
    return os.path.isfile(video) and os.path.isfile(input_file) and os.path.isdir(output_folder)

def parse_clip_line(line):
    #HH:MM:SS-HH:MM:SS
    try:
        start, end = line.split('-')
    except ValueError:
        print('ERROR: invalid input file', file=sys.stderr)
        exit(2)

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

def main(args):
    # get clip timings from input file
    clips = get_clips_from_file(args.input_file)

    # call ffmpeg on those clips and store them in output_folder
    for i, (start, end) in enumerate(clips, start=1):
        delta = (end - start).seconds
        out = os.path.join(args.output, f"clip{i}.mp4")
        command = f'ffmpeg -i {args.video} -ss {start.strftime("%H:%M:%S")} -t {delta} -c:v copy -c:a copy {out}'
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
