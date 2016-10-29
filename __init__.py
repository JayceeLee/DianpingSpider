'''
程序名：   DianpingSpider
功能：    根据已有的的"大众点评网"酒店主页的URL地址，自动抓取所需要的酒店的名称、图片、经纬度、酒店价格、用户评论数量以及用户评论的用户ID、用户名字、评分、评论时间
编程语言：    python3.5.2
Created on 2016-10-30
@author: Lei Gaiceong
'''

import urllib.request
import re
import time
import os
import random

import picture #获取酒店图片
import urlspider #获取酒店的URL
import position #获取酒店位置信息
import PriceAndScores #获取酒店评分和酒店价格

# 统计所有酒店的评价信息，存入文本
def getRatingAll(fileIn):     # 抓取酒店评论页面的间隔时间，单位为秒，默认为1 second
    count =0          # 计数，显示进度
    websitenumber=0
    for line in open(fileIn,'r'):     # 逐行读取并处理文件，即hotel的url
        count=line.split('\t')[0]
        line=line.split('\t')[1] 
        websitenumber+=1
        print("正在抓取第%s个网址的酒店信息"%(websitenumber))
        try:
            print("正在抓取第%s家酒店的信息，网址为%s"%(count,line.strip('\n')))
            # 获取酒店编号
            hotelid = line.strip('\n').split('/')[4]
            #print('该酒店的hotelid是 : ', hotelid)
 
            # 拼凑出该酒店第一页"评论页面"的url
            url = line.strip('\n') + "/review_more"
            #print('该酒店第一页"评论页面"的url是', url)
             
            # 模拟浏览器,打开url
            headers = ('User-Agent', 'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko')
            opener = urllib.request.build_opener()
            opener.addheaders = [headers]
            data = opener.open(url).read()#当访问大众点评网过于次数频繁的时候，大众点评网的反爬虫技术会封锁本机的IP地址，此时data就会出现异常，无法打印正常的html
            #print(data)  
            data = data.decode('utf-8', 'ignore')
            #print(data)
            
            # 获取酒店用户评论数目
            rate_number = re.compile(r'全部点评</a><em class="col-exp">\((.*?)\)</em></span>', re.DOTALL).findall(data)
            rate_number = int(''.join(rate_number))  # 把列表转换为str，把可迭代列表里面的内容用‘ ’连接起来成为str，再进行类型转换
            print("第%d家酒店的评论数为%s" % (websitenumber, rate_number))
             
            if(rate_number<100):#若酒店评论数目少于100条，则不跳过该酒店，不再挖取信息
                continue
                         
            ## 获取酒店名称和地址
            opener1 = urllib.request.build_opener()
            opener1.addheaders = [headers]
            hotel_url =opener1.open(line).read()
            hotel_data = hotel_url.decode('utf-8')#ignore是忽略其中有异常的编码，仅显示有效的编码
            #print(hotel_data)  当访问大众点评网过于次数频繁的时候，大众点评网的反爬虫技术会封锁本机的IP地址，此时hotel_data就会出现异常，无法打印正常的html
            
			# 获取酒店名称
            shop_name=re.compile(u'<h1 class="shop-name">(.*?)    </h1>',re.DOTALL).findall(hotel_data)
            shop_name=str(''.join(shop_name)) #类型转换
            shop_name=shop_name.strip() #去掉字符串中的换行符
            
			# 获取酒店地址
            address=re.compile(u'<p class="shop-address">地址：&nbsp;(.*?)\n         <span>',re.DOTALL).findall(hotel_data)
            address=str(''.join(address))
            #print(address)
			
            # 获取酒店经纬度
            poi=re.compile(r'poi: \"(.*?)\",',re.DOTALL).findall(hotel_data)
            poi=str(''.join(poi))
            position=position.getPosition(poi)
            #print("longitude:%s°E,latitude:%s°N"%(position['lng'],position['lat']))
            
            #获取酒店评分和酒店价格
            (price,scores)=PriceAndScores.getPriceAndScores(line.strip('\n'))
            
            # 获取酒店图片，图片保存在 ./image 路径下
            PictureOut ='.\\image\\'+str(count)+" "+shop_name
            picture.getPicture(line.strip('\n'), PictureOut)
             
            #保存酒店信息
            fileOut='.\\hotel\\'+str(count)+" "+shop_name+'.txt'
            if os.path.exists(fileOut):#如果有重复文件，先删除原文件再创建一个新文件
                os.remove(fileOut)
            fileOp = open(fileOut, 'a', encoding="utf-8")
            fileOp.write("酒店名称: %s\n酒店网址： %s\n地址: %s\n经度: %s°E,纬度: %s°N\n酒店评分： %d stars\n酒店价格：¥ %d 元起/人\n评论数量: %s\n"%(shop_name,line.strip('\n'),address,position['lng'],position['lat'],scores,price,rate_number))
            fileOp.write( "酒店ID \t\t 用户ID \t\t 用户名字 \t\t 房间评分  \t\t 服务评分 \t\t 用户总评分 \t\t 评价时间 \n")
            fileOp.close()
             
            FileName='.\\hotel\\'+str(count)+" "+shop_name+' 用户评论.txt'
            if os.path.exists(FileName):
                os.remove(FileName)
             
			# 解析评分
            pages = int(rate_number / 20) + 1  # 由评论数计算页面数,大众点评网每页最多20条评论.
            for i in range(1, pages + 1):
                      
                # 打开页面
                add_url = url + '?pageno=' + str(i)
                headers = ('User-Agent', 'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko')
                opener = urllib.request.build_opener()
                opener.addheaders = [headers]
                data = opener.open(add_url).read()
                data = data.decode('utf-8', 'ignore')
   
                # 获取酒店评论用户ID列表
                userid_temp=re.compile(r'<a target="_blank" rel="nofollow" href="/member/(.*?)" user-id="(.*?)" class="J_card">', re.DOTALL).findall(data)    
                userid=[None]*len(userid_temp)
                for i in range(0,len(userid_temp)):
                    userid[i]=userid_temp[i][0]
                                          
                # 获取酒店评论用户的名字
                username = re.compile(r'<img title="(.*?)" alt=', re.DOTALL).findall(data)
    
                # 获取评价时间
                rate_time = re.compile(r'<span class="time">(..-..)', re.DOTALL).findall(data)
                       
                # 获取单项评分
                rate_room = re.compile(r'<span class="rst">房间(.*?)<em class="col-exp">', re.DOTALL).findall(data)
