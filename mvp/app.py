from flask import Flask, render_template, request, jsonify, session
import os
from dotenv import load_dotenv
from ai_service import AIService
from database import Database
import json
import uuid

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# サービス初期化
ai_service = AIService(os.getenv('OPENAI_API_KEY'))
db = Database('mvp.db')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """1on1テキストを分析"""
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'テキストが入力されていません'}), 400
    
    try:
        # セッションID生成
        session_id = str(uuid.uuid4())
        
        # テキストを保存
        db.save_session(session_id, text)
        
        # AI分析実行
        analysis_result = ai_service.analyze_text(text)
        
        # 結果を保存
        db.update_session_analysis(session_id, analysis_result)
        
        # セッションに保存
        session['current_session_id'] = session_id
        
        return jsonify({
            'session_id': session_id,
            'analysis': analysis_result
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """改善点に対する対話"""
    data = request.get_json()
    session_id = data.get('session_id')
    improvement_point = data.get('improvement_point')
    user_response = data.get('response', '')
    
    try:
        # 対話履歴を取得
        history = db.get_chat_history(session_id, improvement_point)
        
        # 次の質問を生成
        next_question = ai_service.generate_question(
            improvement_point, 
            history, 
            user_response
        )
        
        # 履歴に追加
        if user_response:
            db.add_chat_history(session_id, improvement_point, 'user', user_response)
        if next_question.get('question'):
            db.add_chat_history(session_id, improvement_point, 'ai', next_question['question'])
        
        return jsonify(next_question)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-plan', methods=['POST'])
def generate_plan():
    """アクションプラン生成"""
    data = request.get_json()
    session_id = data.get('session_id')
    
    try:
        # セッション情報取得
        session_data = db.get_session(session_id)
        chat_histories = db.get_all_chat_histories(session_id)
        
        # アクションプラン生成
        action_plan = ai_service.generate_action_plan(
            session_data['analysis'],
            chat_histories
        )
        
        # プランを保存
        db.save_action_plan(session_id, action_plan)
        
        return jsonify({'action_plan': action_plan})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>')
def get_session(session_id):
    """セッション情報取得"""
    try:
        session_data = db.get_session(session_id)
        return jsonify(session_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

if __name__ == '__main__':
    # データベース初期化
    db.init_db()
    
    # 開発サーバー起動
    app.run(debug=True, port=5000)