# 爬取笔趣阁小说
# encoding: utf-8
from pyquery import PyQuery as pq
import sys

class downloader():


    def __init__(self):
        self.base_server = 'http://www.biqukan.com'
        self.base_url = 'http://www.biqukan.com/1_1094/'
        self.url_list = []
#	self.target_url_list = []
        self.full_urls = []
        self.nums = 0
        self.wanted_pages_num = 0


    def get_url(self): 
        doc = pq(self.base_url)
        target_a = doc('dd a').items()
        for each_a in target_a:
            each_url = each_a.attr.href
            self.url_list.append(each_url)
        self.nums= len(self.url_list)
        for each in self.url_list[15:]:
            each_full_url = self.base_server + each
            self.full_urls.append(each_full_url)



    def get_content(self,target):
        content = pq(target)
        text = content('#content').text()
        head = content('h1').text()
        full_text = (head+'\n'*2+text)
        return full_text



	
    def writer(self,path,text):
        with open(path, 'a') as f:
            f.write(text+'\n')



    def choose_page(self):
        begin = input('please input your starting page: ')
        end = input('please input your ending page: ')
        self.wanted_pages_num = int(end)-int(begin)
        return self.wanted_pages_num
		




if __name__ == "__main__":
    dl = downloader()
    dl.get_url()
    print("总章节数: ", dl.nums)

    number = dl.choose_page()
    for i in range(number1):
        each_url = dl.full_urls[i]
        each_text = dl.get_content(each_url)
        dl.writer('321.txt',each_text)
        

        x = (i / number * 100)
        sys.stdout.write("已下载:%.2f %% " % x + '\r')
        sys.stdout.flush()


