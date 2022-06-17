from http.client import UNAUTHORIZED
from sre_constants import AT_UNI_BOUNDARY
from subprocess import SubprocessError

import requests
import json
import praw
import re
import time
from pysafebrowsing import SafeBrowsing
import config
import datetime
from prawcore.exceptions import Forbidden
import linkpreview
from linkpreview import link_preview

#defining global variables
old_karma=0

trigger=False

odd_numb=[1,3,5,7,9,11,13,15,17,19,21,23]
sleep_hours=[22,23,24,0,1,2,3,4,5,6]


#Preparing OAuth handshake
def handshake():
    global reddit

    reddit = praw.Reddit(
    client_id=config.client_id,
    client_secret=config.client_secret,
    password=config.password,
    user_agent=config.user_agent,
    username=config.username,
    ratelimit_seconds=700
)
    #see if handshake worked
    print(reddit.user.me())


#function for sending karam updates via webex --> totally optional and not relevant for the core function of the bot
def info_karma():
    global old_karma

    redditor_name = config.reddit_username
  
    # instantiating the Redditor class
    redditor = reddit.redditor(redditor_name)

    full_karma=redditor.comment_karma+redditor.link_karma
    änderung_karma=full_karma-old_karma

    if änderung_karma!=0:
        old_karma=full_karma

        if änderung_karma<0:
            richtung="gefallen"
        
        if änderung_karma>0:
            richtung="gestiegen"


        url="https://webexapis.com/v1/messages"

        headers={
            "Authorization": f"Bearer {config.webex_api_key}"
        }
        data={
            "toPersonId":config.person_id,
            "markdown":"#### Karma-Update! \n"

            f"Dein Karma ist um {änderung_karma} Punkte auf {full_karma} Punkte {richtung}",
            "encoding":"iso-8859-1",
        }

        r = requests.post(url, data=data,headers=headers)
        print(r.raise_for_status)
    
    else:
        pass

def subreddits():
    global sub_liste_deutsch,sub_liste_eng,subreddit
    #defining the subreddits in which the bot shall monitor comments
    sub_liste_deutsch=config.sub_liste_deutsch

    sub_liste_eng=config.sub_liste_eng


    #joining both the English and German lists together
    subreddit = reddit.subreddit("+".join(sub_liste_deutsch+sub_liste_eng))


