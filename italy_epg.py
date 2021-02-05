#!/usr/bin/env python


# Italy EPG is a script that will communicate with remote EPG provider
# and  parse through all the channels and format into XML so that it can be used
# in xTeve or Plex

from bs4 import BeautifulSoup   ### html parsing
import re                       ### text manipulation
import requests                 ### for making json requests
import json                     ### for json formatting and manipulation
import datetime as dt           ### to format the dates and times properly into xml file
import time                     ### for the sleeps

print("Starting EPG script...")

### Define variables

print("Setting variables...")
network_url = "https://remote_epg_url/"
network_image_url = "https://remote_image_url"
italy_channels = [ 'channel1', 'channel2', 'channel3' ] ### define channels
local_image_url = "http://local.url/italy/"

#######################################################################
### writexmlchannel - write channel headers to xml file
#######################################################################

def writexmlchannel(write_channel):

    f.write('    <channel id="{}">\n'.format(write_channel))
    f.write('      <display-name>{}</display-name>\n'.format(write_channel))
    f.write('      <icon src="{}{}" />\n'.format(local_image_url,write_channel))  ### channel icon located on local server
    f.write('    </channel>\n')

###############################################################################################################################
### writexmlprogramme - writes the input data into xml format into the xml epgtv file
##############################################################################################################################


def writexmlprogramme(requested_channel,iso_start_date,iso_end_date,title,stitle,desc,imagelink,ns_epnum,air_date):

    f.write('    <programme channel="{}" start="{}" stop="{}">\n'.format(requested_channel,iso_start_date,iso_end_date))
    f.write('      <title lang="it">{}</title>\n'.format(title))
    f.write('      <sub-title lang="it">{}</sub-title>\n'.format(stitle))
    if desc:
      f.write('      <desc lang="it">{}</desc>\n'.format(desc))
    if imagelink:
      f.write('      <icon src="{}"/>\n'.format(imagelink))
    if ns_epnum:
      f.write('      <episode-num system="xmltv_ns">{}</episode-num>\n'.format(ns_epnum))
    if air_date:
      f.write('      <episode-num system="original-air-date">{}</episode-num>\n'.format(air_date))
    f.write('    </programme>\n')

##########################################################################################
### dateincrementer - increment date and put into format required for xmltv
##########################################################################################

def dateincrementer(date_increment_requested):

    today = dt.datetime.now()
    today_format = today.strftime('%d-%m-%Y')
    #print("today is: ",today_format)
    date_increment = dt.datetime.now() + dt.timedelta(days=date_increment_requested)
    date_increment_format = date_increment.strftime('%d-%m-%Y')
    #print("Incremented by: {} Day is: {}".format(date_increment_requested,date_increment_format))
    return date_increment_format

#############################################################################################
### Main Loop
#############################################################################################

eventcount = 0  ### Reset counter

### Write XML Header at top of xml epgtv file
print("Opening/creating xml file...")
f = open("italy_epg.xmltv","w")
print("Writing XML header")
f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
f.write('  <tv source-info-url="" generator-info-name="Italy EPG Generator : on {}" source-info-name="Big Vs generator">\n'.format(dt.datetime.now()))


### write all the channel headers
print("Writing channel headers")
for channel in italy_channels:
  writexmlchannel(channel)

### Main program loop

