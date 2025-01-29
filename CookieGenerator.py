
# 不推荐使用！推荐使用CookieTransfer！

import os
import requests
import json
import uuid
import re
from ddddocr import DdddOcr
import string
import time
import random
from random import sample


class LoginJson:
    def __init__(self, json_str=""):
        self.json = json_str

    def to_json(self):
        escaped_string = self.json
        escaped_result = {
            "sauth_json": escaped_string
        }
        return json.dumps(escaped_result)


class AimInfo:
    def __init__(self, ip="", country="", tz="", tzid=""):
        self.ip = ip
        self.country = country
        self.tz = tz
        self.tzid = tzid

    def to_dict(self):
        return {
            "aim": self.ip,
            "country": self.country,
            "tz": self.tz,
            "tzid": self.tzid
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class SAuth:
    def __init__(self, ip, sdk_user_id, session_id, udid, device_id, sdk_version, app_channel, login_channel,
                 real_name, timestamp: str, user_id, device_key, aim_info):
        self.game_id = "x19"
        self.login_channel = login_channel
        self.app_channel = app_channel
        self.platform = "pc"
        self.sdkuid = sdk_user_id
        self.sessionid = session_id
        self.sdk_version = sdk_version
        self.client_login_sn = str(uuid.uuid4()).replace("-", "").upper()
        self.gas_token = ""
        self.source_platform = "pc"
        self.ip = ip
        self.udid = udid
        self.deviceid = device_id
        self.realname = real_name
        self.timestamp = timestamp
        self.userid = user_id
        self.device_key = device_key
        self.aim_info = aim_info

    def to_dict(self):
        return {
            "gameid": self.game_id,
            "login_channel": self.login_channel,
            "app_channel": self.app_channel,
            "platform": self.platform,
            "sdkuid": self.sdkuid,
            "sessionid": self.sessionid,
            "sdk_version": self.sdk_version,
            "udid": self.udid,
            "deviceid": self.deviceid,
            "aim_info": self.aim_info.to_json(),
            "client_login_sn": self.client_login_sn,
            "gas_token": self.gas_token,
            "source_platform": self.source_platform,
            "ip": self.ip,
            "userid": self.userid,
            "realname": self.realname.to_json(),
            "timestamp": self.timestamp
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class RealName:
    def __init__(self, type: str):
        self.realnametype = type

    def to_dict(self):
        return {
            "realname_type": self.realnametype
        }

    def to_json(self):
        return json.dumps(self.to_dict())  # Fix method to use json.dumps


class UserInfoResponse:
    def __init__(self, code, message, data):
        self.Code = code
        self.Message = message
        self.Data = data


class UserInfo:
    def __init__(self, username, sdk_login_data):
        self.Username = username
        self.SdkLoginData = sdk_login_data


class LoginAuthor:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.device_id = str(uuid.uuid4()).replace("-", "").upper()
        self.udid = str(uuid.uuid4()).replace("-", "").upper()

    def check_4399_verify_code(self, proxy):
        value = str(uuid.uuid4()).replace("-", "")
        url = f"http://ptlogin.4399.com/ptlogin/verify.do?username={self.username}&appId=kid_wdsj&t={str(uuid.uuid4())}&inputWidth=iptw2&v=1"
        cookies = {"USESSIONID": value}
        response = requests.get(url, cookies=cookies, proxies=proxy)
        pattern = r"/ptlogin/captcha\.do\?captchaId=[\w\d]+"
        match = re.search(pattern, response.text)
        if match:
            value2 = match.group(0)
            return value2.replace("/ptlogin/captcha.do?captchaId=", ""), f"http://ptlogin.4399.com/{value2.strip('/')}"
        return "", ""

    def login(self, verifycode, verifysession, proxy):
        session_id = str(uuid.uuid4())
        text = verifycode
        text2 = verifysession

        # Prepare request data
        login_url = "http://ptlogin.4399.com/ptlogin/login.do?v=1"
        cookies = {
            "ptusertype": "kid_wdsj.4399_login",
            "USESSIONID": session_id,
        }
        payload = {
            'postLoginHandler': 'default',
            'externalLogin': 'qq',
            'bizId': '2100001792',
            'appId': 'kid_wdsj',
            'gameId': 'wd',
            'sec': '1',
            'password': self.password,
            'username': self.username
        }

        if text:
            payload['redirectUrl'] = ''
            payload['sessionId'] = text2
            payload['inputCaptcha'] = text

        # Send login request
        response = requests.post(login_url, cookies=cookies, data=payload, proxies=proxy)

        if response.status_code != 200:
            raise Exception(f"登录失败，HTTP错误代码：{response.status_code}，错误信息：{response.text}")

        # Process response cookies
        cookies = requests.utils.dict_from_cookiejar(response.cookies)
        obj = cookies.get("Uauth")
        text5 = cookies.get("Puser")

        if obj is None or text5 is None:
            raise Exception("请检查账号密码是否正确或IP是否被拉黑")

        array = obj.split('|')
        check_url = f"http://ptlogin.4399.com/ptlogin/checkKidLoginUserCookie.do?appId=kid_wdsj&gameUrl=http://cdn.h5wan.4399sj.com/microterminal-h5-frame?game_id=500352&rand_time={array[4]}&nick=null&onLineStart=false&show=1&isCrossDomain=1&retUrl=http%253A%252F%252Fptlogin.4399.com%252Fresource%252Fucenter.html"

        # Prepare second request
        check_response = requests.post(check_url, cookies=cookies, proxies=proxy)

        if check_response.status_code != 200:
            raise Exception(f"校验实名失败，HTTP错误代码：{check_response.status_code}，错误信息：{check_response.text}")

        # Get user info
        user_info_url = "https://microgame.5054399.net/v2/service/sdk/info?callback="
        query_str = check_response.url.split('?')[1].strip()
        response2 = requests.get(user_info_url, params={'queryStr': query_str}, proxies=proxy)

        if response2.status_code != 200:
            raise Exception(f"用户信息获取失败，HTTP错误代码：{response2.status_code}，错误信息：{response2.text}")

        data = response2.json()

        if data['data'] is None:
            raise Exception(f"用户信息获取失败，错误代码：{data['code']}，信息：{data['msg']}")

        dictionary = dict(part.split('=') for part in data['data']['sdk_login_data'].split('&'))
        user_id = dictionary["username"]
        sdk_user_id = dictionary["uid"]
        session_id = dictionary["token"]
        time_stamp = dictionary["time"]

        aim_info = AimInfo(
            ip="127.0.0.1",
            tz="0800",
            tzid="",
            country="CN"
        )

        return SAuth(
            ip="127.0.0.1",
            sdk_user_id=sdk_user_id,
            session_id=session_id,
            udid=self.udid,
            device_id=self.device_id,
            sdk_version="1.0.0",
            app_channel="4399pc",
            login_channel="4399pc",
            real_name=RealName("0"),
            timestamp=time_stamp,
            user_id=user_id,
            device_key="",
            aim_info=aim_info
        )


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
}


# 辅助函数生成指定长度的随机字符串
def randstr(chars, length):
    return ''.join(sample(chars, length))


# 字符集用于生成随机字符串
strings = string.ascii_letters + string.digits
captcha_strings = string.ascii_lowercase + string.digits
ocr = DdddOcr(use_gpu=True, show_ad=False, import_onnx_path="4399ocr/4399ocr.onnx",
              charsets_path="4399ocr/4399ocr.json")


def randfile(file):
    with open(file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        f.close()
    return sample(lines, 1)[0].strip()


def dologin(username, password, proxy):
    author = LoginAuthor(username, password)
    ans = author.check_4399_verify_code(proxy)
    print(ans[0], ans[1])
    url = ans[1]
    session = ans[0]
    captcha_response = ""
    if session != "":
        # ip = randfile("ip.txt")
        proxies = {'https': 'http://127.0.0.1:8089'}
        response = requests.get(
            url,
            headers=headers,
            proxies=proxies
        )
        if response.status_code == 200:
            captcha = ocr.classification(response.content)
            print(f"First try is {captcha}")
            if len(captcha) < 4:
                captcha += randstr(captcha_strings, 4 - len(captcha))
            print(f"验证码识别 {captcha}")
            captcha_response = captcha
        else:
            print(f"错误发生，HTTP状态码: {response.status_code}")

    sauth = author.login(captcha_response, session, proxy)
    login_json = LoginJson(json_str=sauth.to_json())
    with open('Sauths.txt', 'a', encoding='utf-8') as file:
        file.write(f"{login_json.to_json()}\n".replace(" ", ""))


def main():
    temp_file = 'temp_accounts.txt'
    with open('accounts.txt', 'r', encoding='utf-8') as file, open(temp_file, 'w', encoding='utf-8') as temp:
        lines = file.readlines()
        for line in lines:
            print("正在获取: " + line.strip())
            filp = line.split(":")
            username = filp[0].strip()
            password = filp[1].strip()
            # ip = randfile("ip.txt")
            proxies = {'https': 'http://127.0.0.1:8089'}
            try:
                dologin(username, password, proxies)
            except:
                print("生成失败，可能是验证码错误或代理无法使用...")
                print("将继续保留在accounts.txt内(生成结束后)")
                temp.write(line)
            time.sleep(random.randrange(1, 3))
    os.replace(temp_file, 'accounts.txt')
    os.remove(temp_file)


if __name__ == "__main__":
    main()
