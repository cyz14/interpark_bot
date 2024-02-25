#!/usr/bin/env python
# encoding=utf-8

import json
import os
import sys
import time
import platform
import pathlib

from DrissionPage import WebPage
from DrissionPage.common import Keys
from DrissionPage.common import By
from DrissionPage.common import wait_until
from DrissionPage.common import make_session_ele
from DrissionPage.common import configs_to_here

logging.basicConfig()
logger = logging.getLogger('logger')
import warnings

from urllib3.exceptions import InsecureRequestWarning

warnings.simplefilter('ignore',InsecureRequestWarning)

import ssl

ssl._create_default_https_context = ssl._create_unverified_context

# ocr
import base64

try:
    import ddddocr
    from NonBrowser import NonBrowser
except Exception as exc:
    pass

import argparse

# import chromedriver_autoinstaller
import chromedriver_autoinstaller_max as chromedriver_autoinstaller

CONST_APP_VERSION = "Max Interpark Bot (2023.02.17)"

CONST_MAXBOT_CONFIG_FILE = 'settings.json'
CONST_MAXBOT_LAST_URL_FILE = "MAXBOT_LAST_URL.txt"
CONST_MAXBOT_INT28_FILE = "MAXBOT_INT28_IDLE.txt"

CONST_HOMEPAGE_DEFAULT = "https://www.globalinterpark.com/"
CONST_INTERPARK_SIGN_IN_URL = "https://www.globalinterpark.com/user/signin"

CONST_CHROME_VERSION_NOT_MATCH_EN="Please download the WebDriver version to match your browser version."
CONST_CHROME_VERSION_NOT_MATCH_TW="請下載與您瀏覽器相同版本的WebDriver版本，或更新您的瀏覽器版本。"

CONST_FROM_TOP_TO_BOTTOM = u"from top to bottom"
CONST_FROM_BOTTOM_TO_TOP = u"from bottom to top"
CONST_RANDOM = u"random"
CONST_SELECT_ORDER_DEFAULT = CONST_FROM_TOP_TO_BOTTOM

CONST_WEBDRIVER_TYPE_SELENIUM = "selenium"
CONST_WEBDRIVER_TYPE_UC = "undetected_chromedriver"
CONST_WEBDRIVER_TYPE_DRISSONPAGE = "drissonpage"


def t_or_f(arg):
    ret = False
    ua = str(arg).upper()
    if 'TRUE'.startswith(ua):
        ret = True
    elif 'YES'.startswith(ua):
        ret = True
    return ret


def sx(s1):
    key = 18
    return ''.join(chr(ord(a) ^ key) for a in s1)


def decryptMe(b):
    s = ""
    if len(b) > 0:
        s = sx(base64.b64decode(b).decode("UTF-8"))
    return s


def encryptMe(s):
    data = ""
    if len(s) > 0:
        data = base64.b64encode(sx(s).encode('UTF-8')).decode("UTF-8")
    return data


def get_app_root():
    # 讀取檔案裡的參數值
    basis = ""
    if hasattr(sys, 'frozen'):
        basis = sys.executable
    else:
        basis = sys.argv[0]
    app_root = os.path.dirname(basis)
    return app_root


def get_config_dict(args):
    app_root = get_app_root()
    config_filepath = os.path.join(app_root, CONST_MAXBOT_CONFIG_FILE)

    # allow assign config by command line.
    if not args.input is None:
        if len(args.input) > 0:
            config_filepath = args.input

    config_dict = None
    if os.paht.isfile(config_filepath):
        with open(config_filepath) as json_data:
            config_dict = json.load(json_data)
    return config_dict


def write_last_url_to_file(url):
    outfile = None
    if platform.system() == 'Windows':
        outfile = open(CONST_MAXBOT_LAST_URL_FILE, 'w', encoding='UTF-8')
    else:
        outfile = open(CONST_MAXBOT_LAST_URL_FILE, 'w')

    if not outfile is None:
        outfile.write("%s" % url)


def read_last_url_from_file():
    ret = ""
    with open(CONST_MAXBOT_LAST_URL_FILE, "r") as text_file:
        ret = text_file.readline()
    return ret


