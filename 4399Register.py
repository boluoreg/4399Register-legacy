# -*- coding: utf-8 -*-
from requests import get, post
from random import sample, choice
from ddddocr import DdddOcr
from time import time
from string import ascii_letters, digits, ascii_lowercase
from logging import getLogger, StreamHandler, Formatter, INFO
from threading import Thread, current_thread

strings = ascii_letters + digits
captcha_strings = ascii_lowercase + digits

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
}

proxies = {'https': 'http://127.0.0.1:8089'}

log = getLogger()
log.setLevel(INFO)
console_handler = StreamHandler()
console_handler.setLevel(INFO)
formatter = Formatter('[%(asctime)s %(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
console_handler.setFormatter(formatter)
log.addHandler(console_handler)


ocr = DdddOcr(use_gpu=True, show_ad=False, import_onnx_path="4399ocr/4399ocr.onnx",
              charsets_path="4399ocr/4399ocr.json")

with open("sfz.txt", 'r', encoding='utf-8') as f:
    lines = f.readlines()
    f.close()

def randstr(chars, length):
    return ''.join(sample(chars, length))

def time_how(start):
    return f"{(time() - start):.2f}"

def register_4399(usr, pwd):
    start = time()
    sfz = choice(lines).strip()
    sfz_split = sfz.split(':')

    log.info(f"({current_thread().name}) 菠萝证 {sfz}")

    sessionId = 'captchaReq' + randstr(captcha_strings, 19)
    captcha_response = get(
        f'https://ptlogin.4399.com/ptlogin/captcha.do?captchaId={sessionId}',
        headers=headers,
        proxies=proxies,
        verify=False
    ).content
    captcha = ocr.classification(captcha_response)
    log.info(f"({current_thread().name}) 菠萝码识别 {captcha}")

    data = {
        'postLoginHandler': 'default',
        'displayMode': 'popup',
        'appId': 'www_home',
        'gameId': '',
        'cid': '',
        'externalLogin': 'qq',
        'aid': '',
        'ref': '',
        'css': '',
        'redirectUrl': '',
        'regMode': 'reg_normal',
        'sessionId': sessionId,
        'regIdcard': 'true',
        'noEmail': '',
        'crossDomainIFrame': '',
        'crossDomainUrl': '',
        'mainDivId': 'popup_reg_div',
        'showRegInfo': 'true',
        'includeFcmInfo': 'false',
        'expandFcmInput': 'true',
        'fcmFakeValidate': 'false',
        'realnameValidate': 'true',
        'username': usr,
        'password': pwd,
        'passwordveri': pwd,
        'email': '',
        'inputCaptcha': captcha,
        'reg_eula_agree': 'on',
        'realname': sfz_split[0],
        'idcard': sfz_split[1]
    }

    response = post(
        'https://ptlogin.4399.com/ptlogin/register.do',
        data=data,
        proxies=proxies,
        headers=headers,
        verify=False
    ).text

    if '注册成功' in response:
        result = '生产成功'
        with open('accounts.txt', 'a') as f:
            f.write(f'{usr}:{pwd}\n')
            f.close()
    elif '身份证实名账号数量超过限制' in response:
        result = '菠萝证种植数量超过限制'
    elif '身份证实名过于频繁' in response:
        result = '菠萝证种植过于频繁'
    elif '该姓名身份证提交验证过于频繁' in response:
        result = '该菠萝人的菠萝证种植过于频繁'
    elif '用户名已被注册' in response:
        result = '该菠萝已被生产'
    else:
        result = "未知的菠萝"

    if '验证码错误' in response:
        log.info(f"({current_thread().name}) 耗时 {time_how(start)}s 菠萝码错误")
        result = register_4399(usr, pwd)
    else:
        log.info(f"({current_thread().name}) 耗时 {time_how(start)}s {result}")

    return result

def main():
    while True:
        try:
            start = time()
            usr = "S" + randstr(strings, 3) + "K" + randstr(strings, 3) + "Y" + randstr(strings, 3)
            pwd = randstr(strings, 12)
            log.info(f"({current_thread().name}) 🍍 尝试生产菠萝 {usr}:{pwd}")
            result = register_4399(usr, pwd)
            log.info(f"({current_thread().name}) 总耗时 {time_how(start)}s {result}")
        except Exception as e:
            log.warning(f"({current_thread().name}) {e}")

if __name__ == "__main__":
    num_threads = 100
    threads = []

    for i in range(num_threads):
        thread = Thread(target=main, name=f"{i+1}")
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
