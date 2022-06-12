from sre_constants import AT_UNI_BOUNDARY
from subprocess import SubprocessError
import requests
import json
import praw
import re
import time
from pysafebrowsing import SafeBrowsing
import config

old_karma=0

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



reddit = praw.Reddit(
    client_id=config.client_id,
    client_secret=config.client_secret,
    password=config.password,
    user_agent=config.user_agent,
    username=config.username,
    ratelimit_seconds=700
)

print(reddit.user.me())

sub_liste_deutsch=config.sub_liste_deutsch

sub_liste_eng=config.sub_liste_eng



subreddit = reddit.subreddit("+".join(sub_liste_deutsch+sub_liste_eng))
for comment in subreddit.stream.comments(skip_existing=True):
    print("Ich arbeite")
    body=comment.body.split()

    if len(body)<50:
        if ("[") in comment.body and ("](") in comment.body and ("https") in comment.body and ("(") in comment.body and (")") in comment.body and "message/" not in comment.body and "r/" not in comment.body:
            link=comment.body
            result = re.search(']((.*))', link)
            try:
                link=result.group(1)
                link=link[1:]
                while ")" in link:
                    link=link[:-1]
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



                zusammengefügt=f"({link})"
                body=comment.body
                if body.count(link)>1:
                    continue


                ###Safety-Analyse###
                key = SafeBrowsing(config.google_safe_api)
                lookup = key.lookup_urls([link])

                ergebnis=lookup[link]["malicious"]


                if zusammengefügt in comment.body and subreddit_name in sub_liste_deutsch:

                    if ergebnis==True:
                        ergebnis="Achtung: Seite ist unsicher (Google Safe Browsing)"

                    if ergebnis==False:
                        ergebnis="Seite ist sicher (Google Safe Browsing)"

                    comment = reddit.comment(str(comment))
                    comment.reply(f"Hi!\n Die verlinkte Website lautet: {link} \n\n\n\n {ergebnis} \n\n ***** \n ####### Ich bin ein kleiner Bot, der die verlinkten URLs aus Kommentaren prüft, damit ihr wisst, worauf ihr klickt!")
                    print(f"ich habe auf Comment {comment} geantwortet")
                    info_karma()
                    time.sleep(60)

                if zusammengefügt in comment.body and subreddit_name in sub_liste_eng:

                    if ergebnis==True:
                        ergebnis="Danger: page is unsafe (Google Safe Browsing)"

                    if ergebnis==False:
                        ergebnis="Page is safe to access (Google Safe Browsing)"
                    comment = reddit.comment(str(comment))
                    comment.reply(f"Hi!\n the linked website is: {link} \n\n\n\n {ergebnis} \n\n ***** \n ###### I am a friendly bot. I show the URL of linked pages and check them so that mobile users know what they click on!")
                    print(f"I replied to {comment}")
                    info_karma()
                    time.sleep(60)

            except:
                pass

