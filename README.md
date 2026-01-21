# YTDL web
yt-dlp front-end in django 

## Installation
- Install Python 3.11.*
- Clone this repository:
```git clone https://github.com/zuirx/ytdl-django```
```cd ytdl-django```
- Create a venv (and enable it):
```python -m venv venv```
- Install requirements.txt:
```pip install -r requirements.txt```
- In the project's directory, create the static files:
```python ./manage collectstatic```
- Run on windows: run runserver-win.py
- Run on Debian/Linux: run runserver-deb.py

## TODO
- [ ] show download % progress
- [ ] transcript download
- [ ] download the playlist (and other yt-dlp features)
- [ ] select video/audio: good, bad, medium quality
- [ ] add server limits
- [ ] translation languages
- [ ] mix audio and video (on the way)
