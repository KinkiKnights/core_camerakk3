import rclpy
from rclpy.node import Node
from kk_driver_msg.msg import CameraCmd, MouseCtrl
import time
import threading

import asyncio
import websockets

camera_id = 0;
target = 127;
ros_args = None

class CameraMouseNode(Node):
    def __init__(self):
        super().__init__('camera_mouse_node')
        
        # /cameraトピックからCameraCmdメッセージをサブスクライブ
        self.subscription = self.create_subscription(
            CameraCmd,
            '/camera',
            self.camera_callback,
            10
        )
        
        # /auto_targetトピックにMouseCtrlメッセージをパブリッシュ
        self.publisher = self.create_publisher(MouseCtrl, '/auto_target', 10)
        
        # 0.1秒ごとにMouseCtrlメッセージをパブリッシュするタイマー
        self.timer = self.create_timer(0.1, self.timer_callback)
        
        # MouseCtrlメッセージの初期化
        self.mouse_ctrl = MouseCtrl()
        self.mouse_ctrl.x = 0  # 初期値

    def camera_callback(self, msg):
        global camera_id;
        # CameraCmdメッセージを受信したときの処理
        camera_id = msg.camera_id

    def timer_callback(self):
        global target, camera_id
        # 0.1秒ごとにMouseCtrlメッセージをパブリッシュ
        self.mouse_ctrl.x = target
        self.publisher.publish(self.mouse_ctrl)
def run_spin():
    global ros_args
    rclpy.init(args=ros_args)
    node = CameraMouseNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

async def websocket_handler(websocket):
    global target
    print("WebSocket 接続完了")

    try:
        # クライアントに定期的に camera_id を送信するタスクを作成
        async def send_camera_id():
            while True:
                await websocket.send(str(camera_id))
                await asyncio.sleep(0.1)  # 0.1秒待機

        # メッセージ受信と camera_id 送信を並行して実行
        send_task = asyncio.create_task(send_camera_id())
        async for message in websocket:
            print(f"受信データ: {message}")
            try:
                targets = list(map(int, message.split(',')))
                target = targets[0]
            except ValueError:
                print("数値変換エラー")
    except websockets.exceptions.ConnectionClosed:
        print("WebSocket 切断")
    finally:
        # タスクが終了したらキャンセルする
        send_task.cancel()

async def ws_wait():
    async with websockets.serve(websocket_handler, "0.0.0.0", 8123):
        print("WebSocket start listen (ws://0.0.0.0:8123)")
        await asyncio.Future()

# メインループを開始


def main(args=None):
    global ros_args
    ros_args = args
    ros_thread = threading.Thread(target=run_spin)
    ros_thread.daemon = True
    ros_thread.start()
    asyncio.run(ws_wait())


if __name__ == '__main__':
    main()