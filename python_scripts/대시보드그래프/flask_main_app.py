# flask_main_app.py

from flask import Flask, render_template

# Flask 애플리케이션 초기화
app = Flask(__name__)

# 메인 페이지 라우트 정의
@app.route('/')
def index():
    """
    메인 HTML 템플릿(main_page.html)을 렌더링합니다.
    이 템플릿 내부에 Dash 그래프를 로드하는 <iframe> 태그들이 포함되어 있습니다.
    """
    return render_template('main_page.html')

if __name__ == '__main__':
    # Flask 앱을 5000번 포트로 실행합니다.
    # Dash 앱은 8051번 포트로 실행되어야 합니다.
    print("=" * 80)
    print("### 🌐 Flask 메인 웹 서버 (port:5000) 실행 중... ")
    print("   ➡️ http://127.0.0.1:5000/ 에 접속하세요.")
    print("   ⚠️ Dash 서버(8051)가 먼저 실행되어 있어야 합니다.")
    print("=" * 80)
    app.run(host='0.0.0.0',debug=True, port=5000)