# -*- coding: utf-8 -*-
"""
Created on Mon Jul 24 13:53:57 2017

@author: Amadeus

"""

import time, sys, json, random
from selenium import webdriver
import pymysql
import requests
from collections import Counter


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
    return db


class danmu(object):
    def __init__(self, uid, nickname, text, timeline):
        self.uid = uid
        self.nickname = nickname
        self.text = text
        self.timeline = timeline
        self.eid = 0
        self.statsName = 0
        self.statsChoice = 0
        
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
            print('房间号有误，请检查后重新启动')
            sys.exit(0) 
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
        cursor = db.cursor()
        sql = ('INSERT INTO danmu (uid, nickname, text, timeline) values ("%s","%s","%s","%s")'%
               (self.uid, self.nickname, self.text, self.timeline))
        #检查弹幕是否重复
        try:
            sqlCheck = 'SELECT * FROM danmu WHERE timeline = "%s" and uid = "%s"'%(self.timeline, self.uid) 
            cursor.execute(sqlCheck)
            if cursor.fetchone() == None:
                try:
                    cursor.execute(sql)
                    db.commit()
                except:
                    db.rollback()
        finally:
            db.close()
            
            
    def run(roomid):
        #瞎jb跑起来
        while 1:
            for x in danmu.getDanmu(roomid):
                x.checkDanmuCommand()
                x.saveDanmu()
            time.sleep(1)
            
    
    def checkDanmuCommand(self,command): 
        #处理弹幕数据，提出弹幕命令
        if command == 'choice':
            if self.text.find('选择') != -1 and self.text[-1].isdigit():
                choice = int(self.text[-1]) - 1
                return [self.nickname, choice]
        elif command == 'name':
            if self.text.find('名字') != -1:
                name = self.text[2:]
                return [self.nickname, name]
        return None
    
    
    def stats(roomid,command):
        #统计弹幕命令，并且输出结果
        if command == 'choice':
            print('正在统计选择，统计大概进行10秒，请耐心等待')
            choiceList = []
            namePool = []
            for i in range(10):
                for x in danmu.getDanmu(roomid):
                    choice = x.checkDanmuCommand('choice')
                    if choice != None and choice[0] not in namePool:
                        namePool.append(choice[0])
                        choiceList.append(choice[1])
                time.sleep(1)
            if len(choiceList) == 0:
                print('因为样本数不足，所以默认选择第一个选项')
                return 0
            for x in choiceList:
                print('选择'+x)
            choice = Counter(choiceList)[0][0] - 1
            print('大家选择了第' + str(choice+1) + '个选项')
            return choice
        elif command == 'name':
            print('正在统计名字，统计大概进行15秒，请耐心等待')
            nameList = []
            namePool = []
            for i in range(15):
                for x in danmu.getDanmu(roomid):
                    name = x.checkDanmuCommand('name')
                    if name != None and name[0] not in namePool:
                        namePool.append(name[0])
                        nameList.append(name[1])
                time.sleep(1)
            if len(nameList) == 0:
                print('因为样本数不足，所以默认名字为凤凰院凶真')
                name = '凤凰院凶真'
                return name
            for x in nameList:
                print('名字'+x)
            rand = random.randrange(0, len(nameList))
            name = nameList[rand]
            print('随机选择的名字是' + name)
            return name
        
            
class role(object): 
    #这个类需要处理更多的数据才能用，暂时懒得写了
    #todo
    def __init__(self, name, age, sex, lifeRoad, roleState, bgState):
        self.name = name
        self.age = age
        self.sex = sex  
        self.lifeRoad = lifeRoad
        self.roleState = roleState
        self.bgState = bgState
    
    
    def saveRole(self):
        #存储用户信息
        db = connDb()
        cursor = db.cursor()
        sql = ('INSERT INTO role (name, age, sex, lifeRoad, roleState, bgState) VALUES ("%s", "%s", "%s", "%s", "%s", "%s");'% 
                (self.name, self.age, self.sex, self.lifeRoad, self.roleState, self.bgState))
        try:
            cursor.execute(sql)
            db.commit()
        except:
            db.rollback()
        finally:
            db.close()
        return 'todo'
    

