#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, argparse, time, subprocess, shlex, logging, os

from bigbluebutton_api_python import BigBlueButton, exception

from selenium import webdriver
from selenium.webdriver.common.keys import Keys  
from selenium.webdriver.chrome.options import Options  
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from datetime import datetime
from time import sleep

downloadProcess = None
browser = None
selelnium_timeout = 30
connect_timeout = 5
#resolution = (1920, 1080)
resolution = (1280, 720)

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

parser = argparse.ArgumentParser()
parser.add_argument("-s","--server", help="Big Blue Button Server URL")
parser.add_argument("-p","--secret", help="Big Blue Button Secret")
parser.add_argument("-i","--id", help="Big Blue Button Meeting ID")
parser.add_argument("-I","--intro", help="Intro file to play before streaming")
parser.add_argument("-B","--beginIntroAt", help="begin intro at position (e.g. 00:01:05)")
parser.add_argument("-E","--endIntroAt", help="End intro at position (e.g. 01:00:04)")
parser.add_argument("-l","--stream", help="live stream a BigBlueButton meeting",action="store_true")
parser.add_argument("-d","--download", help="download / save a BigBlueButton meeting",action="store_true")
parser.add_argument("-m","--moderator", help="Join the meeting as moderator",action="store_true")
parser.add_argument("-S","--startMeeting", help="start the meeting if not running",action="store_true")
parser.add_argument("-A","--attendeePassword", help="attendee password (required to create meetings)")
parser.add_argument("-M","--moderatorPassword", help="moderator password (required to create a meeting)")
parser.add_argument("-T","--meetingTitle", help="meeting title (required to create a meeting)")
parser.add_argument("-u","--user", help="Name to join the meeting",default="Live")
parser.add_argument("-t","--target", help="RTMP Streaming URL")
parser.add_argument("-c","--chat", help="Show the chat",action="store_true")
parser.add_argument("-r","--record", help="Screen to record <122>|<0> (default 122)",default=122,type=int)
parser.add_argument("-v","--video_id", help="Video ID",default="1234")
args = parser.parse_args()

bbb = BigBlueButton(args.server,args.secret)


def set_up():
    global browser

    options = Options()  
    options.add_argument('--disable-infobars') 
    options.add_argument('--no-sandbox') 
    options.add_argument('--kiosk') 
    options.add_argument('--window-size={},{}'.format(*resolution))
    options.add_argument('--window-position=0,0')
    options.add_experimental_option("excludeSwitches", ['enable-automation'])
    options.add_argument('--shm-size=1gb') 
    options.add_argument('--disable-dev-shm-usage') 
    options.add_argument('--start-fullscreen') 
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.media_stream_mic": 1,
        "profile.default_content_setting_values.media_stream_camera": 1,
    })
    
    logging.info('Starting browser!!')

    browser = webdriver.Chrome(executable_path='./chromedriver',options=options)


def bbb_browser():
    global browser
    logging.info('Open BBB and hide elements!!')
    if args.startMeeting is True:
        try:
            logging.info("create_meeting...")
            create_meeting()
        except exception.bbbexception.BBBException as ERR:
            logging.info(ERR)
    logging.info("get_join_url...")
    url = get_join_url()
    logging.info(url)
    browser.get(url)
    element = EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-label="Listen only"]'))

    WebDriverWait(browser, selelnium_timeout).until(element)
    #sleep(5)
    browser.find_elements_by_css_selector('[aria-label="Listen only"]')[0].click()
    #element = EC.presence_of_element_located((By.CLASS_NAME, ".jumbo--Z12Rgj4 .buttonWrapper--x8uow .audioBtn--1H6rCK"))
    #WebDriverWait(browser, selelnium_timeout).until(element)
    #btn = browser.find_element_by_class_name(".jumbo--Z12Rgj4 .buttonWrapper--x8uow .audioBtn--1H6rCK")
    #btn.click()
    #element = EC.invisibility_of_element((By.CSS_SELECTOR, '.ReactModal__Overlay'))
    #WebDriverWait(browser, selelnium_timeout).until(element)
    #browser.find_element_by_id('chat-toggle-button').click()
    #browser.find_element_by_id('message-input').send_keys("This meeting is streamed to: %s" % args.target)
    #browser.find_elements_by_id('tippy-139')[0].click()
    try:
        element = browser.find_element_by_xpath("//span[@class='audioOptions--NhLnv']//button")
        element.click()
    except Exception:
        pass
    
    if args.chat:
        browser.execute_script("document.querySelector('[aria-label=\"User list\"]').parentElement.style.display='none';")
    else:
        pass
        #browser.find_elements_by_id('chat-toggle-button')[0].click()
        #browser.find_elements_by_css_selector('button[aria-label="Users and messages toggle"]')[0].click()
        
    #browser.execute_script("document.querySelector('[aria-label=\"Users and messages toggle\"]').style.display='none';")
    #browser.execute_script("document.querySelector('[aria-label=\"Options\"]').style.display='none';")
    #browser.execute_script("document.querySelector('[aria-label=\"Actions bar\"]').style.display='none';")
    #browser.execute_script("document.getElementById('container').setAttribute('style','margin-bottom:30px');")

    cancel_webcam()


