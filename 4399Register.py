# -*- coding: utf-8 -*-
from collections import Counter, deque
from random import choice, sample
from string import ascii_letters, ascii_lowercase, digits
from threading import Lock, Thread
from time import sleep, time
import keyboard
from ddddocr import DdddOcr
import requests
from rich.align import Align
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
import rich.box
from dotenv import load_dotenv
import os

load_dotenv()

stats = {
    'total': 0,
    'success': 0,
    'failure': 0,
    'failure_details': Counter(),
    'success_times': deque(),
    'is_paused': False
}
stats_lock = Lock()
start_time = time()
console = Console()


def toggle_pause():
    with stats_lock:
        stats['is_paused'] = not stats['is_paused']


strings = ascii_letters + digits
captcha_strings = ascii_lowercase + digits

USER_AGENT = os.getenv('USER_AGENT')
PROXY = os.getenv('PROXY')
SFZ_FILE = os.getenv('SFZ_FILE')
OCR_FOLDER = os.getenv('OCR_FOLDER')
SYMBOL = os.getenv('SYMBOL')
THREADS = os.getenv('THREADS')


headers = {
    'User-Agent': USER_AGENT
}

proxies = {
    "http": PROXY,
    "https": PROXY
}


try:
    ocr = DdddOcr(use_gpu=True, show_ad=False, import_onnx_path=f"{OCR_FOLDER}/4399ocr.onnx",
                  charsets_path=f"{OCR_FOLDER}/4399ocr.json")
    with open(SFZ_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
except FileNotFoundError as e:
    console.print(f"[bold red]错误: 缺少必要文件: {e.filename}，请确保它在程序目录下。[/bold red]")
    exit()

def randstr(chars, length):
    return ''.join(sample(chars, length))

def get_elapsed_time():
    elapsed = time() - start_time
    hours, rem = divmod(elapsed, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

def register_4399(usr, pwd, count=1):
    try:
        sfz = choice(lines).strip()
        sfz_split = sfz.split(':')

        sessionId = 'captchaReq' + randstr(captcha_strings, 19)
        captcha_response = requests.get(
            f'https://ptlogin.4399.com/ptlogin/captcha.do?captchaId={sessionId}',
            headers=headers,
            proxies=proxies,
            verify=False,
            timeout=10
        ).content
        captcha = ocr.classification(captcha_response)

        data = {
            'postLoginHandler': 'default', 'displayMode': 'popup', 'appId': 'www_home', 'gameId': '', 'cid': '',
            'externalLogin': 'qq', 'aid': '', 'ref': '', 'css': '', 'redirectUrl': '', 'regMode': 'reg_normal',
            'sessionId': sessionId, 'regIdcard': 'true', 'noEmail': '', 'crossDomainIFrame': '', 'crossDomainUrl': '',
            'mainDivId': 'popup_reg_div', 'showRegInfo': 'true', 'includeFcmInfo': 'false', 'expandFcmInput': 'true',
            'fcmFakeValidate': 'false', 'realnameValidate': 'true', 'username': usr, 'password': pwd,
            'passwordveri': pwd, 'email': '', 'inputCaptcha': captcha, 'reg_eula_agree': 'on',
            'realname': sfz_split[0], 'idcard': sfz_split[1]
        }

        response = requests.post(
            'https://ptlogin.4399.com/ptlogin/register.do',
            data=data,
            proxies=proxies,
            headers=headers,
            verify=False,
            timeout=10
        ).text

        if '注册成功' in response:
            result = '生产成功'
            with open('accounts.txt', 'a') as f:
                f.write(f'{usr}:{pwd}\n')
        elif '验证码错误' in response:
            if count >= 5:
                result = "菠萝码超时"
            else:
                return register_4399(usr, pwd, count + 1)
        elif '身份证实名账号数量超过限制' in response: result = '菠萝证种植数量超过限制'
        elif '身份证实名过于频繁' in response: result = '菠萝证种植过于频繁'
        elif '该姓名身份证提交验证过于频繁' in response: result = '该菠萝人的菠萝证种植过于频繁'
        elif '用户名已被注册' in response: result = '该菠萝已被生产'
        else: result = "未知的菠萝"
        
        return result

    except Exception as e:
        error_type = type(e).__name__
        return f"网络异常_{error_type}"

def worker():
    while True:
        with stats_lock:
            is_paused = stats['is_paused']
        
        if is_paused:
            sleep(0.5)
            continue

        usr = SYMBOL[0] + randstr(strings, 3) + SYMBOL[1] + randstr(strings, 3) + SYMBOL[2] + randstr(strings, 3)
        pwd = randstr(strings, 12)
        
        result = register_4399(usr, pwd)
        
        with stats_lock:
            if stats['is_paused']:
                continue
            stats['total'] += 1
            if result == '生产成功':
                stats['success'] += 1
                stats['success_times'].append(time())
            else:
                stats['failure'] += 1
                stats['failure_details'][result] += 1

def make_header() -> Panel:
    with stats_lock:
        is_paused = stats['is_paused']

    title = Text("Pineapple Register", justify="center", style="bold blue")
    
    if is_paused:
        pause_text = Text(" [ PAUSED ]", style="bold yellow")
        title.append(pause_text)

    return Panel(title, box=rich.box.HEAVY, border_style="blue")

def make_stats_panel() -> Panel:
    with stats_lock:
        total = stats['total']
        success = stats['success']
        failure = stats['failure']
        success_times = stats['success_times']
        success_rate = (success / total * 100) if total > 0 else 0

        current_time = time()
        while success_times and success_times[0] < current_time - 60:
            success_times.popleft()
        spm = len(success_times)

    stats_table = Table.grid(expand=True, padding=(0, 1))
    stats_table.add_column(style="cyan", justify="right")
    stats_table.add_column(style="bold magenta", justify="left")
    stats_table.add_row("总尝试", f"{total}")
    stats_table.add_row("[green]生产成功[/green]", f"[green]{success}[/green]")
    stats_table.add_row("[red]生产失败[/red]", f"[red]{failure}[/red]")
    stats_table.add_row("SPM", f"{spm} / min")

    success_progress = Progress(
        TextColumn("成功率", style="cyan"),
        BarColumn(bar_width=None, complete_style="green"),
        TextColumn("[progress.percentage]{task.percentage:>3.1f}%"),
        expand=True
    )
    success_progress.add_task("rate", completed=success_rate)

    content_group = Group(
        stats_table,
        Rule(style="dim blue"),
        success_progress
    )

    return Panel(content_group, title="[bold yellow]核心统计[/bold yellow]", border_style="yellow")

def make_failure_panel() -> Panel:
    with stats_lock:
        failure = stats['failure']
        failure_details = stats['failure_details']

    reasons_table = Table(show_edge=True, title_style="bold red", expand=True, box=rich.box.ROUNDED)
    reasons_table.add_column("原因", style="red", no_wrap=True, ratio=60)
    reasons_table.add_column("数量", style="cyan", ratio=20, justify="center")
    reasons_table.add_column("占比", style="magenta", ratio=20, justify="center")

    if failure > 0:
        sorted_failures = failure_details.most_common(10)
        for reason, count in sorted_failures:
            percentage = (count / failure * 100)
            reasons_table.add_row(reason, str(count), f"{percentage:.1f}%")

    return Panel(reasons_table, title="[bold red]失败分析[/bold red]", border_style="red")

def make_footer() -> Align:
    return Align.center(
        Text(f"运行时长: {get_elapsed_time()} | 按 空格键 暂停/继续 | 按 Ctrl+C 停止", style="bold dim")
    )

def generate_layout() -> Layout:
    layout = Layout(name="root")

    layout.split(
        Layout(make_header(), name="header", size=3),
        Layout(ratio=1, name="main"),
        Layout(make_footer(), name="footer", size=1)
    )

    layout["main"].split_row(
        Layout(make_stats_panel(), name="side"),
        Layout(make_failure_panel(), name="body", ratio=2)
    )
    return layout

if __name__ == "__main__":
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    
    keyboard.on_press_key("space", lambda _: toggle_pause())

    num_threads = int(THREADS)

    for i in range(num_threads):
        thread = Thread(target=worker, daemon=True)
        thread.start()

    try:
        with Live(generate_layout(), screen=True, redirect_stderr=False, refresh_per_second=4) as live:
            while True:
                sleep(0.25)
                live.update(generate_layout())
    except KeyboardInterrupt:
        console.print("\n[bold green]程序已停止。[/bold green]")
    except Exception as e:
        console.print(f"\n[bold red]发生意外错误: {e}[/bold red]")
        console.print_exception()
