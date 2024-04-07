import newspaper
import pandas as pd         # 导入pandas库
url = 'http://www.southcn.com/'      # 南方网
#south_paper = newspaper.build(url, language='zh')    # 构建新闻源
south_paper = newspaper.build(url,language='zh',memoize_articles = False)    # 构建新闻源

# for category in south_paper.category_urls():
#     print(category)
    
# for article in south_paper.articles:
#     print(article.url)
# len(south_paper.articles)      # 查看新闻链接的数量，与south_paper.size()一致


news_title = []
news_text = []
news = south_paper.articles
for i in range(len(news)):    # 以新闻链接的长度为循环次数
    paper = news[i]
    try :
        paper.download()
        paper.parse()
        news_title.append(paper.title)     # 将新闻题目以列表形式逐一储存
        news_text.append(paper.text)       # 将新闻正文以列表形式逐一储存
    except:
        news_title.append('NULL')          # 如果无法访问，以NULL替代
        news_text.append('NULL')          
        continue
# 建立数据表存储爬取的新闻信息
south_paper_data = pd.DataFrame({'title':news_title,'text':news_text})
south_paper_data.to_csv('data.csv')