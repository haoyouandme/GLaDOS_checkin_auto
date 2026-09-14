import requests
import json
import os
from urllib.parse import quote


# -------------------------------------------------------------------------------------------
# GitHub Actions - GLaDOS 自动签到
# -------------------------------------------------------------------------------------------

if __name__ == '__main__':

    # PushPlus 秘钥
    sckey = os.environ.get("PUSHPLUS_TOKEN", "")

    # GLaDOS Cookie
    cookie_env = os.environ.get("GLADOS_COOKIE", "")
    cookies = cookie_env.split("&") if cookie_env else []

    if not cookies or cookies[0] == "":
        print("未获取到 COOKIE 变量")
        exit(0)

    # ---------------------------------------------------------------------------------------
    # GLaDOS API
    # ---------------------------------------------------------------------------------------

    url = "https://glados.cloud/api/user/checkin"
    url2 = "https://glados.cloud/api/user/status"

    referer = "https://glados.cloud/console/checkin"
    origin = "https://glados.cloud"

    useragent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/102.0.0.0 Safari/537.36"
    )

    payload = {
        "token": "glados.cloud"
    }

    # PushPlus 汇总内容
    sendContent = ""

    session = requests.Session()

    # ---------------------------------------------------------------------------------------
    # 多账号签到
    # ---------------------------------------------------------------------------------------

    for index, cookie in enumerate(cookies, start=1):

        print("")
        print("========================================")
        print("开始处理第 {} 个账号".format(index))
        print("========================================")

        headers = {
            "cookie": cookie.strip(),
            "referer": referer,
            "origin": origin,
            "user-agent": useragent,
            "content-type": "application/json;charset=UTF-8",
        }

        # -------------------------------------------------------------------------------
        # 签到
        # -------------------------------------------------------------------------------

        try:
            checkin = session.post(
                url,
                headers=headers,
                data=json.dumps(payload),
                timeout=20
            )

            print("签到接口 HTTP 状态码：{}".format(checkin.status_code))

        except requests.RequestException as e:
            print("签到请求失败：{}".format(e))
            sendContent += "账号{}：签到请求失败\n".format(index)
            continue

        # -------------------------------------------------------------------------------
        # 解析签到结果
        # -------------------------------------------------------------------------------

        checkin_data = None

        try:
            checkin_data = checkin.json()
        except ValueError:
            print("签到接口返回的不是 JSON")
            print("签到接口返回内容：")
            print(checkin.text[:500])

        if isinstance(checkin_data, dict):
            message = checkin_data.get("message")

            if message:
                print("签到结果：{}".format(message))
            else:
                print("签到接口返回：{}".format(checkin_data))

        # -------------------------------------------------------------------------------
        # 查询账号状态
        # -------------------------------------------------------------------------------

        try:
            state = session.get(
                url2,
                headers=headers,
                timeout=20
            )

            print("状态接口 HTTP 状态码：{}".format(state.status_code))

        except requests.RequestException as e:
            print("状态请求失败：{}".format(e))
            sendContent += "账号{}：状态请求失败\n".format(index)
            continue

        # -------------------------------------------------------------------------------
        # 解析状态
        # -------------------------------------------------------------------------------

        try:
            state_data = state.json()
        except ValueError:

            print("")
            print("******** 状态接口返回的不是 JSON ********")
            print("HTTP 状态码：{}".format(state.status_code))
            print("Content-Type：{}".format(
                state.headers.get("Content-Type", "")
            ))
            print("返回内容：")
            print(state.text[:1000])
            print("****************************************")

            sendContent += "账号{}：状态接口返回非 JSON\n".format(index)
            continue

        # -------------------------------------------------------------------------------
        # 获取账号信息
        # -------------------------------------------------------------------------------

        try:

            data = state_data.get("data", {})

            email = data.get("email", "未知账号")
            left_days = data.get("leftDays", "未知")

            if left_days != "未知":
                left_days = str(left_days).split(".")[0]

            print(
                "{}----签到完成----剩余({})天".format(
                    email,
                    left_days
                )
            )

            # 签到结果
            if isinstance(checkin_data, dict) and checkin_data.get("message"):

                message = checkin_data["message"]

                sendContent += (
                    "{}----{}----剩余({})天\n".format(
                        email,
                        message,
                        left_days
                    )
                )

            else:

                sendContent += (
                    "{}----签到接口异常----剩余({})天\n".format(
                        email,
                        left_days
                    )
                )

        except Exception as e:

            print("解析账号状态失败：{}".format(e))
            print("状态 JSON：{}".format(state_data))

            sendContent += (
                "账号{}：解析状态失败\n".format(index)
            )

    # ---------------------------------------------------------------------------------------
    # PushPlus 推送
    # ---------------------------------------------------------------------------------------

    if sckey != "" and sendContent != "":

        try:

            title = "GLaDOS签到"

            push_url = (
                "http://www.pushplus.plus/send"
                "?token={}"
                "&title={}"
                "&content={}"
            ).format(
                quote(sckey),
                quote(title),
                quote(sendContent)
            )

            push = requests.get(
                push_url,
                timeout=20
            )

            print("")
            print("PushPlus HTTP 状态码：{}".format(push.status_code))
            print("PushPlus 返回：{}".format(push.text[:500]))

        except requests.RequestException as e:

            print("PushPlus 推送失败：{}".format(e))

    print("")
    print("========================================")
    print("所有账号处理完成")
    print("========================================")
