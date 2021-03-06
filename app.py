# -*- coding: utf-8 -*-
"""
Created on Fri Aug 24 18:12:45 2018

@author: linzino
"""

from linebot.models import *
from datetime import datetime 
import feedparser
import random
# line-bot
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import *

# mongodb
from pymongo import MongoClient
import pymongo
import urllib.parse
from datetime import datetime 

# server-side
from flask import Flask, request, abort

# line-bot
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import *

# package
import re
from datetime import datetime 

# customer module
import mongodb
import corwler


app = Flask(__name__)

line_bot_api = LineBotApi('l4pC2u/3DFbFW3pC0BE8huyEqMgaIZjlc0NzmqgLmm5+KXfRJLyjHIBwPPH5ize3LxjSKrbAUMi2hJEtJKKcRBdLg/MB6k/0g0n/dzZB+JImR7h8O1GRQaq3/JUNQaqxGhjTSWc0AnFsdIDIbcQ5LQdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('f44868616b14237cf0bd486d8e591e8e')



@app.route("/callback", methods=['POST'])
def callback():

    
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(FollowEvent)
def handle_follow(event):
    '''
    當使用者加入時觸動
    '''
    # 取得使用者資料
    profile = line_bot_api.get_profile(event.source.user_id)
    name = profile.display_name
    uid = profile.user_id
    
    print(name)
    print(uid)
    # Udbddac07bac1811e17ffbbd9db459079
    if mongodb.find_user(uid,'users')<= 0:
        # 整理資料
        dic = {'userid':uid,
               'username':name,
               'creattime':datetime.now(),
               'Note':'user',
               'ready':0}
        
        mongodb.insert_one(dic,'users')



@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    '''
    當收到使用者訊息的時候
    '''
    profile = line_bot_api.get_profile(event.source.user_id)
    name = profile.display_name
    uid = profile.user_id
    message = event.message.text

    def hello():
      now=datetime.now()
      greet=''
      twh=int(now.hour+8)
      if twh>24:
          twh=twh-24
      if twh<12:
          greet='早安!'
      elif twh<14:
          greet='午安!'
      elif twh<18:
          greet='下午好!'
      else:
          greet='晚安!'
      casttext = name+'對大家說：大家'+greet
      remessage = TextSendMessage(text=casttext)
      userids = mongodb.get_all_userid('users')
      msgs = StickerSendMessage(
          package_id='1',
          #sticker_id=random.randint(1,15)
          sticker_id='2'
          )
      line_bot_api.multicast(userids, remessage)
      line_bot_api.multicast(userids, msgs)      
      
    def news():
      dic = corwler.udn_news()
      columns = []
      for i in range(0,3):
          carousel = CarouselColumn(
                      thumbnail_image_url = dic[i]['img'],
                      title = dic[i]['title'],
                      text = dic[i]['summary'],
                      actions=[
                          URITemplateAction(
                              label = '點我看新聞',
                              uri = dic[i]['link']
                            )
                          ]
                      )
          columns.append(carousel)        
      remessage = TemplateSendMessage(
                  alt_text='Carousel template',
                  template=CarouselTemplate(columns=columns)
                  )           
      line_bot_api.reply_message(event.reply_token, remessage)      
      
    
    def dcard():
      text = corwler.Dcard()
      line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=text))
      
    def choosebank():
      # 設定使用者下一句話要群廣播
      mongodb.update_byid(uid,{'ready':1},'users')
      remessage = TextSendMessage(text='請選擇銀行編號(120,142)?')
      line_bot_api.reply_message(
                      event.reply_token,
                      remessage)
      
      
    def postscore(message):
      mongodb.update_byid(uid,{'ready':0},'users')
      message=int(message)
      text = corwler.google(message)
      # 包裝訊息
      remessage = TextSendMessage(text=text)
      # 回應使用者
      line_bot_api.reply_message(
                      event.reply_token,
                      remessage)           
      
    if re.search('新聞|news', event.message.text, re.IGNORECASE):
        news()  
        return 0 
        
    if re.search('Dcard|dcard', event.message.text, re.IGNORECASE):
        dcard()
        return 0
    
    if message == '打招呼':
        hello()
        return 0         
    
    if message == '評價':
        choosebank()
        return 0 
    
    if mongodb.get_ready(uid,'users') ==1 :
        postscore(message)
        return 0 
    
    if re.search('Hi|hello|你好|ha', message, re.IGNORECASE):
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))        
        return 0 
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))
    return 0 


if __name__ == '__main__':
    app.run(debug=True)