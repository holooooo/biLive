# -*- coding: utf-8 -*-
"""
Created on Mon Jul 24 13:53:57 2017

@author: Amadeus

玩法：在开局时，会进行10秒的弹幕统计。然后随机挑选出一个名字开始游戏。内容：名字{name}
每个问题会等待10秒来接受玩家的选择。内容：选择{名字}
游戏界面包含以下要素：题目，bgm名，年龄，性别，问题，选项，游戏轮次，历史游戏结果
bgm音频流和数据视频流是两个流，在最后合并起来
"""

import time, os, json
from selenium import webdriver
import pymysql
import requests


def connDb():
    config = {
     'host':'127.0.0.1',
     'port':3306,
     'user':'root',
     'password':'',
     'db':'bilive',
     'charset':'utf8',
     }
    db = pymysql.connect(**config)
    print('数据库连接成功')
    return db



    

class danmu(object):
    def __init__(self, uid, nickname, text, timeline):
        self.__uid = uid
        self.__nickname = nickname
        self.__text = text
        self.__timeline = timeline
        
    def getDanmu(roomId):
        #爬取某个房间弹幕（准确的说是得到)，返回的是一个由十个弹幕组成的弹幕数组
        data = {
            'roomid': roomId
            }
        url = 'http://live.bilibili.com/ajax/msg'
        sess = requests.session()
        tempdanmu = sess.post(url, data=data)
        tempdanmu = json.loads(tempdanmu.text, encoding='utf-8')
        tempdanmu = tempdanmu['data']['room']
        if len(tempdanmu) == 0:
            print('房间号有误，请重新输入')
            os._exit(0)
        result = []
        for x in tempdanmu:
            uid = int(x['uid'])
            nickname = str(x['nickname'])
            text = str(x['text'])
            timeline = str(x['timeline'])
            newDanmu = danmu(uid, nickname, text, timeline)
            result.append(newDanmu)
        return result
    
    
    def saveDanmu(self):
        #将弹幕存入数据库
        db = connDb()
        print('数据库连接成功')
        cursor = db.cursor()
        sql = ('INSERT INTO danmu (uid, nickname, text, timeline) values ("%s","%s","%s","%s")'%
               (self.__uid, self.__nickname, self.__text, self.__timeline))
        print(self.__uid, self.__nickname, self.__text, self.__timeline)
        #检查弹幕是否重复
        try:
            sqlCheck = 'SELECT * FROM danmu WHERE timeline = "%s" and uid = "%s"'%(self.__timeline, self.__uid) 
            cursor.execute(sqlCheck)
            if cursor.fetchone() != None:
                print('该弹幕已存在')
            else:
                print(baocuo)
        except:
            try:
                cursor.execute(sql)
                db.commit()
                print('写入一行数据')
            except:
                db.rollback()
                print('写入失败')
        finally:
            db.close()
            print('关闭数据库连接')
            
    
    def checkDanmuCommand(self):         
        if self.__text.find('选择') != -1 and self.__text[-1].isdigit():
            choice = int(self.__text[-1])
            return ['choice', choice]
        if self.__text.find('名字') != -1:
            name = self.__text[2:]
            return ['name', name]
        return None

    
class role(object):
    def __init__(self, name, age, sex, lifeRoad, roleState, bgState):
        self.name = name
        self.age = age
        self.sex = sex
        self.lifeRoad = lifeRoad
        self.roleState = roleState
        self.bgState = bgState
    
    
    def saveRole(self):
        #存储用户信息
        return 'todo'
    

class game(object):
    def __init__(self):
        self.driver = webdriver.PhantomJS()
        url = 'http://www.msgjug.com/p_life/page.html'
        self.driver.get(url)
        print('初始化完成')
    
    
    def getStatus(self):
        #爬取目前状况
        name = self.driver.find_element_by_id('gameRoleName')
        age = self.driver.find_element_by_id('gameRoleAge')
        sex = self.driver.find_element_by_id('gameRoleSex')
        lifeRoad = []
        roleState = self.driver.find_element_by_xpath('//*[@id="roleState"]').find_element_by_tag('li')
        roleState = [x.text for x in roleState]
        bgState = self.driver.find_element_by_xpath('//*[@id="BGState"]').find_element_by_tag('li')
        bgState = [x.text for x in bgState]
        getLife = self.driver.find_element_by_xpath('//*[@id="vUIgameLeft"]').find_element_by_tag('div')
        for x in getLife:
            temp = []
            temp.append(x.find_element_by_tag('h2').text)
            temp.append(x.find_element_by_tag('span').text)
            temp.append(x.find_element_by_tag('p').text)
            lifeRoad.append(temp)
        status = role(name, age, sex, lifeRoad, roleState, bgState)
        return status
    
    
    def choice(self,choice):
        js = 'game.userSelect(' + choice + ')'
        self.driver.execute_script(js)
    
   
    def gameStart(self, name):
        #重新开始游戏，开始调用getQuestion,并且从弹幕中随机挑选一个名字.如果不行就再还一个，直到名字满意为止
        getGameStart = 'game.changeState("game")'
        newRole = 'newRole()'
        cleanNameCheck = '''happenMgr.init = function(role) {
                	$.post("happen/check_name.gdo", {
                			name: role.name
                		},
                		function(r) {
                			this.target = -1;
                			var datas = EvtLib;
                			for (var i = 0; i < datas.length; i++) {
                				happenMgr.list[i] = createHappen(datas[i])
                			}
                			game.cpuProcess()
                		})
                };'''
        self.driver.execute_script(getGameStart)
        print('游戏开始')
        self.driver.execute_script(cleanNameCheck)
        self.driver.find_element_by_id('inputName').send_keys(name)
        self.driver.execute_script(newRole)
    
    
    def getEvent(self):
        event = self.driver.find_element_by_id('happen')
        title = event.find_element_by_tag_name('h2').text
        content = event.find_element_by_tag_name('p').text 
        choice = event.find_element_by_tag_name('button')
        choice = [x.text for x in choice]
        return [title, content, choice]
    
    
    def gameOver(self, role):
        #结束游戏，统计数据并存入数据库
        self.driver.quit()
        print('游戏结束')
    

    def getHistoryGame(self):
        #从数据库取得历史游戏排行榜
        return 'todo'


def getPic():
    #输出画面，并且一直刷新，一秒刷新一次
    return 'todo'


def getVideo():
    #输出视频
    getPic()
    os.system('ffmpeg -framerate 1 -i now.jpg -c：v libx264 -r 30 -pix_fmt yuv420p out.mp4')
    os.system('')
    return 'todo'



try:
    #game = game()
    #game.gameStart("姚明")
    #game.getStatus()
    #game.gameOver(game.getStatus())
    while 1:
        newdanmu = danmu.getDanmu(44515)
        for x in newdanmu:
            danmu.saveDanmu(x)
        time.sleep(1)
except KeyboardInterrupt:
    print('程序已退出')