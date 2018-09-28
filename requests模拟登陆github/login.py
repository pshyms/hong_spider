import requests
from lxml import etree


class Login(object):
    def __init__(self):
        self.headers = {
            'Referer': 'https://github.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
            'Host': 'github.com'
        }
        self.login_url = 'https://github.com/login'
	# github网站规定的post表单的上传地址
        self.post_url = 'https://github.com/session'
        self.logined_url = 'https://github.com/settings/profile'
        # Session帮助我们维持一个会话，可自动处理cookies
        self.session = requests.Session()
    
    def token(self):
        # 使用Session对象的get()方法访问github的登陆页面
        response = self.session.get(self.login_url, headers=self.headers)
        selector = etree.HTML(response.text)
        # 获取登陆页面中name属性为authenticity_token的input元素的value值
        token = selector.xpath('//div//input[2]/@value')
        return token
    
    def login(self, email, password):
	    # 构造一个表单，复制各字段，其中email和password以变量的形式传递
        post_data = {
            'commit': 'Sign in',
            'utf8': '✓',
            'authenticity_token': self.token()[0],
            'login': "email",
            'password': "password"
        }
	# 上传用户信息到https://github.com/session，使用Session对象的post()方法模拟登陆，并调用dynamics方法
        response = self.session.post(self.post_url, data=post_data, headers=self.headers)
        if response.status_code == 200:
            self.dynamics(response.text)
        
	# 从个人中心页面获取用户信息，并调用profile方法
        response = self.session.get(self.logined_url, headers=self.headers)
        if response.status_code == 200:
            self.profile(response.text)
    
    # 处理关注人的动态信息，提取了所有动态信息，然后将其遍历输出，这个测试不成功
    def dynamics(self, html):
        selector = etree.HTML(html)
        dynamics = selector.xpath('//div[contains(@class, "news")]//div[contains(@class, "alert")]')
        for item in dynamics:
            dynamic = ' '.join(item.xpath('.//div[@class="title"]//text()')).strip()
            print(dynamic)
    
    # 处理个人详情页信息，提取个人昵称和邮箱，然后将其输出
    def profile(self, html):
        selector = etree.HTML(html)
        name = selector.xpath('//input[@id="user_profile_name"]/@value')[0]
	# 小技巧：找到value不为空的option元素
        email = selector.xpath('//select[@id="user_profile_email"]/option[@value!=""]/text()')
        print(name, email)


if __name__ == "__main__":
    login = Login()
    login.login(email='cqc@cuiqingcai.com', password='password')
