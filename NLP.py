import PIL.Image
import nltk
import newspaper
import pandas as pd         # 导入pandas库
import jieba
import numpy
import wordcloud
import PIL
import numpy as np
from urllib import request
import datetime
import json
def GetArticle(url = 'http://www.southcn.com/' , FileName="data.txt",bIsmemoize = False):
    #url = 'http://www.southcn.com/'      # 南方网
    #south_paper = newspaper.build(url, language='zh')    # 构建新闻源
    south_paper = newspaper.build(url,language='zh',memoize_articles = bIsmemoize)    # 构建新闻源


    news_title = []
    news_text = []
    top_word_num=20
    stc_num=10
    news = south_paper.articles
    myStopWords = stopwordslist("dataset/StopWordList.txt")
    with open(FileName,'w') as f:
        for i in range(len(news)):    # 以新闻链接的长度为循环次数
            paper = news[i]
            try :
                paper.download()
                paper.parse()
                TitleWithNum = "第"+str(i+1)+"篇 "+paper.title +'\n\n'
                Context = paper.text+'\n'
                news_title.append(TitleWithNum)     # 将新闻题目以列表形式逐一储存
                news_text.append(Context)       # 将新闻正文以列表形式逐一储存
                mean_scoredsenteces,topnsentences,topn_words = GetTopSentences(Context,myStopWords,top_word_num,stc_num)
                Str_stc = ("内容总结："+ ''.join(topnsentences)).replace('\n', '').replace('\r', '') + "\n\n\n"
                f.write(TitleWithNum)
                f.write(Str_stc)
                f.write(Context)
            except:
                news_title.append('NULL')          # 如果无法访问，以NULL替代
                news_text.append('NULL')          
                continue
    # 建立数据表存储爬取的新闻信息
    #south_paper_data = pd.DataFrame({'title':news_title,'text':news_text})
    #south_paper_data.to_csv('data.csv')
    return news_title,Str_stc,news_text,topn_words



#分句
def sent_tokenizer(texts):
    start=0
    i=0#每个字符的位置
    sentences=[]
    punt_list=',.!?:;~，。！？：；～'#标点符号

    for text in texts:#遍历每一个字符
        if text in punt_list and token not in punt_list: #检查标点符号下一个字符是否还是标点
            sentences.append(texts[start:i+1])#当前标点符号位置
            start=i+1#start标记到下一句的开头
            i+=1
        else:
            i+=1#若不是标点符号，则字符位置继续前移
            token=list(texts[start:i+2]).pop()#取下一个字符.pop是删除最后一个
    if start<len(texts):
        sentences.append(texts[start:])#这是为了处理文本末尾没有标点符号的情况
    return sentences

#对停用词加载
def stopwordslist(filepath):
    stopwords = [line.strip() for line in open(filepath, 'r', encoding='gbk').readlines()]
    return stopwords

#对句子打分
def score_sentences(sentences,topn_words):#参数 sentences：文本组（分好句的文本，topn_words：高频词组
    scores=[]
    sentence_idx=-1#初始句子索引标号-1
    for s in [list(jieba.cut(s)) for s in sentences]:# 遍历每一个分句，这里的每个分句是 分词数组 分句1类似 ['花', '果园', '中央商务区', 'F4', '栋楼', 'B33', '城', '，']
        sentence_idx+=1 #句子索引+1。。0表示第一个句子
        word_idx=[]#存放关键词在分句中的索引位置.得到结果类似：[1, 2, 3, 4, 5]，[0, 1]，[0, 1, 2, 4, 5, 7]..
        for w in topn_words:#遍历每一个高频词
            try:
                word_idx.append(s.index(w))#关键词出现在该分句子中的索引位置
            except ValueError:#w不在句子中
                pass
        word_idx.sort()
        if len(word_idx)==0:
            continue

        #对于两个连续的单词，利用单词位置索引，通过距离阀值计算族
        clusters=[] #存放的是几个cluster。类似[[0, 1, 2], [4, 5], [7]]
        cluster=[word_idx[0]] #存放的是一个类别（簇） 类似[0, 1, 2]
        i=1
        while i<len(word_idx):#遍历 当前分句中的高频词
            CLUSTER_THRESHOLD=2#举例阈值我设为2
            if word_idx[i]-word_idx[i-1]<CLUSTER_THRESHOLD:#如果当前高频词索引 与前一个高频词索引相差小于3，
                cluster.append(word_idx[i])#则认为是一类
            else:
                clusters.append(cluster[:])#将当前类别添加进clusters=[]
                cluster=[word_idx[i]] #新的类别
            i+=1
        clusters.append(cluster)

        #对每个族打分，每个族类的最大分数是对句子的打分
        max_cluster_score=0
        for c in clusters:#遍历每一个簇
            significant_words_in_cluster=len(c)#当前簇 的高频词个数
            total_words_in_cluster=c[-1]-c[0]+1#当前簇里 最后一个高频词 与第一个的距离
            score=1.0*significant_words_in_cluster*significant_words_in_cluster/total_words_in_cluster
            if score>max_cluster_score:
                max_cluster_score=score
        scores.append((sentence_idx,max_cluster_score))#存放当前分句的最大簇（说明下，一个分解可能有几个簇） 存放格式（分句索引，分解最大簇得分）
    return scores;

