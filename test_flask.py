from flask import Flask, request, jsonify
import json

app = Flask(__name__)

def my_function(query):
    return f"收到的 query: {query}"

@app.route('/api/process', methods=['POST'])
def process():
    data = request.get_json()
    query = data.get("query", "")
    result = my_function(query)
    # 用 json.dumps 并 ensure_ascii=False
    return app.response_class(
        response=json.dumps({"result": result}, ensure_ascii=False),
        status=200,
        mimetype='application/json'
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

# curl -X POST https://a4bd0695f1d2.ngrok-free.app/api/process \
#      -H "Content-Type: application/json" \
#      -d '{"query": "你好"}'