# -*- coding: utf-8 -*-
# @Version : Python3.6
# @Time    : 2018/8/22 21:42
# @Author  : Guan                  
# @File    : spider.py                   
# @SoftWare: PyCharm


import re
import os
import time
import pymongo
import requests

from CONFIG import *
from lxml import etree
from hashlib import md5
from urllib import parse
from urllib import request

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


browser = None
wait = None
colletion = None
imgdir = ""

def login(url):
    """
    登陆微博
    :param url:
    :return:
    """
    browser.get(url)

    # 等待元素加载，如果时间过长，返回False
    try:
        wait.until(EC.presence_of_element_located((By.ID, "loginname")))

    except TimeoutException:
        return False

    else:
        try:
            # 如果有弹框，忽略
            alert = browser.switch_to_alert()
            alert.dismiss
        except:
            pass

        # 输入账户与密码
        browser.find_element_by_xpath('//*[@id="loginname"]').send_keys(USERNAME)
        browser.find_element_by_xpath(
            '//*[@id="pl_login_form"]/div/div[3]/div[2]/div/input').send_keys(PASSWORD)
        # 等待1s,操作太快，点击【登录】会失败
        time.sleep(1)
        browser.find_element_by_xpath(
            '//*[@id="pl_login_form"]/div/div[3]/div[6]/a').click()
        return True

def test_login():
    """
    测试登陆
    :return:
    """
    # 这里我找的登陆后的头像来测试的
    try:
        wait.until(EC.presence_of_element_located((By.ID, "v6_pl_rightmod_myinfo")))
    except TimeoutException:
        print("【登陆失败】")
        return False
    else:
        print("【登陆成功】")
        return True

def get_weibo_data(url):
    """
    获取微博的数据
    :param url:
    :return:
    """

    for page in range(1, PAGE+1):

        # 构建页面链接
        PAGE_PARAMS["page"] = page
        query = parse.urlencode(PAGE_PARAMS)

        print("{0}?{1}".format(FOR_WHO_URL, query))
        browser.get("{0}?{1}".format(FOR_WHO_URL, query))

        while True:
            try:
                # 尝试寻找某元素（这个元素只有在这一页加载到底的时候才会出现）
                browser.find_element_by_xpath(
                    '//a[contains(@class, "page S_txt1")]')
            except NoSuchElementException:
                # 下拉滚动条，加载数据
                browser.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight)")
            else:
                yield browser.page_source
                break
    # 关闭浏览器
    browser.quit()

def extract_data(html):
    """
    提取页面数据
    :param html:
    :return:
    """
    selector = etree.HTML(html)

    nodes = selector.xpath(
        '//div[contains(@class, "WB_cardwrap WB_feed_type S_bg2 WB_feed_like")]')

    for node in nodes:
        # 依次：时间，设备，正文，图片链接，（转发数，评论数，点赞数）集合
        time = node.xpath(
            './/div[@class="WB_detail"]/div[contains(@class, "WB_from")]/a[1]/text()')
        equipment = node.xpath(
            './/div[@class="WB_detail"]/div[contains(@class, "WB_from")]/a[2]/text()')
        content = node.xpath(
            './/div[@class="WB_detail"]/div[contains(@class, "WB_text")]/text()')
        imglinks = node.xpath(
            './/div[@class="WB_detail"]/div[contains(@class, "WB_media_wrap")]//img/@src')
        TCPCol = node.xpath(
            './/div[@class="WB_handle"]//li//em/text()')
        yield {
            "time": time,
            "equipment": equipment,
            "content": content,
            "imglinks": imglinks,
            "TCPCol": TCPCol
        }

def clear_data(data):
    """
    清洗数据
    :param data:
    :return:
    """

    # 利用MD5加密，生成“指纹”
    data["_id"] = md5(str(data).encode("utf-8")).hexdigest()

    data["time"] = "".join(data["time"])
    data["equipment"] = "".join(data["equipment"])

    symbol = "\u200b"
    data["content"] = "".join(data["content"]).strip().replace(r"\n", "").replace(symbol, "")

    # （转发数，评论数，点赞数）集合，将其各自提取出来
    try:
        tmp = filter(lambda y: y, [re.search(r"\d+|[\u4e00-\u9fa5]+", x) for x in data["TCPCol"]])

        tmp = [i.group() for i in list(tmp)]
        tmp.pop(0)
        data["transNum"], data["comNum"], data["praNum"] = [int(i) if re.match(r"\d+", i) else 0 for i in tmp]
    except Exception as e:
        print(e)
        print(data["TCPCol"])
        return
    del data["TCPCol"]

    # 完整图片的url地址
    data["imglinks"] = [parse.urljoin("https://weibo.com", x) for x in data["imglinks"]]

    return data

def to_mongodb(data):
    """
    存放入mongodb
    :param data:
    :return:
    """
    try:
        colletion.insert_one(data)
    except pymongo.errors.DuplicateKeyError:
        pass

def request_img(*args):
    """
    请求图片
    :param args:
    :return:
    """

    # 构建存放图片目录
    path = "{0}/{1}".format(imgdir, args[0].replace(":", ""))
    if not os.path.exists(path):
        os.mkdir(path)

    for url in args[1]:
        try:
            response = requests.get(url=url, headers=HEADERS)
        except:
            pass
        else:
            with open("{0}/{1}.jpg".format(path, md5(url.encode("utf-8")).hexdigest()), "wb") as f:
                f.write(response.content)

def init():
    """
    初始化配置
    :return:
    """
    chrome_options = webdriver.ChromeOptions()

    prefs = {
        "profile.managed_default_content_settings.images": 2, # 禁止加载图片设置
        "profile.default_content_setting_values": {'notifications': 2} # 禁止浏览器提示
    }
    chrome_options.add_experimental_option("prefs", prefs)

    # 实例一个浏览器
    global browser
    browser = webdriver.Chrome(chrome_options=chrome_options)
    browser.maximize_window()

    # 设置最长等待时间
    global wait
    wait = WebDriverWait(browser, 10)

    global colletion
    colletion = pymongo.MongoClient("localhost", 27017).weibo.luoluo

    # 动态创建images目录
    dirname = os.path.dirname(__file__)
    dirpath = os.path.abspath(dirname)
    global imgdir
    imgdir = "{0}/{1}".format(dirpath, "images")
    if not os.path.exists(imgdir):
        os.mkdir(imgdir)

def main():

    init()

    if not login(LOGIN_URL):
        print("【登陆页面，未能成功加载节点】")

    else:
        result = test_login()
        if not result:
            return

        for html in get_weibo_data(FOR_WHO_URL):
            for data in extract_data(html):

                clearedData = clear_data(data)

                # 如果数据里面有图片url，请求图片
                if clearedData.get("imglinks"):
                    request_img(
                        clearedData["time"],
                        clearedData["imglinks"]
                    )

                to_mongodb(clearedData)
                print(data)


        print("【完成】")


if __name__ == "__main__":
    main()