def get_chromedriver_path(webdriver_path):
    chromedriver_path = os.path.join(webdriver_path, "chromedriver")
    if platform.system().lower()=="windows":
        chromedriver_path = os.path.join(webdriver_path, "chromedriver.exe")
    return chromedriver_path


def load_chromdriver_normal(config_dict, webdriver_type):
    show_debug_message = True       # debug.
    show_debug_message = False      # online

    if config_dict["advanced"]["verbose"]:
        show_debug_message = True

    driver = None

    Root_Dir = get_app_root()
    webdriver_path = os.path.join(Root_Dir, "webdriver")
    chromedriver_path = get_chromedriver_path(webdriver_path)

    if not os.path.exists(webdriver_path):
        os.mkdir(webdriver_path)

    return driver


def close_browser_tabs(driver):
    if driver is not None:
        try:
            # drisson attr
            window_handles_count = driver.tabs_count
            if window_handles_count > 1:
                driver.close_other_tabs()
        except Exception as e:
            print(e)


def clean_uc_exe_cache():
    exe_name = "chromedriver%s"

    platform = sys.platform
    if platform.endswith("win32"):
        exe_name %= ".exe"
    if platform.endswith(("linux", "linux2")):
        exe_name %= ""
    if platform.endswith("darwin"):
        exe_name %= ""

    d = ""
    if platform.endswith("win32"):
        d = "~/appdata/roaming/undetected_chromedriver"
    elif "LAMBDA_TASK_ROOT" in os.environ:
        d = "/tmp/undetected_chromedriver"
    elif platform.startswith(("linux", "linux2")):
        d = "~/.local/share/undetected_chromedriver"
    elif platform.endswith("darwin"):
        d = "~/Library/Application Support/undetected_chromedriver"
    else:
        d = "~/.undetected_chromedriver"
    data_path = os.path.abspath(os.path.expanduser(d))

    is_cache_exist = False
    p = pathlib.Path(data_path)
    files = list(p.rglob("*chromedriver*?"))
    for file in files:
        if os.path.exists(str(file)):
            is_cache_exist = True
            try:
                os.unlink(str(file))
            except Exception as exc2:
                print(exc2)
                pass

    return is_cache_exist


