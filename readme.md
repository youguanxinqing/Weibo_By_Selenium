# Weibo\_By_Selenium
需要说明的是，经过渲染之后的网页数据，会夹杂许多杂志，增加清洗数据的难度。这里之所以用selenium+chrome的方法来爬取新浪微博，只为练习。事实上，如果数据并不庞大，调用新浪提供的免费接口，或者访问APP的数据源，都是更好的选择。这里不做延伸



## 要求
这里我选择爬取的是我喜欢的一个作家，落落的微博，需要提取的数据如下所示： 
![](https://i.imgur.com/sfsntzX.png)  

**要求1**：发布时间，发布设别，微博正文，图片链接，转发数，评论数，点赞数  
**要求2**：将这些数据存入mongodb中  
**要求3**：下载获取到的图片链接（我这里选择的是封面图片，而不是高清大图）  

## 注意
整个过程中需要注意的地方：
**注意1**：微博每页的数据并非直接全部呈现，当内容比较多时，需要下拉滑动条进行数据的加载   
![](https://i.imgur.com/fylwWEa.png)  
控制浏览器下拉代码：  
```python
browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
```
（实际是执行了js语句）  

**注意2**：尽管显示微博页数只有32，当当你访问page=100的时候，依然可以得到渲染后的页面，只是这个页面没有数据  
![](https://i.imgur.com/SplaTRV.png)

我做了最笨也是最简单的处理，以页数作为循环次数
```python
for page in range(1, PAGE+1):
	...
```

**注意3**：当转发或者评论或者点赞为0的时候，微博直接显示文字 
![](https://i.imgur.com/n2Ce8Sy.png)

我是通过正则来清洗的数据，因为这样看起来会有些高大上（逃。。。） 

	tmp = filter(lambda y: y, [re.search(r"\d+|[\u4e00-\u9fa5]+", x) for x in data["TCPCol"]])

	tmp = [i.group() for i in list(tmp)]
	tmp.pop(0)
	data["transNum"], data["comNum"], data["praNum"] = [int(i) if re.match(r"\d+", i) else 0 for i in tmp]



## 效果
程序运行效果如下： 
![](https://i.imgur.com/bF9zmS2.gif) 

插入mongodb数据格式如下：  
![](https://i.imgur.com/2JcExnK.png)  

本地保存图片如下： 
![](https://i.imgur.com/9pypsMW.png)

## 问题
其中我遇到一个问题，程序已经能够正常运行，然而添加无头设置之后会报错，编译器提示元素不可见。暂时我还没能解决这个问题，之后我会好好研究，或者，要不你们告诉告诉我嘛【**装可爱脸.jpg**】
