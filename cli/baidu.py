import json

import typer
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from utils.pyredis import get_redis_client_sync

app = typer.Typer()

r = get_redis_client_sync()


@app.command()
def acsToken(
    url: str = typer.Argument(
        "https://gushitong.baidu.com/index/ab-000001?name=%25E4%25B8%258A%25E8%25AF%2581%25E6%258C%2587%25E6%2595%25B0",
        help="request url",
    ),
    timeout: int = typer.Option(
        3,
        "--timeout",
        "-t",
        help="timeout内如果没有请求完整,会强制中断,然后从已有的请求中获取数据",
    ),
):
    """通过selenium获取百度股事通Acs-Token

    Args:
        url (str, optional): 请求的『URL』地址. Defaults to typer.Argument( "https://gushitong.baidu.com/", help="request url", ).
        timeout (int, optional): _description_. Defaults to typer.Option( 3, "--timeout", "-t", help="timeout内如果没有请求完整,会强制中断,然后从已有的请求中获取数据", ).

    Returns:
        str: 『Acs-Token』字符串
    """
    # 配置 Chrome 浏览器以启用 Performance API
    chrome_options = Options()
    chrome_options.add_argument("--enable-logging")
    chrome_options.add_argument("--v=1")
    chrome_options.add_argument("--headless")  # 启用无头模式
    chrome_options.add_argument("--disable-gpu")  # 禁用 GPU 加速
    chrome_options.add_argument("--window-size=1920,1080")  # 设置窗口大小
    chrome_options.add_argument("--no-sandbox")  # 禁用沙盒模式
    chrome_options.add_argument("--disable-dev-shm-usage")  # 禁用 /dev/shm 使用
    chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chrome_options
    )
    driver.set_page_load_timeout(timeout)

    try:
        driver.get(url)
    except Exception:
        driver.execute_script("window.stop();")

    # 从网络请求中提取 Acs-Token
    acs_token = get_acs_token_from_requests(driver)

    driver.quit()

    if acs_token:
        print(f"Acs-Token:『{acs_token}』")
        r.set("baidu.Acs-Token", acs_token)

    return acs_token


def get_acs_token_from_requests(driver):
    """从网络请求中提取 Acs-Token"""
    # 获取性能日志

    logs = driver.get_log("performance")

    for entry in logs:
        log = json.loads(entry["message"])["message"]

        # 检查是否是网络请求
        if log["method"] == "Network.requestWillBeSent":
            request = log["params"].get("request", {})
            headers = request.get("headers", {})

            # 检查请求头中是否包含 Acs-Token
            if "Acs-Token" in headers:
                return headers["Acs-Token"]

    return ""


if __name__ == "__main__":
    app()
