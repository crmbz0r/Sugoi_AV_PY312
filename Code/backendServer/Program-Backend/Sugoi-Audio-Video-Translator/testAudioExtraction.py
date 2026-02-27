from moviepy.editor import *

video = VideoFileClip("test_video.mp4") # 2.
audio = video.audio # 3.
audio.write_audiofile("test_audio.mp3") # 4.