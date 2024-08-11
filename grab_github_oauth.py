from flask import Flask, request

app = Flask(__name__)

@app.route('/github/callback')
def github_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    print(f"OAuth Credentials received!<br>Code: {code}<br>State: {state}")
    return f"OAuth Credentials received!<br>Code: {code}<br>State: {state}"

if __name__ == "__main__":
    app.run(port=8080)
