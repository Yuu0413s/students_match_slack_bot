import os
import time
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# .env ファイルを探して読み込む
load_dotenv()

# ボットトークンを渡してアプリを初期化します
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))


@app.message("メール検索")
def lookup_and_send(message, say, client): 
    
    # 1. メールアドレスを定義（本来はメッセージから抽出したりしますが、まずは固定でテスト）
    target_email = ""

    try:
        # 2. APIを使って検索（さっきの翻訳ルールを使って！）
        # users.lookupByEmail を Python語に翻訳してください
        result = client.users_lookupByEmail(email=target_email)

        # 3. 結果からIDを取り出す（ResponseのJSONを見て！）
        # userの中にあるidを取り出します
        user_id = result["user"]["id"]


        # 4. 見つけたIDに向かってメッセージを送る
        # chat.postMessage を Python語に翻訳してください
        # 引数 channel には、さっき見つけた user_id を入れます
        post_result = client.chat_postMessage(
            blocks=[
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"メールアドレスから検索して送りました！"},
                    "accessory": {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "クリックボタン"},
                        "action_id": "button_click"
                    }
                }
            ],
            text="メールアドレスから検索して送りました！",
            channel=user_id, 
        )

        # ts = post_result["ts"]
        # channel = post_result["channel"]

    except Exception as e:
        # メールが見つからないとエラーになるので、失敗した時の処理
        say(f"エラーが発生しました: {e}")

@app.action("button_click")
def action_button_click(ack, client, body, say):
    try:
        # アクションを確認したことを即時で応答します
        ack()

        ts_float = float(body['actions'][0]['action_ts'])
        struct_time = time.localtime(ts_float)
        formatted_time = time.strftime("%Y年%m月%d日 %H時%M分%S秒", struct_time)
        # 現在の時刻を取得
        

        # ここで chat.update を使ってメッセージを編集します
        client.chat_update(
            channel = body["channel"]["id"],
            ts = body["message"]["ts"],
            text = "メッセージを編集しました" \
            f"{formatted_time}にクリックされました",
        )

    except Exception as e:
        # メールが見つからないとエラーになるので、失敗した時の処理
        say(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    # アプリを起動して、ソケットモードで Slack に接続します
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()