import yt_dlp, os, re, random, subprocess, pprint, traceback, requests
from datetime import datetime, timedelta, timezone as tz
from importlib.metadata import version
from django.shortcuts import render, redirect
from django.http import FileResponse
from django.utils import timezone
from django.contrib import messages

DOWNLOAD_DIR = 'content-downloads'
MIX_DIR = 'content-mix'
GITREPO = 'https://api.github.com/repos/zuirx/ytdl-django/commits'

def home_yt(request, subpath=''):

    video_id = request.GET.get("v") or request.GET.get("watch")

    if "https://www.youtube.com/watch" in subpath:
        return download_yt(request,subpath,video_id,"?v=")
    
    elif "https://youtu.be" in subpath:
        return download_yt(request,subpath)
    
    lastup, lastuptxt = '','' ; lastuptdy = False
    if True:
        lastup, lastuptxt = get_last_update_github()
        today = datetime.now(tz.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        if lastup == today: lastuptdy = True
    # except: pass

    if request.method == 'POST':
        url = request.POST.get("yt_link")
        action = request.POST.get("action")
        message = ''

        if not url:
            message = 'No link provided.'

        if not re.search('http', url):
            message = 'Invalid link. (we need the https:// or http://)'
            messages.error(request,message)
            return redirect('home_yt')

        match action:
            case 'info':
                
                try:
                    with yt_dlp.YoutubeDL({"listformats": True}) as ydl: 
                        info = ydl.extract_info(url,download=False)
                    
                    formats_dict = {
                        'video': {},
                        'audio': {}
                    }

                    for f in info['formats']:
                        format_id = f.get('format_id')
                        filenum = f.get('filesize')

                        if filenum:
                            filesize_calc = round(float(f.get('filesize')) / 1024.0 / 1024,2) 
                            filesize_final = f"{filesize_calc} MB"
                        else:
                            filesize_final = 'empty'

                        entry = {
                            'ext': f.get('ext'),
                            'resolution': f.get('resolution'),
                            'fps': f.get('fps'),
                            'vcodec': f.get('vcodec'),
                            'acodec': f.get('acodec'),
                            'filesize': filesize_final,
                            'url': url,
                        }

                        if f.get('vcodec') != 'none':
                            formats_dict['video'][format_id] = entry
                        else: 
                            formats_dict['audio'][format_id] = entry

                    context = {
                        'dl_opts': formats_dict,
                        'final_url' : url,
                        'message': message,
                    }
                    return render(request, 'main/home.html', context)
                
                except Exception as e:
                    messages.error(request, f"Error: {e}")
                    return redirect('home_yt')
            
            case 'video':
                return download_yt(request,subpath=url,type='video')

            case 'audio':
                return download_yt(request,subpath=url,type='audio')

    try:
        ytdlpver = version('yt_dlp')
    except:
        ytdlpver = 'unknown'

    theme = request.COOKIES.get('theme')
    context = {
        'theme' : theme,
        'ytdlpver' : ytdlpver,
        'lastup' : lastup,
        'lastuptxt' : lastuptxt,
        'lastuptdy' : lastuptdy,
    }
    return render(request, 'main/home.html', context)


def dl_from_opt(request):
    action      = request.POST.get("action")
    itag        = action.split(' - ')[0]
    url         = action.split(' - ')[1]
    typeitag    = action.split(' - ')[2]
    return download_yt(request, subpath=url,itag=itag,typeitag=typeitag)


def user_def_cookie(request):
    color_def = request.POST.get("coloropt")
    response = redirect('home_yt')

    if color_def:
        response.set_cookie(
            key='theme',
            value=color_def,
            expires=timezone.now() + timedelta(days=7)
        )

    return response


def get_last_update_github():

    headers = {"Accept": "application/vnd.github.v3+json"}
    
    response = requests.get(GITREPO, headers=headers)
    
    if response.status_code == 200:
        commits = response.json()
        if commits:
            last_commit_date = commits[0]['commit']['committer']['date']
            commit_text = commits[0]['commit']['message']
            return last_commit_date, commit_text


def ffconverter(inn, out, param):
    pass


def download_yt(request, subpath='', video_id='', noreturn=False, middle='', type='video', itag=0, typeitag='', custom_output_dir='', filename=''):
    url = subpath + middle + video_id
    if not custom_output_dir: output_dir = DOWNLOAD_DIR
    else: output_dir = custom_output_dir

    os.makedirs('content-downloads',exist_ok=True)
    
    if not video_id:
        random_num = random.randrange(100000,999999)
        video_id = f'file{random_num}'
        if '?v=' in subpath and "youtube.com" in subpath:
            video_id = subpath.split("?v=")[-1]

    try: os.remove(final_path)
    except: pass

    match type:
        case 'video': 
            format = 'bestvideo+bestaudio/best'
            filetype = 'webm'
        case 'audio': 
            format = 'bestaudio'
            filetype = 'mp3'
        case _: 
            format = 'best'
            filetype = 'mp4'

    if itag: format = itag
    if typeitag: filetype = typeitag

    final_path = os.path.join(output_dir, f'{video_id}.{filetype}')
    ydl_opts = {
        'quiet': True,
        'format': format,
        'outtmpl': final_path,
        'writethumbnail': True, 
        'postprocessors': [
            {
                'key': 'EmbedThumbnail',
            },
            {
                'key': 'FFmpegThumbnailsConvertor',
                'format': 'jpg',
                'when': 'before_dl',
            },
            {
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            }
        ],
    }

    match type:
        case 'audio':
            ydl_opts['postprocessors'].insert(0, {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            })

    pprint.pprint(ydl_opts)
    # print(final_path,'+++++++++++++++++++++++++++++')

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: 
            info = ydl.extract_info(url, download=True)
            # pprint.pprint(info)

            try:
                final_path = info['requested_downloads'][0]['filepath']
                print(info['filepath'])
            except: pass

            try:
                title = info['title']
            except:
                title = filename

        if title: video_id = title

        if noreturn:
            return f'{video_id}.{filetype}'
        else:
            response = FileResponse(open(final_path, 'rb'), as_attachment=True, filename=f'{video_id}.{filetype}')
            return response
   
    except Exception as e:
        messages.error(request, f"Error: {e}")
        traceback.print_exc()
        return redirect('home_yt')


def mix_av(request):

    video_options = []
    audio_options = []
    
    if request.method == 'POST':
        url = request.POST.get("yt_link")

        for key, value in request.POST.items():
            if key.endswith('_vcheck') and value == 'on': video_options.append(key)
            if key.endswith('_acheck') and value == 'on': audio_options.append(key)
        
        # print(video_options)
        # print(audio_options)

        if len(video_options) > 1 or len(audio_options) > 1:
            messages.error(request, "More than one video or audio selected.")
            return redirect('home_yt')
        if len(video_options) < 1 or len(audio_options) < 1:
            messages.error(request, "Less than one video or audio selected.")
            return redirect('home_yt')
        
        random_num = random.randrange(100000,999999)
        
        videofile = download_yt(request,subpath=url,itag=video_options[0].split("_")[0],noreturn=True,custom_output_dir=MIX_DIR,filename=f'videotomix{random_num}')
        audiofile = download_yt(request,subpath=url,itag=audio_options[0].split("_")[0],noreturn=True,custom_output_dir=MIX_DIR,filename=f'audiotomix{random_num}')
        output_final = 'filefinal.mp4'

        command = [
            'ffmpeg',
            '-y',
            '-i', videofile,
            '-i', audiofile,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-map', '0:v:0',
            '-map', '1:a:0',
            output_final
        ]

        print(command)

        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
            print(f"{output_final}")
        except subprocess.CalledProcessError as e:
            print(f"{e.stderr}")

        response = FileResponse(open(output_final, 'rb'), as_attachment=True, filename=f'{output_final}')
        return response

    return redirect('home_yt')