#                 rate_envir = re.compile(r'<span class="rst">位置(.*?)<em class="col-exp">', re.DOTALL).findall(data)
                rate_service = re.compile(r'<span class="rst">服务(.*?)<em class="col-exp">', re.DOTALL).findall(data)
   
                # 获取该用户对酒店的总评分
                rate_total = re.compile(r'" class="item-rank-rst irr-star(.*?)0"></span>', re.DOTALL).findall(data)
                mink = min(int(len(userid)), int(len(rate_total)), int(len(rate_room)))
                       
                # 获取用户评论
                user_comments= re.compile(r'<div class="J_brief-cont">(.*?)</div>',re.DOTALL).findall(data)
                user_comments=str(''.join(user_comments)) #类型转换
                user_comments=user_comments.strip() #去掉字符串中的换行符
                #print(user_comments)
   
                #将除酒店评论外的信息写入文件
                fileOp = open(fileOut, 'a', encoding="utf-8")
                for k in range(0, mink):
                    fileOp.write('%s \t\t %s \t\t %s \t\t %s \t\t %s \t\t %s \t\t %s \t\t\n' % (hotelid, userid[k], username[k], rate_room[k], rate_service[k], rate_total[k], rate_time[k]))    
                fileOp.close()
               
                #将酒店评论写入另外的文件                    
                CommentsFile=open(FileName, 'a', encoding="utf-8")
                CommentsFile.write(user_comments.strip('\n'))
                CommentsFile.close()
                sleepNum=random.randint(0,2)
                time.sleep(sleepNum)#当访问过频的时候，大众点评网的发爬虫技术可能会临时封锁我们的ip，所以可以通过设定时间来调整爬取速度，建议慢速爬取。或者通过代理ip来避免反爬虫技术封锁IP
                print(sleepNum)
            print("成功挖取第%s酒店的信息\n"%(count))
                
        # 异常处理：若异常，存储该url到exception.txt中。记录出现异常的网址，然后继续下一行的抓取
        except:
            print("第%s个酒店网址的信息抓取失败\n"%(websitenumber))#发生异常，无法成功爬取有用信息，抓取失败
            exceptionFile='exception.txt'
            file_except = open(exceptionFile,'a')
            file_except.write("%s\t\t%s"%(str(websitenumber),line)) #将爬取酒店信息时发生异常的网址保存起来

#----------------------------------
#------------测试爬虫程序-------------
#----------------------------------
if __name__ == "__main__":
    urlspider.getHotelUrl()
    fileIn = "HotelUrl.txt"
    getRatingAll(fileIn)#抓取酒店评论页面的间隔时间，单位为秒，可为0