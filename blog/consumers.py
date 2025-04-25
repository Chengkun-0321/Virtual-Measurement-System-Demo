import paramiko  # 用來建立 SSH 連線
import json  # 處理前端送來的 JSON 格式資料
from channels.generic.websocket import AsyncWebsocketConsumer  # Django Channels 的 WebSocket 消費者

class TrainConsumer(AsyncWebsocketConsumer):
    # 當有 WebSocket 連線進來時會觸發
    async def connect(self):
        await self.accept()  # 接受 WebSocket 連線
        print("WebSocket 已建立連線")

    # 當前端送資料過來時會觸發
    async def receive(self, text_data):
        data = json.loads(text_data)    # 解析前端傳來的 JSON 字串為 Python 字典
        hostname = data['hostname']     # 取得 SSH 連線所需的 hostname
        port = int(data['port'])        # 取得 SSH 連線所需的 port，並轉為整數
        username = data['username']     # 取得 SSH 連線所需的使用者名稱
        password = data['password']     # 取得 SSH 連線所需的密碼

        print(f"接收到 SSH 連線資料：hostname={hostname}, port={port}, username={username}")  # 紀錄一下收到的連線資訊

        # 建立 SSH 連線
        ssh = paramiko.SSHClient()  # 初始化 SSH Client
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 自動接受不在 known_hosts 的主機金鑰
        try:
            ssh.connect(hostname=hostname, port=port, username=username, password=password)
            await self.send("✅ SSH 連線成功！")  # 成功建立 SSH 後回傳訊息給前端

            # 取得遠端系統資訊
            stdin, stdout, stderr = ssh.exec_command("uname -a")
            sysinfo = stdout.read().decode().strip()
            await self.send(f"🖥️ 遠端系統資訊：{sysinfo}")

        except Exception as e:
            await self.send(f"❌ SSH 連線失敗：{str(e)}")
            return  # 失敗時中止後續流程
        
        # 要在遠端執行的指令（可以改成你要訓練模型的指令）
        cmd = "echo 'Hello from remote!'"
        stdin, stdout, stderr = ssh.exec_command(cmd)  # 執行指令，並取得標準輸出、錯誤輸出

        # 逐行讀取遠端回傳的標準輸出，並透過 WebSocket 傳回前端
        for line in stdout:
            await self.send(line.strip())  # 把每行輸出的內容傳回前端（即時顯示）

        ssh.close()  # 關閉 SSH 連線