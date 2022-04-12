from locale import Error
from pywinauto.application import Application
import sys, re, os, subprocess, argparse, warnings

outputres = {'great':(240,160),'nice':(216,144),'lesser':(204,136),'compression':(192,128)}
bitrate = {'great':60,'nice':28,'lesser':12,'compression':8}
framerate = {'great':15,'nice':12,'lesser':7.5,'compression':6}
split = {'great':480,'nice':900,'lesser':1500,'compression':1800}


def perform_the_action(input_file, output_file, quality):
    # Consider making this executable location a flag.
    app = Application().start("meteo.exe")

    # print(app['Dialog'].print_control_identifiers())

    app['Dialog']['Edit1'].type_keys(input_file)
    app['Dialog']['Edit2'].type_keys(output_file)
    app['Dialog']['Edit4'].type_keys('{DELETE}{DELETE}{DELETE}'+str(bitrate[quality]))
    app['Dialog']['Manual  RadioButton'].click()
    app['Dialog']['AsptCheckBox'].click()
    app['Dialog']['WEdit'].type_keys('{DELETE}{DELETE}{DELETE}'+str(outputres[quality][0]))
    app['Dialog']['HEdit'].type_keys('{DELETE}{DELETE}{DELETE}'+str(outputres[quality][1]))
    app['Dialog']['FramrateComboBox'].type_keys('O')
    app['Dialog']['Pre-FilterComboBox'].type_keys('N')
    app['Dialog']['Pre-SpedCheckBox'].click()
    app['Dialog']['Button3'].click()

    while True:
        # Consider making this timeout a flag.
        app['Dialog']['Button3'].wait("ready", 600)
        t = app['Dialog']['Static2'].texts()[0]
        if 'replace it' in t:
            # Replace rom if already exists, consider making this a flag.
            app['Dialog']['Button1'].click()
        elif 'Output' in t:
            app.kill()
            return
        elif 'Input file error' in t:
            app.kill()
            raise FileNotFoundError()
        else:
            # I feel like this is an unrecoverable error. To be seen.
            print(t)
            raise Error("Unexpected message " + t)


# Returns a list of output files.
def call_ffmpeg(input_file, temp_folder, quality, duration):

    # Should title be a flag somehow?
    input_filename = os.path.split(input_file)[-1]
    title = re.sub(r"[^a-zA-Z0-9]","", input_filename[:-4])[0:12]

    

    output = []
    
    # Consider making this executable location a flag.
    # Consider overwriting the files to be a flag.
    ffmpegcommand = '.\\ffmpeg.exe -y -v quiet -i ' + '"{}"'.format(input_file) + ' '
    for i in range((duration//split[quality])+1):
        # framerate
        ffmpegcommand += '-r ' + str(framerate[quality]) + ' '
        # split at time
        ffmpegcommand += '-ss ' + str(i*split[quality]) + ' -t ' + str(min(duration-split[quality]*i, split[quality])) + ' '
        # cut subtitles
        ffmpegcommand += '-sn '
        # resize
        ffmpegcommand += '-vf "scale=w=' + str(outputres[quality][0]) + ':h=' + str(outputres[quality][1]) + ':force_original_aspect_ratio=decrease,pad='+ str(outputres[quality][0]) + ':' + str(outputres[quality][1]) + ':(ow-iw)/2:(oh-ih)/2,setpts=0.75*PTS" '
        # bitrate
        ffmpegcommand += '-b:v ' + str(bitrate[quality]) + 'k '
        # maybe dither
        ffmpegcommand += '-sws_dither bayer '
        # maybe speed
        ffmpegcommand += '-filter:a "atempo=1.33333" '
        # output file
        ffmpegcommand += os.path.join(temp_folder, title + '_part_' + str(i) + '.avi ')
        output += [title + '_part_' + str(i)]
    # print(ffmpegcommand)
    subprocess.run(ffmpegcommand,stderr=sys.stdout)

    return output


def main():

    warnings.simplefilter('ignore', category=UserWarning)

    input_file = None
    input_file_folder = None
    output_folder = None
    quality = None
    temp_folder = None
    duration = None

    parser = argparse.ArgumentParser()
    parser.add_argument('inputfile')
    parser.add_argument('duration')
    parser.add_argument('-o', '--outputfolder')
    parser.add_argument('-q', '--quality', default='great')
    parser.add_argument('-t', '--tempfolder')
    parser.add_argument('-d', '--deletetemp', action='store_true')
    args = parser.parse_args()

    if os.path.exists(args.inputfile):
        input_file = args.inputfile
        input_file_folder = os.path.join(os.path.split(input_file)[0])
    else:
        raise FileNotFoundError(args.inputfile)

    try:
        duration = int(args.duration)
    except:
        raise TypeError(args.duration)
    
    if(args.outputfolder is not None):
        if(os.path.exists(args.outputfolder)):
            output_folder = args.outputfolder
        else:
            # Consider trying to make the folder if it does not exist, consider making this a flag.
            raise FileNotFoundError(args.outputfolder)
    else:
        output_folder = input_file_folder
    
    if args.quality in outputres:
        quality = args.quality
    else:
        # Do I need to list the presets here? Should I have a flag for assuming a quality?
        raise Exception("Quality " + quality + " not in presets.")

    if(args.tempfolder is not None):
        if(os.path.exists(args.tempfolder)):
            temp_folder = args.tempfolder
        else:
            # Consider trying to make the folder if it does not exist, consider making this a flag.
            raise FileNotFoundError(args.tempfolder)
    else:
        temp_folder = input_file_folder
    
    # ensure outputs
    # calculate specs
    # multithreading?

    temp_files = call_ffmpeg(input_file, temp_folder, quality, round(duration / 1.33))
    for i in temp_files:
    # for i in temp_files[0:1]:
        perform_the_action(os.path.join(temp_folder, i + '.avi'), os.path.join(output_folder, i + '.gba'), quality);
    
    if(args.deletetemp):
        for i in temp_files:
            os.remove(os.path.join(temp_folder, i + '.avi'))

if __name__ == "__main__":
    main()