def create_meeting():
    create_params = {}
    if args.moderatorPassword:
        create_params['moderatorPW'] = args.moderatorPassword
    if args.attendeePassword:
        create_params['attendeePW'] = args.attendeePassword
    if args.meetingTitle:
        create_params['name'] = args.meetingTitle
    return bbb.create_meeting(args.id, params=create_params)


def get_join_url():
    minfo = bbb.get_meeting_info(args.id)
    if args.moderator:
        pwd = minfo.get_meetinginfo().get_moderatorpw()
    else:
        pwd = minfo.get_meetinginfo().get_attendeepw()
    return bbb.get_join_meeting_url(args.user,args.id, pwd)


def stream_intro(frames=30):
    audio_options = '-f alsa -i pulse -ac 2 -c:a aac -b:a 160k -ar 44100'
    video_options = '-c:v libx264 -x264-params "nal-hrd=cbr" -profile:v high -level:v 4.2 -vf format=yuv420p -b:v 4000k -maxrate 4000k -minrate 2000k -bufsize 8000k -g {} -preset ultrafast'.format(frames)
    introBegin = ""
    if args.beginIntroAt:
        introBegin = "-ss %s"%(args.beginIntroAt)
    introEnd = ""
    if args.endIntroAt:
        introEnd = "-to %s"%(args.endIntroAt)
    ffmpeg_stream = 'ffmpeg -re %s %s -thread_queue_size 1024 -i %s -thread_queue_size 1024 %s -threads 0 %s -f flv "%s"' % ( introBegin, introEnd, args.intro, audio_options, video_options, args.target)
    ffmpeg_args = shlex.split(ffmpeg_stream)
    logging.info("streaming intro...")
    p = subprocess.call(ffmpeg_args)


def cancel_webcam():
    xpath = '/html/body/div[2]/div/div/div[1]/div/div[3]/div/button[1]'
    element = EC.presence_of_element_located((By.XPATH, xpath))
    try:
        WebDriverWait(browser, connect_timeout).until(element)
        browser.find_element_by_xpath(xpath).click()
    finally:
        pass


def check_number_users():
    number_users = browser.find_element_by_class_name('userCountText--IpKDk').text
    logging.info('Number of users: {}'.format(number_users))
    return int(number_users)


def stream(frames=30):
    audio_options = '-f alsa -i pulse -ac 2 -c:a aac -b:a 160k -ar 44100'
    #video_options = ' -c:v libvpx-vp9 -b:v 2000k -crf 33 -quality realtime -speed 5'

    codec = 'libx264'
    #codec = 'libvpx-vp9'

    video_options = '-c:v {} -x264-params "nal-hrd=cbr" -profile:v high -level:v 4.2 -vf format=yuv420p -b:v 4000k -maxrate 4000k -minrate 2000k -bufsize 8000k -g {} -preset ultrafast -tune zerolatency'.format(codec, frames)

    ffmpeg_stream = 'ffmpeg -thread_queue_size 1024 -f x11grab -draw_mouse 0 -s %dx%d  -i :%d -thread_queue_size 1024 %s -threads 0 %s -f flv -flvflags no_duration_filesize "%s"' % ( *resolution, args.record, audio_options, video_options, args.target)

    print('-'*100)
    logging.info(ffmpeg_stream)
    print('-'*100)

    ffmpeg_args = shlex.split(ffmpeg_stream)
    logging.info("streaming meeting...")

    # Check unitl there is users on the conference
    while check_number_users() <= 1:
        sleep(10)

    p = subprocess.Popen(ffmpeg_args)

    # Check unitl there is no more users on the conference
    while check_number_users() > 1:
        sleep(10)

    logging.info('Stop streaming. Not enough users')

    return p


def download():
    downloadFile = "/video/%s.mkv" % args.video_id 
    audio_options = '-f alsa -i pulse -ac 2'
    codec = 'libx264rgb'
    #codec = 'libvpx-vp9'
    video_options = '-c:v {} -crf 0 -preset ultrafast'.format(codec)

    ffmpeg_stream = 'ffmpeg -y -thread_queue_size 1024 -f x11grab -draw_mouse 0 -s %dx%d  -i :%d -thread_queue_size 1024 %s %s %s' % ( *resolution, args.record, audio_options, video_options, downloadFile)

    ffmpeg_args = shlex.split(ffmpeg_stream)
    logging.info("saving meeting as %s" % downloadFile)

    # Check unitl there is users on the conference
    while check_number_users() <= 1:
        sleep(10)

    p = subprocess.Popen(ffmpeg_args)

    # Check unitl there is no more users on the conference
    while check_number_users() > 1:
        sleep(10)

    logging.info('Stop recording. Not enough users.')

    return p


if args.startMeeting is False:
    while bbb.is_meeting_running(args.id).is_meeting_running() != True:
        logging.info("Meeting isn't running. We will try again in %d seconds!" % connect_timeout)
        time.sleep(connect_timeout)

# current date and time
now = datetime.now()
fileTimeStamp = now.strftime("%Y%m%d%H%M%S")

set_up()
if args.stream and args.intro:
    stream_intro()
if args.stream or args.download:
    bbb_browser()
if args.download:
    downloadProcess = download()
if args.stream:
    streamProcess = stream()
    streamProcess.terminate()
    streamProcess.wait()
if downloadProcess:
    #downloadProcess.communicate(input=None)
    downloadProcess.terminate()
    downloadProcess.wait()
if browser:
    browser.quit()
