
# 虽然相较于CookieGenerator有了不少优化，但是似乎暂时无法使用，请不要投入生产！如果你可以修复它或者优化它的代码逻辑，请提交PR。
# 这是一个库，并不能直接使用。

from requests import get, post
from json import dumps
from uuid import uuid4
from re import search
from ddddocr import DdddOcr

#proxies = {'https': 'http://127.0.0.1:8089', 'http': 'http://127.0.0.1:8089'}
proxies = {}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
}

ocr = DdddOcr(use_gpu=True, show_ad=False, import_onnx_path="4399ocr/4399ocr.onnx", charsets_path="4399ocr/4399ocr.json")

def generate_uuid():
    return str(uuid4()).replace("-", "").upper()

def check_verify_code(username):
    url = f"http://ptlogin.4399.com/ptlogin/verify.do?username={username}&appId=kid_wdsj&t={uuid4()}&inputWidth=iptw2&v=1"
    response = get(url, cookies={"USESSIONID": generate_uuid()}, proxies=proxies, headers=headers)
    match = search(r"/ptlogin/captcha\.do\?captchaId=[\w\d]+", response.text)
    return (match.group(0).split("=")[1], f"http://ptlogin.4399.com{match.group(0)}") if match else ("", "")

def process_captcha(captcha_url):
    print("需要验证")
    captcha_image = get(captcha_url, proxies=proxies, headers=headers).content
    while True:
        captcha = ocr.classification(captcha_image)
        if len(captcha) == 4 and captcha.isalnum():
            return captcha.lower()
        print("验证码格式错误")

def login(username, password, verifycode="", verifysession=""):
    login_url = "http://ptlogin.4399.com/ptlogin/login.do?v=1"
    payload = {
        'postLoginHandler': 'default',
        'externalLogin': 'qq',
        'bizId': '2100001792',
        'appId': 'kid_wdsj',
        'gameId': 'wd',
        'sec': '1',
        'password': password,
        'username': username,
        'redirectUrl': '',
        'sessionId': verifysession,
        'inputCaptcha': verifycode
    } if verifycode else {
        'postLoginHandler': 'default',
        'externalLogin': 'qq',
        'bizId': '2100001792',
        'appId': 'kid_wdsj',
        'gameId': 'wd',
        'sec': '1',
        'password': password,
        'username': username
    }
    response = post(login_url, cookies={"ptusertype": "kid_wdsj.4399_login", "USESSIONID": generate_uuid()}, data=payload, proxies=proxies, headers=headers)
    if response.status_code != 200:
        raise Exception(f"登录失败，HTTP错误代码：{response.status_code}，错误信息：{response.text}")
    cookies = response.cookies.get_dict()
    if not cookies.get("Uauth") or not cookies.get("Puser"):
        raise Exception("请检查账号密码是否正确或IP是否被拉黑")
    check_url = f"http://ptlogin.4399.com/ptlogin/checkKidLoginUserCookie.do?appId=kid_wdsj&gameUrl=http://cdn.h5wan.4399sj.com/microterminal-h5-frame?game_id=500352&rand_time={cookies['Uauth'].split('|')[4]}&nick=null&onLineStart=false&show=1&isCrossDomain=1&retUrl=http%253A%252F%252Fptlogin.4399.com%252Fresource%252Fucenter.html"
    check_response = post(check_url, cookies=cookies, proxies=proxies, headers=headers)
    if check_response.status_code != 200:
        raise Exception(f"校验实名失败，HTTP错误代码：{check_response.status_code}，错误信息：{check_response.text}")
    user_info = get("https://microgame.5054399.net/v2/service/sdk/info?callback=", params={'queryStr': check_response.url.split('?')[1].strip()}, proxies=proxies, headers=headers).json()
    if not user_info.get('data'):
        raise Exception(f"用户信息获取失败，错误代码：{user_info.get('code')}，信息：{user_info.get('msg')}")
    return {k: v for k, v in (item.split('=') for item in user_info['data']['sdk_login_data'].split('&'))}

def get_cookie(username, password):
    try:
        print("检测验证码")
        session_id, captcha_url = check_verify_code(username)
        captcha = process_captcha(captcha_url) if captcha_url else ""
        user_data = login(username, password, captcha, session_id)
        sauth_data = {
            "gameid": "x19",
            "login_channel": "4399pc",
            "app_channel": "4399pc",
            "platform": "pc",
            "sdkuid": user_data["uid"],
            "sessionid": user_data["token"],
            "sdk_version": "1.0.0",
            "udid": generate_uuid(),
            "deviceid": generate_uuid(),
            "aim_info": dumps({"aim": "127.0.0.1", "country": "CN", "tz": "0800", "tzid": ""}),
            "client_login_sn": generate_uuid(),
            "gas_token": "",
            "source_platform": "pc",
            "ip": "127.0.0.1",
            "userid": user_data["username"],
            "realname": dumps({"realname_type": "0"}),
            "timestamp": user_data["time"]
        }
        return dumps({"sauth_json": dumps(sauth_data)}).replace(" ", "")
    except Exception as e:
        print(f"登录异常: {str(e)}")
        return None