def main():
    zähler=0
    global subreddit,sub_liste_deutsch,sub_liste_eng,reddit,sleep_hours,odd_numb,reddit
    
    handshake()
    subreddits()
    
    for comment in subreddit.stream.comments(skip_existing=True):
        zähler+=1
        subreddit1 = comment.subreddit

        print(f"Ich arbeite, Nr. {zähler}, subreddit {subreddit1}")


        #Making the commentv pulled countable
        body=comment.body.split()

        #I only analyse comments shorter than 50 words at the moment
        if len(body)<50:

        #analyze wether a URL is hyperlinked and exluding some reddit-specific links
            if ("[") in comment.body and ("](") in comment.body and ("https") in comment.body and ("(") in comment.body and (")") in comment.body and "message/" not in comment.body and "r/" not in comment.body:
                link=comment.body

                #cleaning comment for URL
                result = re.search(']((.*))', link)

                link=result.group(1)
                link=link[1:]
                while ")" in link:
                    link=link[:-1]
                
                #See result
                print(comment)
                print(comment.body)
                print(link)

                ####Get Subreddit Name#####
                comment_id = str(comment)
    
                # instantiating the Comment class
                comment = reddit.comment(comment_id)
                
                # fetching the subreddit attribute
                subreddit = comment.subreddit
        
                subreddit_name= subreddit.display_name
                
                #See result
                print(subreddit_name)


                zusammengefügt=f"({link})"
                body=comment.body

                #check wether redditor included the plain URL additionally to the hyperlinked text
                if (body.count(link)>1) or (zusammengefügt not in comment.body):
                    continue


                #####################
                #Analyzing threat level of URL
                #####################
                key = SafeBrowsing(config.google_safe_api)
                lookup = key.lookup_urls([link])

                ergebnis=lookup[link]["malicious"]

                #####################
                #differentiate subreddits to reply in correct language#
                #####################

                #German
                if subreddit_name in sub_liste_deutsch:

                    if ergebnis==True:
                        ergebnis="Achtung: Seite ist unsicher (Google Safe Browsing)"

                    if ergebnis==False:
                        ergebnis="Seite ist sicher (Google Safe Browsing)"

                    comment = reddit.comment(str(comment))

                    #Pulling name of the page, if possible
                    preview = link_preview(link)
                    
                    try:
                        titel=preview.title

                    except:
                        titel=None

                    #Prepare message depending on success of title pull
                    if titel!=None:
                        try:
                            comment.reply(f"*beep boop*!\n Die verlinkte Website lautet: {link} \n\n Titel: **{titel}** \n\n\n\n {ergebnis} \n\n ***** \n ###### Ich bin ein kleiner Bot, der die verlinkten URLs aus Kommentaren prüft, damit ihr wisst, worauf ihr klickt!")
                            print(f"ich habe auf Comment {comment} geantwortet")
                        
                        #If comment ist too long, comment without title
                        except:
                            comment.reply(f"*beep boop*!\n Die verlinkte Website lautet: {link} \n\n\n\n {ergebnis} \n\n ***** \n ###### Ich bin ein kleiner Bot, der die verlinkten URLs aus Kommentaren prüft, damit ihr wisst, worauf ihr klickt!")
                            print(f"ich habe auf Comment {comment} geantwortet")

                    if titel==None:
                        comment.reply(f"*beep boop*!\n Die verlinkte Website lautet: {link} \n\n\n\n {ergebnis} \n\n ***** \n ###### Ich bin ein kleiner Bot, der die verlinkten URLs aus Kommentaren prüft, damit ihr wisst, worauf ihr klickt!")
                        print(f"ich habe auf Comment {comment} geantwortet")

                    #control at what time I receive the webex messages
                    if datetime.datetime.now().hour not in sleep_hours:
                        info_karma()

                #English
                if subreddit_name in sub_liste_eng:

                    if ergebnis==True:
                        ergebnis="Danger: page is unsafe (Google Safe Browsing)"

                    if ergebnis==False:
                        ergebnis="Page is safe to access (Google Safe Browsing)"


                    preview = link_preview(link)
                    
                    try:
                        titel=preview.title
                    except:
                        titel=None

                    comment = reddit.comment(str(comment))

                    if titel!=None:
                        try:
                            comment.reply(f"*beep boop*!\n the linked website is: {link} \n\n Title: **{titel}** \n\n\n\n {ergebnis} \n\n ***** \n ###### I am a friendly bot. I show the URL and name of linked pages and check them so that mobile users know what they click on!")
                            print(f"I replied to {comment}")
                        
                        except:
                            comment.reply(f"*beep boop*!\n the linked website is: {link} \n\n\n\n {ergebnis} \n\n ***** \n ###### I am a friendly bot. I show the URL of linked pages and check them so that mobile users know what they click on!")
                            print(f"I replied to {comment}")

                    if titel==None:
                        comment.reply(f"*beep boop*!\n the linked website is: {link} \n\n\n\n {ergebnis} \n\n ***** \n ###### I am a friendly bot. I show the URL of linked pages and check them so that mobile users know what they click on!")
                        print(f"I replied to {comment}")
                    

                    if datetime.datetime.now().hour not in sleep_hours:
                        info_karma()


while True:

    try:
        main()
        

    except Forbidden as f:
        print(f)

        url="https://webexapis.com/v1/messages"

        headers={
            "Authorization": f"Bearer {config.webex_api_key}"
        }
        data={
            "toPersonId":config.person_id,
            "markdown":f"#### Reddit: Fehler! \n\n Fehlermeldung: {f} ",
            "encoding":"iso-8859-1",
        }

        r = requests.post(url, data=data,headers=headers)
        print(r.raise_for_status)
        
        continue

    except Exception as e:
        print(e)

        url="https://webexapis.com/v1/messages"

        headers={
            "Authorization": f"Bearer {config.webex_api_key}"
        }
        data={
            "toPersonId":config.person_id,
            "markdown":f"#### Reddit: Anderer Fehler!",
            "encoding":"iso-8859-1",
        }

        r = requests.post(url, data=data,headers=headers)
        print(r.raise_for_status)
        
        continue