def load_chromdriver_uc(config_dict):
    import undetected_chromedriver as uc

    show_debug_message = True        # debug.
    show_debug_message = False       # online

    if config_dict["advanced"]["verbose"]:
        show_debug_message = True

    Root_Dir = get_app_root()
    webdriver_path = os.path.join(Root_Dir, "webdriver")
    chromedriver_path = get_chromedriver_path(webdriver_path)

    if not os.path.exists(webdriver_path):
        os.mkdir(webdriver_path)

    if not os.path.exists(chromedriver_path):
        print("ChromeDriver not exist, try to download to:", webdriver_path)
        chromedriver_autoinstaller.install(path=webdriver_path, make_version_dir=False)
    else:
        print("ChromeDriver exist:", chromedriver_path)

    options = uc.ChromeOptions()
    options.page_load_strategy = 'eager'
    #options.page_load_strategy = 'none'
    options.unhandled_prompt_behavior = "accept"

    #print("strategy", options.page_load_strategy)

    if config_dict["advanced"]["adblock_plus_enable"]:
        load_extension_path = ""
        extension_list = get_favoriate_extension_path(webdriver_path)
        for ext in extension_list:
            ext = ext.replace('.crx','')
            if os.path.exists(ext):
                load_extension_path += ("," + os.path.abspath(ext))
        if len(load_extension_path) > 0:
            print('load-extension:', load_extension_path[1:])
            options.add_argument('--load-extension=' + load_extension_path[1:])

    if config_dict["advanced"]["headless"]:
        #options.add_argument('--headless')
        options.add_argument('--headless=new')
    options.add_argument('--disable-features=TranslateUI')
    options.add_argument('--disable-translate')
    options.add_argument('--lang=zh-TW')
    options.add_argument('--disable-web-security')
    options.add_argument("--no-sandbox");
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-notifications")

    options.add_argument("--password-store=basic")
    options.add_experimental_option("prefs", {"credentials_enable_service": False, "profile.password_manager_enabled": False, "translate":{"enabled": False}})

    driver = None
    if os.path.exists(chromedriver_path):
        # use chromedriver_autodownload instead of uc auto download.
        is_cache_exist = clean_uc_exe_cache()

        try:
            driver = uc.Chrome(driver_executable_path=chromedriver_path, options=options, headless=config_dict["advanced"]["headless"])
        except Exception as exc:
            print(exc)
            error_message = str(exc)
            left_part = None
            if "Stacktrace:" in error_message:
                left_part = error_message.split("Stacktrace:")[0]
                print(left_part)

            if "This version of ChromeDriver only supports Chrome version" in error_message:
                print(CONST_CHROME_VERSION_NOT_MATCH_EN)
                print(CONST_CHROME_VERSION_NOT_MATCH_TW)

            # remove exist chromedriver, download again.
            try:
                print("Deleting exist and download ChromeDriver again.")
                os.unlink(chromedriver_path)
            except Exception as exc2:
                print(exc2)
                pass

            chromedriver_autoinstaller.install(path=webdriver_path, make_version_dir=False)
            try:
                driver = uc.Chrome(driver_executable_path=chromedriver_path, options=options, headless=config_dict["advanced"]["headless"])
            except Exception as exc2:
                pass
    else:
        print("WebDriver not found at path:", chromedriver_path)

    if driver is None:
        print('WebDriver object is None..., try again..')
        try:
            driver = uc.Chrome(options=options, headless=config_dict["advanced"]["headless"])
        except Exception as exc:
            print(exc)
            error_message = str(exc)
            left_part = None
            if "Stacktrace:" in error_message:
                left_part = error_message.split("Stacktrace:")[0]
                print(left_part)

            if "This version of ChromeDriver only supports Chrome version" in error_message:
                print(CONST_CHROME_VERSION_NOT_MATCH_EN)
                print(CONST_CHROME_VERSION_NOT_MATCH_TW)
            pass

    if driver is None:
        print("create web drive object by undetected_chromedriver fail!")

        if os.path.exists(chromedriver_path):
            print("Unable to use undetected_chromedriver, ")
            print("try to use local chromedriver to launch chrome browser.")
            driver_type = "selenium"
            driver = load_chromdriver_normal(config_dict, driver_type)
        else:
            print("建議您自行下載 ChromeDriver 到 webdriver 的資料夾下")
            print("you need manually download ChromeDriver to webdriver folder.")

    return driver


def load_drissonpage(config_dict):
    driver = WebPage()
    return driver


def get_driver_by_config(config_dict):
    global driver

    # read config
    homepage = config_dict["homepage"]

    if config_dict is None:
        homepage = ""
    if len(homepage) == 0:
        homepage = CONST_HOMEPAGE_DEFAULT

    Root_Dir = get_app_root()
    webdriver_path = os.path.join(Root_Dir, "webdriver")
    print("platform.system().lower():", platform.system().lower())

    if config_dict["browser"] in ["chrome", "brave"]:
        # method 6: Selenium Stealth
        if config_dict["webdriver_type"] == CONST_WEBDRIVER_TYPE_SELENIUM:
            driver = load_chromdriver_normal(config_dict, config_dict["webdriver_type"])
        elif config_dict["webdriver_type"] == CONST_WEBDRIVER_TYPE_UC:
            # method 5: uc
            if platform.system.lower() == "windows":
                if hasattr(sys, 'frozen'):
                    from multiprocessing import freeze_support
                    freeze_support()
            driver = load_chromdriver_uc(config_dict)
        elif config_dict["webdriver_type"] == CONST_WEBDRIVER_TYPE_DRISSONPAGE:
            # method DrissonPage
            if platform.system.lower() == "windows":
                if hasattr(sys, 'frozen'):
                    from multiprocessing import freeze_support
                    freeze_support()
            driver = load_drissonpage(config_dict)

    if driver is None:
        print("create web driver object fail @_@;")
    else:
        try:
            print("goto url:", homepage)

            if 'globalinterpark.com' in homepage:
                if len(config_dict["advanced"]["interpark_account"])>0:
                    homepage = CONST_INTERPARK_SIGN_IN_URL

            driver.get(homepage)
            time.sleep(3.0)
        except Exception as exce1:
            print('get URL Exception:', exce1)
            pass

    return driver