#结果输出
def GetTopSentences(texts,stopwords,topn_wordnum=20,n=10):#texts 文本，topn_wordnum高频词个数,n为返回几个句子
    #stopwords = stopwordslist("dataset/StopWordList.txt")#加载停用词
    sentence = sent_tokenizer(texts)  # 分句
    words = [w for sentence in sentence for w in jieba.cut(sentence) if w not in stopwords if
             len(w) > 1 and w != '\t']  # 词语，非单词词，同时非符号
    wordfre = nltk.FreqDist(words)  # 统计词频
    topn_words = [w[0] for w in sorted(wordfre.items(), key=lambda d: d[1], reverse=True)][:topn_wordnum]  # 取出词频最高的topn_wordnum个单词

    scored_sentences = score_sentences(sentence, topn_words)#给分句打分

    # 1,利用均值和标准差过滤非重要句子
    avg = numpy.mean([s[1] for s in scored_sentences])  # 均值
    std = numpy.std([s[1] for s in scored_sentences])  # 标准差
    mean_scored = [(sent_idx, score) for (sent_idx, score) in scored_sentences if
                   score > (avg + 0.5 * std)]  # sent_idx 分句标号，score得分

    # 2，返回top n句子
    top_n_scored = sorted(scored_sentences, key=lambda s: s[1])[-n:]  # 对得分进行排序，取出n个句子
    top_n_scored = sorted(top_n_scored, key=lambda s: s[0])  # 对得分最高的几个分句，进行分句位置排序
    #c = dict(mean_scoredsenteces=[sentence[idx] for (idx, score) in mean_scored]) 
    #c1=dict(topnsenteces=[sentence[idx] for (idx, score) in top_n_scored])
    #return c,c1
    mean_scoredsenteces=[sentence[idx] for (idx, score) in mean_scored]
    topnsentences=[sentence[idx] for (idx, score) in top_n_scored]
    return mean_scoredsenteces,topnsentences,topn_words


def GetWordCloud(TopWordsList,imgPath = "img/wordcloud/marks.jpg"):
    
    wc = wordcloud.WordCloud(
    background_color='red',
    width=500,
    height=500,
    mask=np.array(PIL.Image.open(imgPath)), #设置背景图片
    )
    wc.generate_from_text(TopWordsList,collocations=False)
    wc.to_file("img/wordcloud/res.jpg")


def GetBingImg():
    market = 'zh-CN'
    resolution = '1920x1080'

    # idx表示当前离这天的天数 ，0表示当天，1表示抓取前一天的
    response = request.urlopen("http://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt" + market)
    obj = json.load(response)
    url = (obj['images'][0]['urlbase'])
    print(obj['images'][0]['copyright'])
    print(obj['images'][0]['startdate'])
    url = 'http://www.bing.com' + url + '_' + resolution + '.jpg'

    todayDate = datetime.datetime.now().strftime("%Y%m%d")
    print(todayDate)

    imgName = "img/bg/bing.jpg"
    f = open(imgName, 'wb')
    bingpic = request.urlopen(url)
    f.write(bingpic.read())
    f.close()
    return bingpic ,imgName

#GetArticle()