class game(object):
    def __init__(self, roomid):
        self.roomid = roomid
        option = webdriver.ChromeOptions()
        option.add_argument('--app=http://www.msgjug.com/p_life/page.html')
        self.driver = webdriver.Chrome(chrome_options=option)
    
    
    def getStatus(self):
        #爬取目前状况，目前好像没用了。。.
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
    
    
    def choice(self):
        #选择事件函数
        choice = danmu.stats(self.roomid, 'choice')
        js = 'game.userSelect(' + str(choice) + ')'
        self.driver.execute_script(js)
    
   
    def gameStart(self, i):
        #重新开始游戏，开始调用getQuestion,并且从弹幕中随机挑选一个名字.如果不行就再还一个，直到名字满意为止
        print('游戏开始,当前为第' + str(i) + '轮')
        name = danmu.stats(self.roomid,'name')
        print('名字为' + name)
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
        cleanSelectLimit = '''game.userSelect = function(btn) {
                	var select = btn;
                	game.role.plusAff(game.happen.aff[select]); {
                		var lifeRoadNode = [game.happen.id, parseInt(btn.id), game.role.age];
                		game.role.lifeRoad.push(lifeRoadNode)
                	}
                	happenMgr.target = game.happen.aff[select].target;
                	$("#vUIgameRight").html("");
                	var dead = [];
                	dead[0] = "死亡";
                	if (!game.role.isAff(dead)) {
                		var temp = $("#vUIgameLeft");
                		temp.scrollTop(temp[0].scrollHeight);
                		game.cpuProcess()
                	} else {
                		game.roleDead()
                	}
                };'''
        self.driver.execute_script(getGameStart)
        print('游戏开始')
        self.driver.execute_script(cleanNameCheck)
        self.driver.execute_script(cleanSelectLimit)
        self.driver.find_element_by_id('inputName').send_keys(name)
        self.driver.execute_script(newRole)
        self.driver.implicitly_wait(3)
    
    
    def alive(self):
        #检测玩家是否存活
        death = self.driver.find_element_by_id('bury').text
        if death == '下葬':
            return False
        return True
    
    
    def gameOver(self, i):
        #结束游戏，统计数据并存入数据库
        name = self.driver.find_element_by_id('overName').text
        left = self.driver.find_element_by_id('overLeftTop')
        age = left.find_element_by_tag_name('span').text[:-1]
        if age == 'undefine':
            print('很惭愧，这局游戏崩溃了')
            age = 0
        death = left.find_element_by_tag_name('h2').text
        db = connDb()
        cursor = db.cursor()
        sql = ('INSERT INTO user (name, age, death) VALUES ("%s", "%s", "%s")'%
               (name, int(age), death))
        try:
            cursor.execute(sql)
            db.commit()
        except:
            db.rollback()
        finally:
            db.close()
            bury = 'B站弹幕版逗比人生'
            time.sleep(7)
            self.driver.find_element_by_id('deadSay').send_keys(bury)
            self.driver.execute_script('game.bury()')
            self.driver.refresh()
            print('游戏结束,第' + str(i) + '号观测者死于' + death +'。该观测者成长到了' + str(age) + '岁')
            print('文明的种子仍在，它将重新启动，再次开始在三体世界中命运莫测的进化，欢迎您再次登录。')
            print('---------------------------------------------------')
    
    
def main():
    try:
        i = 1
        newGame = game(3742025)
        while 1:
            newGame.gameStart(i)
            while newGame.alive():
                newGame.choice()
            newGame.gameOver(i)
            i += 1
    except KeyboardInterrupt:
        sys.exit()
        print('程序已退出')
        
main()