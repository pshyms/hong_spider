mport time
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 代码修改了减速阈值，原先为4/5测试不成功，修改为4/7后成功

"""
遗留问题
1. 验证码拖动失败后重新再试，为什么会向右边移动一些？


已解决问题点
1. is_pixel_equal()函数中，阈值为什么是60，解答如下
首先取到两张图，第一张图是不带滑块和缺口的图，
第二张图是点击滑动按钮后出现滑片和缺口的图，
但是仔细看第二张图，是除了目标缺口之外，还有一个阴影缺口，目录可能就是防爬，阈值设为60就是为了排除这个阴影。

2. get_gap中的left=66开始找两张图的不同，是为了排除滑块部分的不同。

3. BORDER =6 是因为验证图起始滑块左边有个边界，这个值为6，计算滑动总距离的时候，需要用缺口的横坐标 - BORDER
这个BORDER值貌似需要定时修改，缺口对齐允许一个误差值，如果一直精确对齐，貌似也有问题

4. get_track函数中的mid阈值需要定时修改，否则次数多了容易被定位爬虫操作，因为移动动作一样
"""

EMAIL = '1816635208@qq.com'
PASSWORD = 'shiyan823'
BORDER = 7
#INIT_LEFT = 60


class CrackGeetest():
    def __init__(self):
        self.url = 'https://account.geetest.com/login'
        self.browser = webdriver.Chrome()
        self.wait = WebDriverWait(self.browser, 20)
        self.email = EMAIL
        self.password = PASSWORD
    
    def __del__(self):
        self.browser.close()
    
    def get_geetest_button(self):
        """
        获取初始验证按钮
        :return:
        """
        button = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'geetest_radar_tip')))
        return button
    
    def get_position(self):
        """
        获取验证码位置
        :return: 验证码位置元组
        """
        img = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'geetest_canvas_img')))
        time.sleep(2)
        location = img.location
        size = img.size
        top, bottom, left, right = location['y'], location['y'] + size['height'], location['x'], location['x'] + size[
            'width']
        return (top, bottom, left, right)
    
    def get_screenshot(self):
        """
        获取网页截图
        :return: 截图对象
        get_screenshot_as_png()是webdriver.chrome()的一个方法，是获取屏幕截图，保存的是二进制数据
        使用ByteIO操作二进制数据，BytesIO实现了在内存中读写bytes，返回的是2进制数据，类似b'\xe4\xb8\xad\xe6\x96\x87'
        Image.open()读取图片内容并赋值给变量screenshot
        """
        screenshot = self.browser.get_screenshot_as_png()
        screenshot = Image.open(BytesIO(screenshot))
        return screenshot
    
    def get_slider(self):
        """
        获取滑块
        :return: 滑块对象
        """
        slider = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'geetest_slider_button')))
        print("滑块的尺寸", slider.size)
        print("滑块的位置", slider.location)
        return slider
    
    def get_geetest_image(self, name='captcha.png'):
        """
        获取验证码图片
        :return: 图片对象
        """
        top, bottom, left, right = self.get_position()
        print('验证码位置', top, bottom, left, right)
        screenshot = self.get_screenshot()
        captcha = screenshot.crop((left, top, right, bottom))
        captcha.save(name)  # 使用save方法把截图保存到captcha.png
        return captcha
    
    def open(self):
        """
        打开网页输入用户名密码
        :return: None
        """
        self.browser.get(self.url)
        email = self.wait.until(EC.presence_of_element_located((By.ID, 'email')))
        password = self.wait.until(EC.presence_of_element_located((By.ID, 'password')))
        email.send_keys(self.email)
        password.send_keys(self.password)
    
    def get_gap(self, image1, image2):
        """
        获取缺口偏移量,也就是缺口的左边边界的横坐标值
        :param image1: 不带缺口图片
        :param image2: 带缺口图片
        :return:
        """
        left = 60  # 滑块的长宽都是66，从这里开始是为了排除
        for i in range(left, image1.size[0]):  # image1.size[0]是横坐标，image1.size[1]是纵坐标值
            for j in range(image1.size[1]):
                if not self.is_pixel_equal(image1, image2, i, j):
                    left = i
                    return left
        return left
    
    def is_pixel_equal(self, image1, image2, x, y):
        """
        判断两个像素是否相同
        :param image1: 图片1
        :param image2: 图片2
        :param x: 位置x
        :param y: 位置y
        :return: 像素是否相同
        """
        # 取两个图片的像素点
        pixel1 = image1.load()[x, y]
        pixel2 = image2.load()[x, y]
        print("图片1的像素点", pixel1)
        print("图片2的像素点", pixel2)
        threshold = 60
        if abs(pixel1[0] - pixel2[0]) < threshold and abs(pixel1[1] - pixel2[1]) < threshold and abs(
                pixel1[2] - pixel2[2]) < threshold:
            return True
        else:
            return False
    
    def get_track(self, distance):
        """
        根据偏移量获取移动轨迹
        :param distance: 偏移量
        :return: 移动轨迹
        """
        # 移动轨迹
        track = []
        # 当前位移
        current = 0
        # 减速阈值
        mid = distance * 4 / 7  # 这个值设的太小的话，跑不到缺口的位置，速度就变为了0，因为到mid这个距离后，之后要减速的
        # 计算间隔
        # 初速度
        v = 0
        t = 0.2
        while current < distance:
            if current < mid:
                # 加速度为正2
                a = 2
            else:
                # 加速度为负3
                a = -3
            # 初速度v0
            v0 = v
            # 当前速度v = v0 + at
            v = v0 + a * t
            # 移动距离x = v0t + 1/2 * a * t^2, 变量move就是0.2秒内移动的距离
            move = v0 * t + 1 / 2 * a * t * t
            # 当前位移
            current += move
            # 加入轨迹
            track.append(round(move))
            print(track)  # 用于动态的理解运动轨迹，round()的作用是取整
        return track
    
    def move_to_gap(self, slider, track):
        """
        拖动滑块到缺口处
        :param slider: 滑块
        :param track: 轨迹
        :return:
        """
        ActionChains(self.browser).click_and_hold(slider).perform()
        for x in track:
            ActionChains(self.browser).move_by_offset(xoffset=x, yoffset=0).perform()
        time.sleep(0.5)
        ActionChains(self.browser).release().perform()
    
    def login(self):
        """
        登录
        :return: None
        """
        submit = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'login-btn')))
        submit.click()
        time.sleep(10)
        print('登录成功')
    
    def crack(self):
        # 输入用户名密码
        self.open()
        # 点击验证按钮
        button = self.get_geetest_button()
        button.click()
        # 获取验证码图片
        image1 = self.get_geetest_image('captcha1.png')
        # 点按呼出缺口
        slider = self.get_slider()
        slider.click()
        # 获取带缺口的验证码图片
        image2 = self.get_geetest_image('captcha2.png')
        # 获取缺口位置
        gap = self.get_gap(image1, image2)
        print('缺口位置', gap)
        # 减去缺口边界值
        gap -= BORDER
        print("减去缺口位移后的位置", gap)
        # 获取移动轨迹
        track = self.get_track(gap)
        print('滑动轨迹', track)
        # 拖动滑块
        self.move_to_gap(slider, track)
        
        success = self.wait.until(
            EC.text_to_be_present_in_element((By.CLASS_NAME, 'geetest_success_radar_tip_content'), '验证成功'))
        print(success)
        
        # 失败后重试，目的是多次爬取后，会有防爬机制，要求再滑动一次，第一次爬取不要判断语句也行。
        if not success:
            self.crack()
        else:
            self.login()


if __name__ == '__main__':
    crack = CrackGeetest()
    crack.crack()