def get_current_url(driver):
    DISCONNECTED_MSG = ': target window already closed'

    url = ""
    is_quit_bot = False

    try:
        url = driver.url
    except Exception as exc:
        logger.error('Maxbot URL Exception')
        logger.error(exc, exc_info=True)

        # UnicodeEncodeError: 'ascii' codec can't encode characters in position 63-72: ordinal not in range(128)
        str_exc = ""
        try:
            str_exc = str(exc)
        except Exception as exc2:
            pass

        if len(str_exc) == 0:
            str_exc = repr(exc)

        exit_bot_error_strings = ['Max retries exceeded'
        , 'chrome not reachable'
        , 'unable to connect to renderer'
        , 'failed to check if window was closed'
        , 'Failed to establish a new connection'
        , 'Connection refused'
        , 'disconnected'
        , 'without establishing a connection'
        , 'web view not found'
        , 'invalid session id'
        ]
        for each_error_string in exit_bot_error_strings:
            if isinstance(str_exc, str):
                if each_error_string in str_exc:
                    print('quit bot by error:', each_error_string)
                    is_quit_bot = True
                    driver.quit()
                    sys.exit()

        # not is above case, print exception.
        print("Exception:", str_exc)
        pass

    return url, is_quit_bot


def escape_to_first_tab(driver, main_window_handle):
    try:
        tabs = driver.tabs()
        window_handles_count = len(tabs)
        if window_handles_count == 1:
            pass
        if window_handles_count > 1:
            for tab_id in tabs:
                # switch focus to child window
                if (tab_id != main_window_handle):
                    # driver.switch_to.window(w)
                    driver.set.activate(tab_id)
                    break
    except Exception as e:
        print("Escape tab exception: ", e)

def interpark_main(driver, config_dict, url, ocr, interpark_dict):
    escape_to_first_tab(driver, interpark_dict["main_window_handle"])
    

def main(args):
    config_dict = get_config_dict(args)

    driver = None
    if config_dict is not None:
        driver = get_driver_by_config(config_dict)
    else:
        print("Load config error!")
    
    # internal variable. 說明：這是一個內部變數，請略過。
    url = ""
    last_url = ""

    interpark_dict = {}
    interpark_dict["opener_popuped"] = False
    interpark_dict["main_window_handle"] = None
    interpark_dict["is_step_1_submited"] = False

    ocr = None
    try:
        if config_dict["ocr_captcha"]["enable"]:
            ocr = ddddocr.DdddOcr(show_ad=False, beta=config_dict["ocr_captcha"]["beta"])
    except Exception as exc:
        print(exc)
        pass

    while True:
        time.sleep(0.05)

        # pass if driver is not loaded
        if driver is None:
            print("web driver not accessible!")
            break

        url, is_quit_bot = get_current_url(driver)
        if is_quit_bot:
            break

        if url is None:
            continue
        else:
            if len(url) == 0:
                continue

        is_maxbot_paused = False
        if os.path.exists(CONST_MAXBOT_INT28_FILE):
            is_maxbot_paused = True

        if len(url) > 0:
            if url != last_url:
                print(url)
                write_last_url_to_file(url)
                if is_maxbot_paused:
                    print("MAXBOT Paused.")
            last_url = url

        if is_maxbot_paused:
            time.sleep(0.2)
            continue

        if len(url) > 0:
            if url != last_url:
                print(url)
            last_url = url

        if "globalinterpark.com" in url:
            if interpark_dict["main_window_handle"] is None:
                interpark_dict["main_window_handle"] = driver.get_tab()

            interpark_dict = interpark_main(driver, config_dict, url, ocr, interpark_dict)
            


def cli():
    parser = argparse.ArgumentParser(
        description="MaxBot Argument Parser"
    )

    parser.add_argument("--input",
        help="config file path",
        type=str
    )

    args = parser.parse_args()
    main(args)

if __name__ == '__main__':
    cli()