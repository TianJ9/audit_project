# import requests
# import json
# question = "How would you build the tallest building ever?"
# url = "https://openrouter.ai/api/v1/chat/completions"
# headers = {
#   "Authorization": f"Bearer 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",
#   "Content-Type": "application/json"
# }
# payload = {
#   "model": "deepseek/deepseek-chat-v3-0324",
#   "messages": [{"role": "user", "content": question}],
#   "stream": True
# }
# buffer = ""
# with requests.post(url, headers=headers, json=payload, stream=True) as r:
#   for chunk in r.iter_content(chunk_size=1024, decode_unicode=True):
#     buffer += chunk
#     while True:
#       try:
#         # Find the next complete SSE line
#         line_end = buffer.find('\n')
#         if line_end == -1:
#           break
#         line = buffer[:line_end].strip()
#         buffer = buffer[line_end + 1:]
#         if line.startswith('data: '):
#           data = line[6:]
#           if data == '[DONE]':
#             break
#           try:
#             data_obj = json.loads(data)
#             content = data_obj["choices"][0]["delta"].get("content")
#             if content:
#               print(content, end="", flush=True)
#           except json.JSONDecodeError:
#             pass
#       except Exception:
#         break

from flask import Flask, Response
import time

app = Flask(__name__)

@app.route("/api/test_stream", methods=["POST"])
def test_stream():
    def generate():
        for i in range(3):
            msg = f"data: 第{i+1}条\n\n"
            print("调试发送:", msg.strip())
            yield msg
            time.sleep(1)
        yield "data: [DONE]\n\n"

    return Response(generate(), mimetype="text/event-stream")

if __name__ == "__main__":
    app.run(port=5000, debug=True)