print("Starting main programme parser")
for i in range(6):

  epg_date_requested = dateincrementer(i)
  print("Requested EPG date is: ",epg_date_requested)
  request_date = str(epg_date_requested)

  for channel in italy_channels:

    time.sleep(5)
    request_url = "{}{}/{}.json".format(network_url,channel,request_date)
    request_epg = requests.get(request_url)                                                                ### Grab the json data from provider
    reqjson = json.loads(request_epg.text)                                                                      ### Put json data into variable/json list
    events = reqjson['events']                     ### events are the tv programmes

    for event in events:                           ### parse individual programmes

      eventcount = eventcount + 1                  ### reset counters
      info_grab_errors = 0

      ### Grab program name
      namegrab = event['program']
      namegrab = namegrab['name']
      if namegrab:  ### if program name exists
        namegrab = re.sub(r'&',r'and',namegrab)
        title=namegrab
      else:
        title=""                               ### no program name provided

      episode = event['episode_title']
      if episode:
        episode = re.sub(r'&',r'and',episode)
        stitle=episode
      else:
        stitle=""

      startdate = event['date']
      if not startdate:
        info_grab_errors = info_grab_errors + 1     ### error out if no start time exists

      starttime = event['hour']
      if not starttime:
        info_grab_errors = info_grab_errors + 1      ### error if no start hour exists
      duration = event['duration']
      if not duration:
        info_grab_errors = info_grab_errors + 1      ### error if no duration exists

      ### Calculate start time ######################################

      mytime = dt.datetime.strptime(starttime,'%H:%M').time() # Convert time string to time object
      mydate = dt.datetime.strptime(startdate,'%d/%m/%Y') #convert date string to date object
      combinedstarttime = dt.datetime.combine(mydate,mytime) #combine date and time together

      timezone="+0200" ###Italy Time Zone
      isodt=combinedstarttime.strftime('%Y%m%d%H%M%S') ### Convert date string to ISO for XMLTV

      ### Convert datetime object to string to paste into XMLTV file
      strdate=str(isodt) #Convert back to string and add timezone
      iso_start_time=strdate+" "+ timezone

      ### Figure out end time #########################################

      duration_time = dt.datetime.strptime(duration,'%H:%M:%S').time() #Convert duration time string to time object

      duration_add_hour = int(duration_time.strftime('%H')) #Strip out Hour and convert to int to use with timedelta
      duration_add_minutes = int(duration_time.strftime('%M'))

      duration_add = combinedstarttime + dt.timedelta(hours=duration_add_hour)
      duration_add = duration_add + dt.timedelta(minutes=duration_add_minutes)

      iso_end_time=duration_add.strftime('%Y%m%d%H%M%S')
      iso_end_time=str(iso_end_time)
      iso_end_time=iso_end_time+" "+timezone   ### Final end time, formatted to ISO and in proper time zone

      ################################
      ### Parse program description
      ################################

      description = str(event['description'])
      if description:
        description = re.sub(r'&',r'and',description)
      else:
        pass      ### No description provided

      sforcheck = False
      episodeforcheck = False

      ### Parse episode number

      episodenumber = event['episode']
      if episodenumber:
        if str.isdecimal(episodenumber):
          ns_episode = int(episodenumber)
          ns_episode = ns_episode - 1
          episodeforcheck = True

      ### Parse season number

      season = event['season']
      if season:
        if str.isdecimal(season):
            sforcheck = True
            ns_season = int(season)
            ns_season = ns_season - 1

      ns_epnum = ""
      air_date = ""

      if sforcheck == True and episodeforcheck == True:

        ns_epnum = "{}.{}.".format(ns_season,ns_episode)

      elif "Puntata del" in stitle:  ### If exists an original air date, use that for season or episode number

        punt = re.sub(r' ','',stitle)
        punt = re.sub(r'Puntatadel','',punt)

        puntsearch = re.search('[0-9]{2}/[0-9]{2}/[0-9]{4}',punt)

        if puntsearch is not None:  ### Found an air date, start to parse
          punt = puntsearch.group()

          punt_date = dt.datetime.strptime(punt,'%d/%m/%Y')
          comb_punt_time = dt.datetime.combine(punt_date,mytime)
          comb_fpunt_time = comb_punt_time.strftime('%Y-%m-%d %H:%M')
          air_date = comb_fpunt_time
        else:
          air_date = ""

      else:
        pass        ### No series or episode information provided

      ### Check for a show thumbnail

      image = event['image']
      if image:
          imagelink = str(network_image_url+image)
      else:
          imagelink = ""

      requested_channel = channel ### Use already provided channel number/name

      ### If there were no errors above, proceed to write data to XML file

      if info_grab_errors == 0:
        writexmlprogramme(requested_channel,iso_start_time,iso_end_time,title,stitle,description,imagelink,ns_epnum,air_date)
      else:
        pass ### Errors parsing program
        #print("Failed to find critical information, not writing to xml") ### Program found errors, not writing program to xml

      ### Finished writing programme

#############################################
### Finished writing channels and programs
#############################################
print("Finished parsing. Programmes added: ",eventcount)          ### Give number of found programs

### Close the output xml file

f.write('  </tv>\n')
f.close()

### Push Results via MQTT ###

network = "Italy"

### If using MQTT, uncomment the below 2 lines

### from pushresults import PushResultsMqtt
###PushResultsMqtt(network,eventcount)


### If using xTeve, Force XTeve to update M3U file, which is pointed at localhost, otherwise comment out below lines
apiurl="http://xteve.lan:34400/api/"
headers = {'Content-type': 'application/json'}

print("Pushing JSON POST update to XTeve")
r = requests.post(apiurl, json={"cmd": "login"}, headers=headers)
t = requests.post(apiurl, json={"cmd": "update.xmltv"}, headers=headers)
datares=json.loads(t.text)

if datares['status'] == True:
     print("POST Successful")




### Done

