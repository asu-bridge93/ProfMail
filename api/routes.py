"""
FastAPI ルート定義 (統一UI版 + チャットボット)
"""
import sqlite3
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from services.email_processor import EmailProcessor
from templates.html_generator import (
    generate_email_cards,
    generate_category_list,
    generate_completed_email_rows,
    generate_email_table_rows
)
from config import EMAIL_CATEGORIES, SCHEDULER_HOUR, SCHEDULER_MINUTE


def create_routes(app: FastAPI, email_processor: EmailProcessor):
    """FastAPI ルートを作成"""
    
    @app.get("/", response_class=HTMLResponse)
    async def dashboard():
        """教授向けダッシュボード"""
        stats = email_processor.get_database().get_statistics()
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ProfMail</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    margin: 0; 
                    padding: 45px; 
                    background: linear-gradient(135deg, #fdfcf5 0%, #f8f9fb 100%); 
                    min-height: 100vh; 
                    color: #2c3e50;
                }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .header {{ 
                    text-align: center; 
                    color: #34495e; 
                    margin-bottom: 30px; 
                    background: rgba(255, 255, 255, 0.9);
                    padding: 20px;
                    border-radius: 15px;
                    box-shadow: 0 4px 20px rgba(52, 73, 94, 0.08);
                    border: 1px solid #e8f4fd;
                }}
                .header h1 {{ 
                    font-size: 2.5em; 
                    margin-bottom: 10px; 
                    background: linear-gradient(45deg, #4a90e2, #6bb6ff);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                }}
                .header p {{ font-size: 1.2em; opacity: 0.8; color: #5a6c7d; }}
                .dashboard {{ display: grid; grid-template-columns: 1fr 2fr; gap: 20px; }}
                .sidebar {{ 
                    background: rgba(255, 255, 255, 0.95); 
                    border-radius: 15px; 
                    padding: 20px; 
                    box-shadow: 0 4px 20px rgba(52, 73, 94, 0.06);
                    border: 1px solid #e8f4fd;
                }}
                .main-content {{ 
                    background: rgba(255, 255, 255, 0.95); 
                    border-radius: 15px; 
                    padding: 20px; 
                    box-shadow: 0 4px 20px rgba(52, 73, 94, 0.06);
                    border: 1px solid #e8f4fd;
                }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 20px; }}
                .stat-box {{ 
                    background: linear-gradient(135deg, #6bb6ff 0%, #4a90e2 100%); 
                    padding: 20px; 
                    border-radius: 12px; 
                    text-align: center; 
                    color: white;
                    text-decoration: none;
                    transition: transform 0.3s ease;
                    border: 1px solid #e1f4fd;
                    box-shadow: 0 2px 12px rgba(74, 144, 226, 0.15);
                }}
                .stat-box:hover {{ transform: translateY(-2px); box-shadow: 0 4px 20px rgba(74, 144, 226, 0.25); }}
                .stat-number {{ font-size: 2em; font-weight: bold; }}
                .stat-label {{ font-size: 0.9em; opacity: 0.95; }}
                .category-list {{ list-style: none; padding: 0; }}
                .category-item {{ 
                    background: #fbfcfd; 
                    margin: 10px 0; 
                    padding: 15px; 
                    border-radius: 10px; 
                    cursor: pointer; 
                    transition: all 0.3s; 
                    border-left: 4px solid #6bb6ff;
                    border: 1px solid #e8f4fd;
                    box-shadow: 0 1px 6px rgba(52, 73, 94, 0.04);
                }}
                .category-item:hover {{ 
                    transform: translateX(3px); 
                    box-shadow: 0 2px 12px rgba(107, 182, 255, 0.15);
                    background: #f0f8ff;
                    border-left-color: #4a90e2;
                }}
                .category-icon {{ font-size: 1.5em; margin-right: 10px; }}
                .category-count {{ 
                    float: right; 
                    background: linear-gradient(135deg, #6bb6ff, #4a90e2); 
                    color: white; 
                    padding: 4px 10px; 
                    border-radius: 12px; 
                    font-size: 0.8em; 
                    font-weight: 600;
                    box-shadow: 0 1px 4px rgba(74, 144, 226, 0.2);
                }}
                /* 0件の場合の薄い青スタイル */
                .category-count-zero {{ 
                    float: right; 
                    background: linear-gradient(135deg, #b3d9ff, #87ceeb); 
                    color: white; 
                    padding: 4px 10px; 
                    border-radius: 12px; 
                    font-size: 0.8em; 
                    font-weight: 600;
                    box-shadow: 0 1px 4px rgba(135, 217, 255, 0.2);
                }}
                .action-buttons {{ padding: 30px; margin: 20px 0; text-align: center; }}
                .btn {{ 
                    background: linear-gradient(135deg, #6bb6ff 0%, #4a90e2 100%); 
                    color: white; 
                    padding: 12px 24px; 
                    border: none; 
                    border-radius: 25px; 
                    cursor: pointer; 
                    margin: 5px; 
                    text-decoration: none; 
                    display: inline-block; 
                    transition: all 0.3s;
                    border: 1px solid #e1f4fd;
                    box-shadow: 0 2px 8px rgba(74, 144, 226, 0.2);
                    font-weight: 500;
                    min-width: 300px;
                }}
                .btn:hover {{ 
                    transform: translateY(-1px); 
                    box-shadow: 0 4px 16px rgba(74, 144, 226, 0.3);
                }}
                .btn-success {{ 
                    background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);
                    color: #2d3436;
                    font-weight: 600;
                    box-shadow: 0 2px 8px rgba(253, 203, 110, 0.3);
                }}
                .btn-success:hover {{ 
                    box-shadow: 0 4px 16px rgba(253, 203, 110, 0.4);
                }}
                /* 完了済みボタン用の緑色スタイル */
                .btn-completed {{ 
                    background: linear-gradient(135deg, #81ecec 0%, #00cec9 100%);
                    color: white;
                    font-weight: 600;
                    box-shadow: 0 2px 8px rgba(0, 206, 201, 0.3);
                    opacity: 0.8;
                }}
                .btn-completed:hover {{ 
                    box-shadow: 0 4px 16px rgba(0, 206, 201, 0.4);
                    opacity: 1;
                }}
                .btn-slack {{ 
                    background: linear-gradient(135deg, #a29bfe 0%, #6c5ce7 100%);
                    color: white;
                    font-weight: 500;
                }}
                #process-btn {{
                    border-radius: 40px !important;
                    padding: 22px 48px !important;
                    font-size: 1.5em !important;
                    font-weight: 600 !important;
                    box-shadow: 0 4px 16px rgba(253, 203, 110, 0.25);
                }}
                #slack-test-btn {{
                    border-radius: 30px !important;
                    padding: 12px 24px !important;
                    font-size: 1em !important;
                    margin-top: 10px !important;
                }}
                .priority-high {{ border-left-color: #ff7675; }}
                .priority-medium {{ border-left-color: #fdcb6e; }}
                .priority-low {{ border-left-color: #81ecec; }}
                .clickable {{ cursor: pointer; }}
                
                /* 🎯 ローディングスピナー */
                .loading-spinner {{
                    display: inline-block;
                    width: 20px;
                    height: 20px;
                    border: 3px solid rgba(255, 255, 255, 0.3);
                    border-radius: 50%;
                    border-top-color: #fff;
                    animation: spin 1s ease-in-out infinite;
                    margin-right: 8px;
                }}
                
                .loading-spinner.large {{
                    width: 24px;
                    height: 24px;
                    border-width: 4px;
                }}
                
                @keyframes spin {{
                    to {{ transform: rotate(360deg); }}
                }}
                
                /* ボタンローディング状態 */
                .btn.loading {{
                    opacity: 0.8;
                    cursor: not-allowed;
                    position: relative;
                    min-width: 180px;
                }}
                
                .btn.loading:hover {{
                    transform: none !important;
                    box-shadow: none !important;
                }}
                
                /* パルス効果 */
                .processing-pulse {{
                    animation: pulse 2s ease-in-out infinite;
                }}
                
                @keyframes pulse {{
                    0% {{ opacity: 1; }}
                    50% {{ opacity: 0.7; }}
                    100% {{ opacity: 1; }}
                }}
                
                /* 🎨 統一されたコピーボタンスタイル */
                .copy-btn-unified {{
                    background: linear-gradient(135deg, #6bb6ff 0%, #4a90e2 100%);
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 25px;
                    cursor: pointer;
                    font-size: 0.9em;
                    font-weight: 500;
                    transition: all 0.3s ease;
                    border: 1px solid rgba(107, 182, 255, 0.2);
                    box-shadow: 0 2px 8px rgba(74, 144, 226, 0.15);
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    text-decoration: none;
                    user-select: none;
                }}
                .copy-btn-unified:hover {{
                    background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%);
                    transform: translateY(-1px);
                    box-shadow: 0 4px 16px rgba(74, 144, 226, 0.25);
                }}
                .copy-btn-unified.success {{
                    background: linear-gradient(135deg, #81ecec 0%, #00cec9 100%);
                    animation: successPulse 0.6s ease;
                }}
                .copy-btn-unified.small {{
                    padding: 6px 14px;
                    font-size: 0.8em;
                    border-radius: 18px;
                }}
                .copy-btn-unified .icon {{
                    font-size: 1em;
                    transition: transform 0.3s ease;
                }}
                .copy-btn-unified:hover .icon {{
                    transform: scale(1.1);
                }}
                @keyframes successPulse {{
                    0% {{ transform: scale(1); }}
                    50% {{ transform: scale(1.05); }}
                    100% {{ transform: scale(1); }}
                }}
                .copy-notification {{
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: linear-gradient(135deg, #81ecec 0%, #00cec9 100%);
                    color: white;
                    padding: 16px 24px;
                    border-radius: 12px;
                    box-shadow: 0 6px 24px rgba(0, 206, 201, 0.25);
                    z-index: 1000;
                    font-weight: 500;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    animation: slideInRight 0.4s ease, fadeOut 0.4s ease 2.6s forwards;
                }}
                @keyframes slideInRight {{
                    from {{ transform: translateX(400px); opacity: 0; }}
                    to {{ transform: translateX(0); opacity: 1; }}
                }}
                @keyframes fadeOut {{
                    from {{ opacity: 1; transform: translateX(0); }}
                    to {{ opacity: 0; transform: translateX(400px); }}
                }}
                
                /* 🤖 チャットボット関連スタイル */
                .chat-float-btn {{
                    position: fixed;
                    bottom: 30px;
                    right: 30px;
                    width: 60px;
                    height: 60px;
                    background: linear-gradient(135deg, #6bb6ff 0%, #4a90e2 100%);
                    border: none;
                    border-radius: 50%;
                    box-shadow: 0 4px 20px rgba(74, 144, 226, 0.3);
                    cursor: pointer;
                    z-index: 1000;
                    transition: all 0.3s ease;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 24px;
                }}
                .chat-float-btn:hover {{
                    transform: scale(1.1);
                    box-shadow: 0 6px 25px rgba(74, 144, 226, 0.4);
                }}
                .chat-popup {{
                    position: fixed;
                    bottom: 100px;
                    right: 30px;
                    width: 350px;
                    height: 500px;
                    background: rgba(255, 255, 255, 0.98);
                    border-radius: 20px;
                    box-shadow: 0 10px 40px rgba(52, 73, 94, 0.15);
                    border: 1px solid #e8f4fd;
                    z-index: 999;
                    display: none;
                    flex-direction: column;
                    overflow: hidden;
                    animation: slideInUp 0.3s ease;
                }}
                .chat-popup.open {{
                    display: flex;
                }}
                @keyframes slideInUp {{
                    from {{ opacity: 0; transform: translateY(20px); }}
                    to {{ opacity: 1; transform: translateY(0); }}
                }}
                .chat-header {{
                    background: linear-gradient(135deg, #6bb6ff 0%, #4a90e2 100%);
                    color: white;
                    padding: 15px 20px;
                    font-weight: 600;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .chat-close {{
                    background: none;
                    border: none;
                    color: white;
                    font-size: 20px;
                    cursor: pointer;
                    opacity: 0.8;
                    transition: opacity 0.3s;
                }}
                .chat-close:hover {{
                    opacity: 1;
                }}
                .chat-messages {{
                    flex: 1;
                    padding: 20px;
                    overflow-y: auto;
                    background: linear-gradient(135deg, #fdfcf5 0%, #f8f9fb 100%);
                }}
                .chat-message {{
                    margin-bottom: 15px;
                    animation: fadeInMessage 0.3s ease;
                }}
                @keyframes fadeInMessage {{
                    from {{ opacity: 0; transform: translateY(10px); }}
                    to {{ opacity: 1; transform: translateY(0); }}
                }}
                .chat-message.user {{
                    text-align: right;
                }}
                .chat-message.assistant {{
                    text-align: left;
                }}
                .chat-bubble {{
                    display: inline-block;
                    padding: 12px 16px;
                    border-radius: 18px;
                    max-width: 85%;
                    line-height: 1.4;
                    word-wrap: break-word;
                }}
                .chat-bubble.user {{
                    background: linear-gradient(135deg, #6bb6ff 0%, #4a90e2 100%);
                    color: white;
                }}
                .chat-bubble.assistant {{
                    background: rgba(255, 255, 255, 0.9);
                    color: #2c3e50;
                    border: 1px solid #e8f4fd;
                    box-shadow: 0 2px 8px rgba(52, 73, 94, 0.05);
                }}
                .chat-input-container {{
                    padding: 15px 20px;
                    background: rgba(255, 255, 255, 0.95);
                    border-top: 1px solid #e8f4fd;
                    display: flex;
                    gap: 10px;
                }}
                .chat-input {{
                    flex: 1;
                    padding: 12px 16px;
                    border: 2px solid #e8f4fd;
                    border-radius: 25px;
                    outline: none;
                    font-size: 14px;
                    transition: border-color 0.3s;
                }}
                .chat-input:focus {{
                    border-color: #4a90e2;
                }}
                .chat-send-btn {{
                    background: linear-gradient(135deg, #6bb6ff 0%, #4a90e2 100%);
                    color: white;
                    border: none;
                    border-radius: 50%;
                    width: 45px;
                    height: 45px;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 18px;
                    transition: all 0.3s ease;
                    box-shadow: 0 2px 8px rgba(74, 144, 226, 0.2);
                }}
                .chat-send-btn:hover {{
                    transform: scale(1.05);
                    box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
                }}
                .chat-send-btn:disabled {{
                    opacity: 0.6;
                    cursor: not-allowed;
                    transform: none;
                }}
                .chat-typing {{
                    display: none;
                    text-align: left;
                    margin-bottom: 15px;
                }}
                .chat-typing.show {{
                    display: block;
                }}
                .typing-bubble {{
                    display: inline-block;
                    padding: 12px 16px;
                    border-radius: 18px;
                    background: rgba(255, 255, 255, 0.9);
                    border: 1px solid #e8f4fd;
                    color: #7f8c8d;
                    font-style: italic;
                }}
                .typing-dots {{
                    display: inline-block;
                    animation: typingDots 1.5s infinite;
                }}
                @keyframes typingDots {{
                    0%, 60%, 100% {{ opacity: 0.4; }}
                    30% {{ opacity: 1; }}
                }}
            </style>
            <script>
                // 🎯 統一されたコピー機能
                class UnifiedCopyManager {{
                    async copyEmailDraft(emailId) {{
                        const textarea = document.querySelector(`#markdown-textarea-${{emailId}}`);
                        const button = event.target.closest('.copy-btn-unified');
                        
                        if (!textarea) {{
                            this._showNotification('草案が見つかりません', 'error');
                            return false;
                        }}

                        const text = textarea.value;
                        if (!text.trim()) {{
                            this._showNotification('コピーする内容がありません', 'warning');
                            return false;
                        }}

                        return await this.copyToClipboard(text, button, '📋 メール草案をコピーしました！');
                    }}

                    async copyToClipboard(text, button, successMessage = 'コピーしました！') {{
                        try {{
                            await this._performCopy(text);
                            this._showButtonSuccess(button);
                            this._showNotification(successMessage, 'success');
                            return true;
                        }} catch (error) {{
                            this._showNotification('コピーに失敗しました', 'error');
                            return false;
                        }}
                    }}

                    async _performCopy(text) {{
                        if (navigator.clipboard && navigator.clipboard.writeText) {{
                            await navigator.clipboard.writeText(text);
                            return;
                        }}
                        const tempTextarea = document.createElement('textarea');
                        tempTextarea.value = text;
                        tempTextarea.style.position = 'fixed';
                        tempTextarea.style.opacity = '0';
                        document.body.appendChild(tempTextarea);
                        tempTextarea.select();
                        const success = document.execCommand('copy');
                        document.body.removeChild(tempTextarea);
                        if (!success) throw new Error('Fallback copy failed');
                    }}

                    _showButtonSuccess(button) {{
                        if (!button) return;
                        const originalText = button.innerHTML;
                        button.classList.add('success');
                        button.innerHTML = '<span class="icon">✅</span><span>コピー完了</span>';
                        button.disabled = true;
                        setTimeout(() => {{
                            button.classList.remove('success');
                            button.innerHTML = originalText;
                            button.disabled = false;
                        }}, 2000);
                    }}

                    _showNotification(message, type = 'success') {{
                        const existingNotification = document.querySelector('.copy-notification');
                        if (existingNotification) existingNotification.remove();

                        const notification = document.createElement('div');
                        notification.className = 'copy-notification';
                        const icons = {{ success: '✅', error: '❌', warning: '⚠️' }};
                        notification.innerHTML = `<span class="icon">${{icons[type] || icons.success}}</span><span>${{message}}</span>`;
                        
                        if (type === 'error') {{
                            notification.style.background = 'linear-gradient(135deg, #f44336 0%, #e57373 100%)';
                        }} else if (type === 'warning') {{
                            notification.style.background = 'linear-gradient(135deg, #ff9800 0%, #ffb74d 100%)';
                        }}

                        document.body.appendChild(notification);
                        setTimeout(() => {{ if (notification.parentNode) notification.remove(); }}, 3000);
                    }}
                }}

                const copyManager = new UnifiedCopyManager();
                
                // グローバル関数
                async function copyEmailDraft(emailId) {{
                    return await copyManager.copyEmailDraft(emailId);
                }}
                
                async function processEmails() {{
                    const button = document.getElementById('process-btn');
                    
                    // ローディング状態開始
                    setButtonLoading(button, '✉️分析中...', true);
                    
                    try {{
                        const response = await fetch('/process', {{ method: 'POST' }});
                        const result = await response.json();
                        
                        if (result.success) {{
                            // 成功状態表示
                            setButtonLoading(button, '✅ 処理完了！', false);
                            
                            let message = `メール処理完了！\\n`;
                            
                            // 基本統計
                            message += `📧 処理総数: ${{result.processed_count}}件\\n`;
                            if (result.new_emails_count > 0) {{
                                message += `🆕 新規メール: ${{result.new_emails_count}}件\\n`;
                            }}
                            if (result.updated_emails_count > 0) {{
                                message += `🔄 更新メール: ${{result.updated_emails_count}}件\\n`;
                            }}
                            
                            // ステータス保持情報
                            if (result.completed_preserved_count > 0) {{
                                message += `✅ 完了ステータス保持: ${{result.completed_preserved_count}}件\\n`;
                            }}
                            
                            // 未対応メール
                            if (result.pending_count) {{
                                message += `📋 未対応メール: ${{result.pending_count}}件\\n`;
                            }}
                            
                            // Slack通知
                            if (result.slack_notification_sent) {{
                                message += `📤 Slack通知も送信しました！`;
                            }}
                            
                            setTimeout(() => {{
                                alert(message);
                                location.reload();
                            }}, 800); // 成功状態を少し見せてからアラート
                        }} else {{
                            setButtonLoading(button, '❌ エラー', false);
                            setTimeout(() => {{
                                alert('エラー: ' + result.error);
                                resetButton(button, '📬 今すぐ処理');
                            }}, 800);
                        }}
                    }} catch (error) {{
                        setButtonLoading(button, '❌ エラー', false);
                        setTimeout(() => {{
                            alert('エラーが発生しました: ' + error.message);
                            resetButton(button, '📬 今すぐ処理');
                        }}, 800);
                    }}
                }}
                
                async function testSlackNotification() {{
                    const button = document.getElementById('slack-test-btn');
                    
                    // ローディング状態開始
                    setButtonLoading(button, '📤 送信中...', false);
                    
                    try {{
                        const response = await fetch('/slack/test', {{ method: 'POST' }});
                        const result = await response.json();
                        
                        if (result.success) {{
                            setButtonLoading(button, '✅ 送信完了！', false);
                            setTimeout(() => {{
                                alert('✅ Slackテスト通知を送信しました！\\nSlackチャンネルを確認してください。');
                                resetButton(button, '📤 Slack テスト');
                            }}, 800);
                        }} else {{
                            setButtonLoading(button, '❌ 失敗', false);
                            setTimeout(() => {{
                                alert('❌ Slack通知送信失敗: ' + (result.error || result.message));
                                resetButton(button, '📤 Slack テスト');
                            }}, 800);
                        }}
                    }} catch (error) {{
                        setButtonLoading(button, '❌ エラー', false);
                        setTimeout(() => {{
                            alert('エラーが発生しました: ' + error.message);
                            resetButton(button, '📤 Slack テスト');
                        }}, 800);
                    }}
                }}
                
                // ボタンローディング状態制御関数
                function setButtonLoading(button, text, useSpinner = true) {{
                    button.disabled = true;
                    button.classList.add('loading');
                    
                    if (useSpinner) {{
                        button.innerHTML = `<span class="loading-spinner"></span>${{text}}`;
                    }} else {{
                        button.innerHTML = text;
                        button.classList.add('processing-pulse');
                    }}
                }}
                
                function resetButton(button, originalText) {{
                    button.disabled = false;
                    button.classList.remove('loading', 'processing-pulse');
                    button.innerHTML = originalText;
                }}
                
                async function showSlackDebug() {{
                    try {{
                        const response = await fetch('/debug/slack');
                        const result = await response.json();
                        
                        let debugMessage = '🔍 Slack設定デバッグ情報:\\n\\n';
                        debugMessage += `Slack通知有効: ${{result.debug_info.enabled}}\\n`;
                        debugMessage += `Webhook URL設定: ${{result.debug_info.has_webhook_url}}\\n`;
                        debugMessage += `Bot Token設定: ${{result.debug_info.has_bot_token}}\\n`;
                        debugMessage += `チャンネル設定: ${{result.debug_info.channel}}\\n`;
                        
                        if (result.debug_info.available_channels) {{
                            debugMessage += '\\n📋 利用可能チャンネル:\\n';
                            result.debug_info.available_channels.slice(0, 5).forEach(ch => {{
                                debugMessage += `  - ${{ch.name}} (ID: ${{ch.id}})\\n`;
                            }});
                        }}
                        
                        if (result.debug_info.target_channel_found !== undefined) {{
                            debugMessage += `\\n🎯 指定チャンネル存在: ${{result.debug_info.target_channel_found}}\\n`;
                            if (result.debug_info.target_channel_info) {{
                                debugMessage += `   名前: ${{result.debug_info.target_channel_info.name}}\\n`;
                                debugMessage += `   ID: ${{result.debug_info.target_channel_info.id}}\\n`;
                            }}
                        }}
                        
                        if (result.debug_info.channels_error) {{
                            debugMessage += `\\n❌ チャンネル取得エラー: ${{result.debug_info.channels_error}}\\n`;
                        }}
                        
                        alert(debugMessage);
                    }} catch (error) {{
                        alert('デバッグ情報取得エラー: ' + error.message);
                    }}
                }}
                
                async function showPreservationTest() {{
                    try {{
                        const response = await fetch('/debug/email-preservation-test');
                        const result = await response.json();
                        
                        let testMessage = '🧪 メール状態保持テスト結果:\\n\\n';
                        
                        // 完了済みメール
                        testMessage += `✅ 完了済みメール: ${{result.preservation_test.completed_count}}件\\n`;
                        if (result.completed_emails.length > 0) {{
                            testMessage += '\\n最近完了したメール（最大5件）:\\n';
                            result.completed_emails.forEach((email, index) => {{
                                testMessage += `   ${{index + 1}}. ${{email.subject}}\\n`;
                                testMessage += `      完了日時: ${{email.completed_at ? email.completed_at.slice(0,16) : 'N/A'}}\\n`;
                            }});
                        }}
                        
                        // 重複チェック
                        testMessage += `\\n🔍 重複メール検出: ${{result.preservation_test.has_duplicates ? 'あり' : 'なし'}}\\n`;
                        if (result.duplicate_emails.length > 0) {{
                            testMessage += '重複メール一覧:\\n';
                            result.duplicate_emails.forEach(dup => {{
                                testMessage += `   ID: ${{dup.id}} (重複数: ${{dup.count}})\\n`;
                            }});
                        }}
                        
                        // 最近の処理
                        testMessage += `\\n📧 最近処理されたメール（最大5件）:\\n`;
                        result.recent_processed.slice(0, 5).forEach((email, index) => {{
                            const statusEmoji = email.status === 'pending' ? '📋' : '✅';
                            testMessage += `   ${{index + 1}}. ${{statusEmoji}} ${{email.subject}}\\n`;
                            testMessage += `      ID: ${{email.id}}\\n`;
                        }});
                        
                        // 問題の診断
                        testMessage += '\\n🔬 診断結果:\\n';
                        if (result.preservation_test.has_duplicates) {{
                            testMessage += '⚠️  重複メールが検出されました。メールIDの一意性に問題がある可能性があります。\\n';
                        }} else {{
                            testMessage += '✅ メールIDは一意です。\\n';
                        }}
                        
                        if (result.preservation_test.completed_count > 0) {{
                            testMessage += '✅ 完了済みメールが存在します。\\n';
                            testMessage += '   次回の「実行」ボタンクリック時に、これらのメールが未対応に戻らないかテストしてください。\\n';
                        }} else {{
                            testMessage += '📝 完了済みメールがありません。\\n';
                            testMessage += '   テストするには、まずメールを完了マークしてください。\\n';
                        }}
                        
                        alert(testMessage);
                    }} catch (error) {{
                        alert('状態保持テストエラー: ' + error.message);
                    }}
                }}
                
                async function showEmailStatus() {{
                    try {{
                        const response = await fetch('/debug/email-status');
                        const result = await response.json();
                        
                        let statusMessage = '📊 メール状態統計:\\n\\n';
                        
                        // ステータス分布
                        statusMessage += '📈 ステータス分布:\\n';
                        for (const [status, count] of Object.entries(result.status_distribution)) {{
                            const statusEmoji = status === 'pending' ? '📋' : status === 'completed' ? '✅' : '❓';
                            statusMessage += `   ${{statusEmoji}} ${{status}}: ${{count}}件\\n`;
                        }}
                        
                        // 完了済み統計
                        if (result.completed_statistics.total_completed > 0) {{
                            statusMessage += `\\n✅ 完了済み統計:\\n`;
                            statusMessage += `   総件数: ${{result.completed_statistics.total_completed}}件\\n`;
                            if (result.completed_statistics.first_completed) {{
                                statusMessage += `   最初の完了: ${{result.completed_statistics.first_completed.slice(0,16)}}\\n`;
                            }}
                            if (result.completed_statistics.last_completed) {{
                                statusMessage += `   最新の完了: ${{result.completed_statistics.last_completed.slice(0,16)}}\\n`;
                            }}
                        }}
                        
                        // 最近のメール
                        statusMessage += `\\n📧 最近の処理メール（上位5件）:\\n`;
                        result.recent_emails.slice(0, 5).forEach((email, index) => {{
                            const statusEmoji = email.status === 'pending' ? '📋' : '✅';
                            statusMessage += `   ${{index + 1}}. ${{statusEmoji}} ${{email.subject}}\\n`;
                        }});
                        
                        alert(statusMessage);
                    }} catch (error) {{
                        alert('メール状態確認エラー: ' + error.message);
                    }}
                }}
                
                function viewCategory(category) {{
                    window.location.href = `/category/${{encodeURIComponent(category)}}`;
                }}

                // 🤖 チャットボット機能
                class ProfessorChatBot {{
                    constructor() {{
                        this.isOpen = false;
                        this.messages = [];
                        this.init();
                    }}
                    
                    init() {{
                        // 初回メッセージ
                        this.messages = [{{
                            type: 'assistant',
                            content: '🎓 こんにちは！ProfMail AIアシスタントです。\\n\\n今日のメール状況を確認したり、特定のメールを検索したりできます。\\n\\n例：「今日やるべきことは？」「高優先度のメールを見せて」「論文査読のメールは？」',
                            timestamp: new Date()
                        }}];
                    }}
                    
                    toggle() {{
                        const popup = document.getElementById('chat-popup');
                        if (this.isOpen) {{
                            popup.classList.remove('open');
                            this.isOpen = false;
                        }} else {{
                            popup.classList.add('open');
                            this.isOpen = true;
                            this.renderMessages();
                            document.getElementById('chat-input').focus();
                        }}
                    }}
                    
                    async sendMessage() {{
                        const input = document.getElementById('chat-input');
                        const message = input.value.trim();
                        
                        if (!message) return;
                        
                        // ユーザーメッセージを追加
                        this.messages.push({{
                            type: 'user',
                            content: message,
                            timestamp: new Date()
                        }});
                        
                        input.value = '';
                        this.renderMessages();
                        this.showTyping();
                        
                        try {{
                            // APIにメッセージ送信
                            const response = await fetch('/chat', {{
                                method: 'POST',
                                headers: {{ 'Content-Type': 'application/json' }},
                                body: JSON.stringify({{ message: message }})
                            }});
                            
                            const result = await response.json();
                            
                            this.hideTyping();
                            
                            if (result.success) {{
                                this.messages.push({{
                                    type: 'assistant',
                                    content: result.response,
                                    timestamp: new Date()
                                }});
                            }} else {{
                                this.messages.push({{
                                    type: 'assistant',
                                    content: '申し訳ございません。エラーが発生しました。',
                                    timestamp: new Date()
                                }});
                            }}
                            
                            this.renderMessages();
                            
                        }} catch (error) {{
                            this.hideTyping();
                            this.messages.push({{
                                type: 'assistant',
                                content: 'ネットワークエラーが発生しました。しばらく後で再試行してください。',
                                timestamp: new Date()
                            }});
                            this.renderMessages();
                        }}
                    }}
                    
                    renderMessages() {{
                        const container = document.getElementById('chat-messages');
                        container.innerHTML = '';
                        
                        this.messages.forEach(msg => {{
                            const messageDiv = document.createElement('div');
                            messageDiv.className = `chat-message ${{msg.type}}`;
                            
                            const bubbleDiv = document.createElement('div');
                            bubbleDiv.className = `chat-bubble ${{msg.type}}`;
                            bubbleDiv.innerHTML = msg.content.replace(/\\n/g, '<br>');
                            
                            messageDiv.appendChild(bubbleDiv);
                            container.appendChild(messageDiv);
                        }});
                        
                        // 最新メッセージまでスクロール
                        container.scrollTop = container.scrollHeight;
                    }}
                    
                    showTyping() {{
                        document.getElementById('chat-typing').classList.add('show');
                        const container = document.getElementById('chat-messages');
                        container.scrollTop = container.scrollHeight;
                    }}
                    
                    hideTyping() {{
                        document.getElementById('chat-typing').classList.remove('show');
                    }}
                    
                    handleKeyPress(event) {{
                        if (event.key === 'Enter' && !event.shiftKey) {{
                            event.preventDefault();
                            this.sendMessage();
                        }}
                    }}
                }}
                
                // グローバルチャットボットインスタンス
                let chatBot;
                
                // ページ読み込み時にチャットボット初期化
                document.addEventListener('DOMContentLoaded', function() {{
                    chatBot = new ProfessorChatBot();
                }});
                
                // グローバル関数
                function toggleChat() {{
                    if (chatBot) chatBot.toggle();
                }}
                
                function sendChatMessage() {{
                    if (chatBot) chatBot.sendMessage();
                }}
                
                function handleChatKeyPress(event) {{
                    if (chatBot) chatBot.handleKeyPress(event);
                }}
            </script>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎓 ProfMail</h1>
                    <p>AI powered email management for academics with Slack integration</p>
                    <p><small>定期実行 {SCHEDULER_HOUR}:{SCHEDULER_MINUTE}</small></p>
                </div>
                
                <div class="dashboard">
                    <div class="sidebar">
                        <h3 style="color: #1976d2;">概要</h3>
                        <div class="stats-grid">
                            <a href="/all" class="stat-box clickable">
                                <div class="stat-number">{stats.get('pending_emails', 0)}</div>
                                <div class="stat-label">未対応</div>
                            </a>
                            <a href="/completed" class="stat-box clickable btn-completed">
                                <div class="stat-number">{stats.get('completed_emails', 0)}</div>
                                <div class="stat-label">完了済み</div>
                            </a>
                        </div>
                        
                        <div class="action-buttons">
                            <button id="process-btn" class="btn btn-success" onclick="processEmails()">実行</button>
                        </div>

                        <h3 style="color: #1976d2;">優先度別</h3>
                        <div style="display: flex; justify-content: space-around; margin: 50px 0;">
                            <a href="/priority/high" style="text-decoration: none; color: inherit;">
                                <div style="text-align: center; padding: 30px; border-radius: 12px; transition: all 0.3s; cursor: pointer; background: #fef5f5; border: 1px solid #ff7675;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                                    <div style="font-size: 2em; color: #ff7675; font-weight: bold;">{stats.get('priority_stats', {}).get('高', 0)}</div>
                                    <div style="color: #ff7675; font-weight: bold;">高</div>
                                </div>
                            </a>
                            <a href="/priority/medium" style="text-decoration: none; color: inherit;">
                                <div style="text-align: center; padding: 30px; border-radius: 12px; transition: all 0.3s; cursor: pointer; background: #fffef7; border: 1px solid #fdcb6e;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                                    <div style="font-size: 2em; color: #fdcb6e; font-weight: bold;">{stats.get('priority_stats', {}).get('中', 0)}</div>
                                    <div style="color: #fdcb6e; font-weight: bold;">中</div>
                                </div>
                            </a>
                            <a href="/priority/low" style="text-decoration: none; color: inherit;">
                                <div style="text-align: center; padding: 30px; border-radius: 12px; transition: all 0.3s; cursor: pointer; background: #f0fffe; border: 1px solid #81ecec;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                                    <div style="font-size: 2em; color: #81ecec; font-weight: bold;">{stats.get('priority_stats', {}).get('低', 0)}</div>
                                    <div style="color: #81ecec; font-weight: bold;">低</div>
                                </div>
                            </a>
                        </div>
                    </div>
                    
                    <div class="main-content">
                        <h3 style="color: #1976d2;">カテゴリ別メール</h3>
                        <ul class="category-list">
                            {generate_category_list(EMAIL_CATEGORIES, stats)}
                        </ul>
                    </div>
                </div>
            </div>
            
            <!-- 🤖 チャットボット -->
            <button class="chat-float-btn" onclick="toggleChat()">💬</button>
            <div id="chat-popup" class="chat-popup">
                <div class="chat-header">
                    <span>🎓 ProfMail AI アシスタント</span>
                    <button class="chat-close" onclick="toggleChat()">×</button>
                </div>
                <div id="chat-messages" class="chat-messages"></div>
                <div id="chat-typing" class="chat-typing">
                    <div class="typing-bubble">
                        <span class="typing-dots">入力中...</span>
                    </div>
                </div>
                <div class="chat-input-container">
                    <input 
                        type="text" 
                        id="chat-input" 
                        class="chat-input" 
                        placeholder="メッセージを入力..."
                        onkeypress="handleChatKeyPress(event)"
                    >
                    <button class="chat-send-btn" onclick="sendChatMessage()">📤</button>
                </div>
            </div>
        </body>
        </html>
        """
        return html_content
    
    @app.get("/priority/{priority_level}", response_class=HTMLResponse)
    async def priority_view(priority_level: str):
        """優先度別メール表示"""
        priority_map = {"high": "高", "medium": "中", "low": "低"}
        priority_jp = priority_map.get(priority_level, priority_level)
        
        emails = email_processor.get_database().get_emails_by_priority(priority_jp, status='pending', limit=30)
        
        html_content = _get_priority_html_template(priority_level, priority_jp, emails)
        return html_content
    
    @app.get("/completed", response_class=HTMLResponse)
    async def completed_emails():
        """完了済みメール表示"""
        emails = email_processor.get_database().get_emails_by_category(status='completed', limit=50)
        
        html_content = _get_completed_html_template(emails)
        return html_content
    
    @app.get("/category/{category_name}", response_class=HTMLResponse)
    async def category_view(category_name: str):
        """カテゴリ別メール表示"""
        pending_emails = email_processor.get_database().get_emails_by_category(category_name, status='pending', limit=20)
        completed_emails = email_processor.get_database().get_emails_by_category(category_name, status='completed', limit=10)
        
        html_content = _get_category_html_template(category_name, pending_emails, completed_emails)
        return html_content
    
    @app.get("/all", response_class=HTMLResponse)
    async def all_emails():
        """すべてのメール表示"""
        emails = email_processor.get_database().get_emails_by_category(status='pending', limit=50)
        
        html_content = _get_all_emails_html_template(emails)
        return html_content
    
    @app.post("/process")
    async def process_emails(days: int = 3):
        """メール処理実行（Slack通知付き）"""
        result = email_processor.run_manual_processing_with_notification(days=days)
        return result
    
    @app.post("/slack/test")
    async def test_slack_notification():
        """Slack通知テスト"""
        try:
            success = email_processor.send_test_slack_notification()
            return {
                "success": success,
                "message": "テスト通知を送信しました" if success else "通知送信に失敗しました",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    @app.post("/emails/{email_id}/complete")
    async def mark_email_completed(email_id: str):
        """メール完了マーク"""
        try:
            success = email_processor.get_database().update_email_status(email_id, 'completed')
            return {"success": success}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.delete("/emails/{email_id}/delete")
    async def delete_email(email_id: str):
        """メール削除"""
        try:
            success = email_processor.get_database().delete_email(email_id)
            return {"success": success}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.post("/chat")
    async def chat_with_assistant(request: dict):
        """教授向けAIアシスタントチャット"""
        try:
            user_message = request.get("message", "")
            
            # チャット機能を使用
            response = email_processor.get_openai_service().chat_with_professor_assistant(
                user_message, 
                email_processor.get_database()
            )
            
            return {
                "success": True,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    @app.get("/debug/slack")
    async def debug_slack():
        """Slack設定デバッグ情報"""
        try:
            debug_info = email_processor.get_slack_debug_info()
            return {
                "message": "Slack設定デバッグ情報",
                "debug_info": debug_info,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}
    
    @app.get("/debug/email-preservation-test")
    async def debug_email_preservation():
        """デバッグ: メール状態保持のテスト"""
        try:
            conn = sqlite3.connect(email_processor.get_database().db_path)
            cursor = conn.cursor()
            
            # 完了済みメールの詳細情報
            cursor.execute('''
                SELECT id, subject, status, completed_at, processed_at
                FROM emails 
                WHERE status = 'completed'
                ORDER BY completed_at DESC
                LIMIT 5
            ''')
            completed_emails = []
            for row in cursor.fetchall():
                completed_emails.append({
                    "id": row[0],
                    "subject": row[1][:50] + "..." if len(row[1]) > 50 else row[1],
                    "status": row[2],
                    "completed_at": row[3],
                    "processed_at": row[4]
                })
            
            # 重複メールの検出
            cursor.execute('''
                SELECT id, COUNT(*) as count
                FROM emails 
                GROUP BY id
                HAVING COUNT(*) > 1
            ''')
            duplicate_emails = [{"id": row[0], "count": row[1]} for row in cursor.fetchall()]
            
            # 最近処理されたメールのID一覧
            cursor.execute('''
                SELECT id, subject, status, processed_at
                FROM emails 
                ORDER BY processed_at DESC
                LIMIT 10
            ''')
            recent_processed = []
            for row in cursor.fetchall():
                recent_processed.append({
                    "id": row[0],
                    "subject": row[1][:30] + "..." if len(row[1]) > 30 else row[1],
                    "status": row[2],
                    "processed_at": row[3]
                })
            
            conn.close()
            
            return {
                "message": "メール状態保持テスト結果",
                "completed_emails": completed_emails,
                "duplicate_emails": duplicate_emails,
                "recent_processed": recent_processed,
                "preservation_test": {
                    "completed_count": len(completed_emails),
                    "duplicate_count": len(duplicate_emails),
                    "has_duplicates": len(duplicate_emails) > 0
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}
    
    @app.get("/debug/email-status")
    async def debug_email_status():
        """デバッグ: メールステータス分布"""
        try:
            conn = sqlite3.connect(email_processor.get_database().db_path)
            cursor = conn.cursor()
            
            # ステータス別集計
            cursor.execute('''
                SELECT status, COUNT(*) as count
                FROM emails 
                GROUP BY status
            ''')
            status_counts = dict(cursor.fetchall())
            
            # 最近の処理メール（上位10件）
            cursor.execute('''
                SELECT subject, status, processed_at, completed_at
                FROM emails 
                ORDER BY processed_at DESC 
                LIMIT 10
            ''')
            recent_emails = []
            for row in cursor.fetchall():
                recent_emails.append({
                    "subject": row[0][:50] + "..." if len(row[0]) > 50 else row[0],
                    "status": row[1],
                    "processed_at": row[2],
                    "completed_at": row[3]
                })
            
            # 完了済みメールの統計
            cursor.execute('''
                SELECT COUNT(*) as completed_count,
                       MIN(completed_at) as first_completed,
                       MAX(completed_at) as last_completed
                FROM emails 
                WHERE status = 'completed'
            ''')
            completed_stats = cursor.fetchone()
            
            conn.close()
            
            return {
                "message": "メールステータス分布",
                "status_distribution": status_counts,
                "recent_emails": recent_emails,
                "completed_statistics": {
                    "total_completed": completed_stats[0] if completed_stats else 0,
                    "first_completed": completed_stats[1] if completed_stats else None,
                    "last_completed": completed_stats[2] if completed_stats else None
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}
    
    @app.get("/debug/emails")
    async def debug_emails():
        """デバッグ: 実際に取得されるメール一覧"""
        try:
            emails = email_processor.gmail_service.get_recent_emails(days=7, max_emails=10)
            
            email_list = []
            for email in emails:
                email_list.append({
                    "subject": email['subject'],
                    "sender": email['sender'],
                    "date": email['date'],
                    "body_preview": email['body'][:200] + "..." if len(email['body']) > 200 else email['body']
                })
            
            return {
                "message": "直近7日間で取得されるメール一覧",
                "count": len(emails),
                "emails": email_list
            }
        except Exception as e:
            return {"error": str(e)}
    
    @app.get("/debug/db")
    async def debug_database():
        """データベース構造デバッグ"""
        try:
            conn = sqlite3.connect(email_processor.get_database().db_path)
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA table_info(emails)")
            table_info = cursor.fetchall()
            
            cursor.execute("SELECT * FROM emails LIMIT 1")
            sample_data = cursor.fetchone()
            
            conn.close()
            
            return {
                "table_structure": table_info,
                "sample_data": sample_data,
                "db_path": email_processor.get_database().db_path
            }
        except Exception as e:
            return {"error": str(e)}
    
    @app.get("/health")
    async def health_check():
        """ヘルスチェック"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "3.4.0 - Enhanced UX Edition"
        }

def _get_common_styles():
    """共通CSSスタイル"""
    return """
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 45px; 
            background: linear-gradient(135deg, #fdfcf5 0%, #f8f9fb 100%); 
            min-height: 100vh; 
            color: #2c3e50;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { 
            color: #34495e; 
            margin-bottom: 30px; 
            background: rgba(255, 255, 255, 0.9);
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 20px rgba(52, 73, 94, 0.08);
            border: 1px solid #e8f4fd;
            position: relative;
        }
        .header.dashboard {
            text-align: center;
        }
        .header.page-header {
            display: flex;
            align-items: center;
            gap: 15px;
            text-align: left;
        }
        .header h1 { 
            font-size: 2.5em; 
            margin-bottom: 10px; 
            background: linear-gradient(45deg, #4a90e2, #6bb6ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .header h2 { 
            color: #4a90e2; 
            margin-bottom: 10px;
        }
        .back-btn { 
            background: linear-gradient(135deg, #6bb6ff 0%, #4a90e2 100%); 
            color: white; 
            padding: 12px 16px; 
            border: none; 
            border-radius: 50%; 
            text-decoration: none; 
            margin-right: 15px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(74, 144, 226, 0.2);
            font-weight: 500;
            font-size: 1.2em;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 33px;
            height: 33px;
        }
        .back-btn:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 4px 16px rgba(74, 144, 226, 0.3);
        }
        .email-card { 
            background: rgba(255, 255, 255, 0.95); 
            margin: 20px 0; 
            border-radius: 15px; 
            box-shadow: 0 4px 20px rgba(52, 73, 94, 0.06); 
            overflow: hidden;
            border: 1px solid #e8f4fd;
            transition: all 0.3s ease;
        }
        .email-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(52, 73, 94, 0.1);
        }
        .email-header { 
            padding: 25px; 
            border-left: 4px solid #6bb6ff; 
        }
        .email-subject { 
            font-size: 1.3em; 
            font-weight: bold; 
            margin-bottom: 12px; 
            color: #4a90e2; 
        }
        .email-meta { 
            color: #7f8c8d; 
            font-size: 0.95em; 
            margin-bottom: 15px; 
            line-height: 1.6;
        }
        .email-summary { 
            color: #34495e; 
            margin-bottom: 20px; 
            padding: 15px; 
            background: linear-gradient(135deg, #f8f9fb 0%, #e8f4fd 100%); 
            border-radius: 10px;
            border: 1px solid #e8f4fd;
        }
        .email-actions { 
            padding: 0 25px 25px 25px; 
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .btn { 
            background: linear-gradient(135deg, #6bb6ff 0%, #4a90e2 100%); 
            color: white; 
            padding: 12px 20px; 
            border: none; 
            border-radius: 25px; 
            cursor: pointer; 
            text-decoration: none; 
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(74, 144, 226, 0.2);
            font-weight: 500;
            font-size: 0.9em;
        }
        .btn:hover { 
            transform: translateY(-1px); 
            box-shadow: 0 4px 16px rgba(74, 144, 226, 0.3);
        }
        .btn-primary { 
            background: linear-gradient(135deg, #6bb6ff 0%, #4a90e2 100%); 
        }
        .btn-success { 
            background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);
            color: #2d3436;
            box-shadow: 0 2px 8px rgba(253, 203, 110, 0.3);
        }
        .btn-success:hover { 
            box-shadow: 0 4px 16px rgba(253, 203, 110, 0.4);
        }
        .btn-danger { 
            background: linear-gradient(135deg, #ff7675 0%, #e17055 100%);
            box-shadow: 0 2px 8px rgba(255, 118, 117, 0.3);
        }
        .btn-danger:hover { 
            box-shadow: 0 4px 16px rgba(255, 118, 117, 0.4);
        }
        .btn-completed { 
            background: linear-gradient(135deg, #81ecec 0%, #00cec9 100%);
            box-shadow: 0 2px 8px rgba(0, 206, 201, 0.3);
        }
        .btn-completed:hover { 
            box-shadow: 0 4px 16px rgba(0, 206, 201, 0.4);
        }
        .priority-high { border-left-color: #ff7675 !important; }
        .priority-medium { border-left-color: #fdcb6e !important; }
        .priority-low { border-left-color: #81ecec !important; }
        .urgency-score { 
            background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%); 
            color: white; 
            padding: 6px 12px; 
            border-radius: 15px; 
            font-size: 0.8em; 
            font-weight: 600;
            box-shadow: 0 1px 4px rgba(253, 203, 110, 0.3);
        }
        .reply-preview { 
            background: linear-gradient(135deg, #fff8e1 0%, #fff3c4 100%); 
            padding: 20px; 
            margin: 15px 0; 
            border-radius: 12px; 
            border-left: 4px solid #fdcb6e;
            border: 1px solid #ffe082;
        }
        .reply-preview h5 { 
            margin: 0 0 15px 0; 
            color: #f57c00; 
            font-size: 1.1em;
        }
        .reply-tabs { margin-bottom: 15px; display: flex; gap: 8px; }
        .tab-btn { 
            padding: 8px 16px; 
            border: 2px solid #fdcb6e; 
            background: white; 
            cursor: pointer; 
            border-radius: 20px;
            transition: all 0.3s ease;
            font-size: 0.9em;
            font-weight: 500;
        }
        .tab-btn.active { 
            background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%); 
            color: white; 
        }
        .tab-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(253, 203, 110, 0.3);
        }
        .reply-content { display: none; }
        .reply-content.active { display: block; }
        .reply-text { 
            color: #495057; 
            line-height: 1.7;
            font-size: 0.95em;
        }
        .markdown-text { 
            width: 100%; 
            height: 220px; 
            border: 2px solid #e8f4fd; 
            border-radius: 12px; 
            padding: 15px; 
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace; 
            resize: vertical; 
            font-size: 14px;
            line-height: 1.6;
            background: #fafbfc;
        }
        .markdown-text:focus { 
            border-color: #4a90e2; 
            outline: none;
            box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
        }
        
        /* 🎨 統一されたコピーボタンスタイル */
        .copy-btn-unified {
            background: linear-gradient(135deg, #6bb6ff 0%, #4a90e2 100%);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 0.9em;
            font-weight: 500;
            transition: all 0.3s ease;
            border: 1px solid rgba(107, 182, 255, 0.2);
            box-shadow: 0 2px 8px rgba(74, 144, 226, 0.15);
            display: inline-flex;
            align-items: center;
            gap: 8px;
            text-decoration: none;
            user-select: none;
        }
        .copy-btn-unified:hover {
            background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%);
            transform: translateY(-1px);
            box-shadow: 0 4px 16px rgba(74, 144, 226, 0.25);
        }
        .copy-btn-unified.success {
            background: linear-gradient(135deg, #81ecec 0%, #00cec9 100%);
            animation: successPulse 0.6s ease;
        }
        .copy-btn-unified.small {
            padding: 6px 14px;
            font-size: 0.8em;
            border-radius: 18px;
        }
        .copy-btn-unified .icon {
            font-size: 1em;
            transition: transform 0.3s ease;
        }
        .copy-btn-unified:hover .icon {
            transform: scale(1.1);
        }
        @keyframes successPulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        .copy-notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #81ecec 0%, #00cec9 100%);
            color: white;
            padding: 16px 24px;
            border-radius: 12px;
            box-shadow: 0 6px 24px rgba(0, 206, 201, 0.25);
            z-index: 1000;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 10px;
            animation: slideInRight 0.4s ease, fadeOut 0.4s ease 2.6s forwards;
        }
        @keyframes slideInRight {
            from { transform: translateX(400px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes fadeOut {
            from { opacity: 1; transform: translateX(0); }
            to { opacity: 0; transform: translateX(400px); }
        }
        
        /* テーブルスタイル - 固定レイアウト */
        .email-table { 
            background: rgba(255, 255, 255, 0.95); 
            border-radius: 15px; 
            overflow: hidden; 
            box-shadow: 0 4px 20px rgba(52, 73, 94, 0.06);
            border: 1px solid #e8f4fd;
        }
        .email-table table { 
            width: 100%; 
            border-collapse: collapse;
            table-layout: fixed; /* 固定レイアウト */
        }
        .email-table th { 
            background: linear-gradient(135deg, #6bb6ff 0%, #4a90e2 100%); 
            color: white; 
            padding: 18px; 
            text-align: left; 
            font-weight: 600;
        }
        .email-table td { 
            padding: 18px; 
            border-bottom: 1px solid #e8f4fd; 
            vertical-align: top;
            word-wrap: break-word;
            overflow: hidden;
        }
        .email-table tr:hover { background: linear-gradient(135deg, #f8f9fb 0%, #e8f4fd 50%); }
        
        /* 列幅の固定設定 */
        .email-table th:nth-child(1),
        .email-table td:nth-child(1) { width: 40%; } /* 件名 */
        .email-table th:nth-child(2),
        .email-table td:nth-child(2) { width: 20%; } /* 送信者 */
        .email-table th:nth-child(3),
        .email-table td:nth-child(3) { width: 12%; } /* カテゴリ */
        .email-table th:nth-child(4),
        .email-table td:nth-child(4) { width: 8%; }  /* 優先度 */
        .email-table th:nth-child(5),
        .email-table td:nth-child(5) { width: 8%; }  /* 緊急度 */
        .email-table th:nth-child(6),
        .email-table td:nth-child(6) { width: 12%; } /* アクション */
        
        /* 長いテキストの省略表示 */
        .email-table .subject-cell {
            display: block;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .email-table .subject-preview {
            display: block;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            font-size: 0.85em;
            color: #7f8c8d;
            margin-top: 4px;
        }
        .email-table .sender-cell {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        /* テーブル内のボタンスタイル */
        .email-table .btn {
            padding: 6px 12px;
            font-size: 0.8em;
            margin: 2px;
            min-width: auto;
        }
        
        .completed-item { 
            background: linear-gradient(135deg, #f0fffe 0%, #e8f5e8 100%); 
            opacity: 0.8; 
        }
        .category-badge { 
            background: linear-gradient(135deg, #6bb6ff 0%, #4a90e2 100%); 
            color: white; 
            padding: 4px 12px; 
            border-radius: 15px; 
            font-size: 0.8em; 
            font-weight: 600;
            box-shadow: 0 1px 4px rgba(74, 144, 226, 0.2);
        }
        .completed-badge { 
            background: linear-gradient(135deg, #81ecec 0%, #00cec9 100%); 
            color: white; 
            padding: 4px 10px; 
            border-radius: 12px; 
            font-size: 0.75em; 
            font-weight: 600;
            box-shadow: 0 1px 4px rgba(0, 206, 201, 0.2);
        }
        
        /* タブ系スタイル */
        .tabs { display: flex; margin-bottom: 25px; gap: 5px; }
        .tab { 
            padding: 15px 30px; 
            cursor: pointer; 
            border: 2px solid #e8f4fd; 
            background: rgba(255, 255, 255, 0.9); 
            border-radius: 25px 25px 0 0; 
            transition: all 0.3s ease;
            font-weight: 500;
        }
        .tab.active { 
            background: linear-gradient(135deg, #6bb6ff 0%, #4a90e2 100%); 
            color: white; 
            border-color: #4a90e2;
        }
        .tab:hover:not(.active) {
            background: linear-gradient(135deg, #f8f9fb 0%, #e8f4fd 100%);
            transform: translateY(-2px);
        }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        
        /* 優先度バッジ */
        .priority-badge { 
            padding: 8px 16px; 
            border-radius: 20px; 
            color: white; 
            font-weight: bold; 
            font-size: 0.9em;
        }
        .priority-high .priority-badge { background: linear-gradient(135deg, #ff7675 0%, #e17055 100%); }
        .priority-medium .priority-badge { background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%); }
        .priority-low .priority-badge { background: linear-gradient(135deg, #81ecec 0%, #00cec9 100%); }
        
        /* 🤖 チャットボット関連スタイル */
        .chat-float-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #6bb6ff 0%, #4a90e2 100%);
            border: none;
            border-radius: 50%;
            box-shadow: 0 4px 20px rgba(74, 144, 226, 0.3);
            cursor: pointer;
            z-index: 1000;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 24px;
        }
        .chat-float-btn:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 25px rgba(74, 144, 226, 0.4);
        }
        .chat-popup {
            position: fixed;
            bottom: 100px;
            right: 30px;
            width: 350px;
            height: 500px;
            background: rgba(255, 255, 255, 0.98);
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(52, 73, 94, 0.15);
            border: 1px solid #e8f4fd;
            z-index: 999;
            display: none;
            flex-direction: column;
            overflow: hidden;
            animation: slideInUp 0.3s ease;
        }
        .chat-popup.open {
            display: flex;
        }
        @keyframes slideInUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .chat-header {
            background: linear-gradient(135deg, #6bb6ff 0%, #4a90e2 100%);
            color: white;
            padding: 15px 20px;
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .chat-close {
            background: none;
            border: none;
            color: white;
            font-size: 20px;
            cursor: pointer;
            opacity: 0.8;
            transition: opacity 0.3s;
        }
        .chat-close:hover {
            opacity: 1;
        }
        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: linear-gradient(135deg, #fdfcf5 0%, #f8f9fb 100%);
        }
        .chat-message {
            margin-bottom: 15px;
            animation: fadeInMessage 0.3s ease;
        }
        @keyframes fadeInMessage {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .chat-message.user {
            text-align: right;
        }
        .chat-message.assistant {
            text-align: left;
        }
        .chat-bubble {
            display: inline-block;
            padding: 12px 16px;
            border-radius: 18px;
            max-width: 85%;
            line-height: 1.4;
            word-wrap: break-word;
        }
        .chat-bubble.user {
            background: linear-gradient(135deg, #6bb6ff 0%, #4a90e2 100%);
            color: white;
        }
        .chat-bubble.assistant {
            background: rgba(255, 255, 255, 0.9);
            color: #2c3e50;
            border: 1px solid #e8f4fd;
            box-shadow: 0 2px 8px rgba(52, 73, 94, 0.05);
        }
        .chat-input-container {
            padding: 15px 20px;
            background: rgba(255, 255, 255, 0.95);
            border-top: 1px solid #e8f4fd;
            display: flex;
            gap: 10px;
        }
        .chat-input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e8f4fd;
            border-radius: 25px;
            outline: none;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        .chat-input:focus {
            border-color: #4a90e2;
        }
        .chat-send-btn {
            background: linear-gradient(135deg, #6bb6ff 0%, #4a90e2 100%);
            color: white;
            border: none;
            border-radius: 50%;
            width: 45px;
            height: 45px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(74, 144, 226, 0.2);
        }
        .chat-send-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
        }
        .chat-send-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .chat-typing {
            display: none;
            text-align: left;
            margin-bottom: 15px;
        }
        .chat-typing.show {
            display: block;
        }
        .typing-bubble {
            display: inline-block;
            padding: 12px 16px;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid #e8f4fd;
            color: #7f8c8d;
            font-style: italic;
        }
        .typing-dots {
            display: inline-block;
            animation: typingDots 1.5s infinite;
        }
        @keyframes typingDots {
            0%, 60%, 100% { opacity: 0.4; }
            30% { opacity: 1; }
        }
    """

def _get_common_script():
    """共通JavaScript"""
    return """
        // 🎯 統一されたコピー機能
        class UnifiedCopyManager {
            async copyEmailDraft(emailId) {
                const textarea = document.querySelector(`#markdown-textarea-${emailId}`);
                const button = event.target.closest('.copy-btn-unified');
                
                if (!textarea) {
                    this._showNotification('草案が見つかりません', 'error');
                    return false;
                }

                const text = textarea.value;
                if (!text.trim()) {
                    this._showNotification('コピーする内容がありません', 'warning');
                    return false;
                }

                return await this.copyToClipboard(text, button, '📋 メール草案をコピーしました！');
            }

            async copyToClipboard(text, button, successMessage = 'コピーしました！') {
                try {
                    await this._performCopy(text);
                    this._showButtonSuccess(button);
                    this._showNotification(successMessage, 'success');
                    return true;
                } catch (error) {
                    this._showNotification('コピーに失敗しました', 'error');
                    return false;
                }
            }

            async _performCopy(text) {
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    await navigator.clipboard.writeText(text);
                    return;
                }
                const tempTextarea = document.createElement('textarea');
                tempTextarea.value = text;
                tempTextarea.style.position = 'fixed';
                tempTextarea.style.opacity = '0';
                document.body.appendChild(tempTextarea);
                tempTextarea.select();
                const success = document.execCommand('copy');
                document.body.removeChild(tempTextarea);
                if (!success) throw new Error('Fallback copy failed');
            }

            _showButtonSuccess(button) {
                if (!button) return;
                const originalText = button.innerHTML;
                button.classList.add('success');
                button.innerHTML = '<span class="icon">✅</span><span>コピー完了</span>';
                button.disabled = true;
                setTimeout(() => {
                    button.classList.remove('success');
                    button.innerHTML = originalText;
                    button.disabled = false;
                }, 2000);
            }

            _showNotification(message, type = 'success') {
                const existingNotification = document.querySelector('.copy-notification');
                if (existingNotification) existingNotification.remove();

                const notification = document.createElement('div');
                notification.className = 'copy-notification';
                const icons = { success: '✅', error: '❌', warning: '⚠️' };
                notification.innerHTML = `<span class="icon">${icons[type] || icons.success}</span><span>${message}</span>`;
                
                if (type === 'error') {
                    notification.style.background = 'linear-gradient(135deg, #f44336 0%, #e57373 100%)';
                } else if (type === 'warning') {
                    notification.style.background = 'linear-gradient(135deg, #ff9800 0%, #ffb74d 100%)';
                }

                document.body.appendChild(notification);
                setTimeout(() => { if (notification.parentNode) notification.remove(); }, 3000);
            }
        }

        const copyManager = new UnifiedCopyManager();
        
        // グローバル関数
        async function copyEmailDraft(emailId) {
            return await copyManager.copyEmailDraft(emailId);
        }
        
        function showReplyTab(emailId, tabType) {
            document.querySelectorAll(`#reply-preview-${emailId}, #reply-markdown-${emailId}`).forEach(el => el.classList.remove('active'));
            document.querySelectorAll(`.tab-btn`).forEach(el => el.classList.remove('active'));
            document.getElementById(`reply-${tabType}-${emailId}`).classList.add('active');
            event.target.classList.add('active');
        }
        
        async function copyToClipboard(emailId) {
            return await copyManager.copyEmailDraft(emailId);
        }
        
        async function copyTextToClipboard(text, successMessage) {
            const button = event ? event.target.closest('.copy-btn-unified') : null;
            return await copyManager.copyToClipboard(text, button, successMessage);
        }
        
        function showCopySuccess(message) {
            copyManager._showNotification(message, 'success');
        }
        
        async function markCompleted(emailId) {
            try {
                const response = await fetch(`/emails/${emailId}/complete`, { method: 'POST' });
                const result = await response.json();
                if (result.success) { location.reload(); }
                else { alert('エラー: ' + result.error); }
            } catch (error) { alert('エラーが発生しました: ' + error.message); }
        }
        
        async function deleteEmail(emailId) {
            if (confirm('このメールを削除しますか？')) {
                try {
                    const response = await fetch(`/emails/${emailId}/delete`, { method: 'DELETE' });
                    const result = await response.json();
                    if (result.success) { location.reload(); }
                    else { alert('エラー: ' + result.error); }
                } catch (error) { alert('エラーが発生しました: ' + error.message); }
            }
        }
        
        function showTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            document.getElementById(tabName).classList.add('active');
            document.querySelector(`[onclick="showTab('${tabName}')"]`).classList.add('active');
        }

        // 🤖 チャットボット機能
        class ProfessorChatBot {
            constructor() {
                this.isOpen = false;
                this.messages = [];
                this.init();
            }
            
            init() {
                // 初回メッセージ
                this.messages = [{
                    type: 'assistant',
                    content: '🎓 こんにちは！ProfMail AIアシスタントです。\\n\\n今日のメール状況を確認したり、特定のメールを検索したりできます。\\n\\n例：「今日やるべきことは？」「高優先度のメールを見せて」「論文査読のメールは？」',
                    timestamp: new Date()
                }];
            }
            
            toggle() {
                const popup = document.getElementById('chat-popup');
                if (this.isOpen) {
                    popup.classList.remove('open');
                    this.isOpen = false;
                } else {
                    popup.classList.add('open');
                    this.isOpen = true;
                    this.renderMessages();
                    const input = document.getElementById('chat-input');
                    if (input) input.focus();
                }
            }
            
            async sendMessage() {
                const input = document.getElementById('chat-input');
                const message = input.value.trim();
                
                if (!message) return;
                
                // ユーザーメッセージを追加
                this.messages.push({
                    type: 'user',
                    content: message,
                    timestamp: new Date()
                });
                
                input.value = '';
                this.renderMessages();
                this.showTyping();
                
                try {
                    // APIにメッセージ送信
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: message })
                    });
                    
                    const result = await response.json();
                    
                    this.hideTyping();
                    
                    if (result.success) {
                        this.messages.push({
                            type: 'assistant',
                            content: result.response,
                            timestamp: new Date()
                        });
                    } else {
                        this.messages.push({
                            type: 'assistant',
                            content: '申し訳ございません。エラーが発生しました。',
                            timestamp: new Date()
                        });
                    }
                    
                    this.renderMessages();
                    
                } catch (error) {
                    this.hideTyping();
                    this.messages.push({
                        type: 'assistant',
                        content: 'ネットワークエラーが発生しました。しばらく後で再試行してください。',
                        timestamp: new Date()
                    });
                    this.renderMessages();
                }
            }
            
            renderMessages() {
                const container = document.getElementById('chat-messages');
                if (!container) return;
                
                container.innerHTML = '';
                
                this.messages.forEach(msg => {
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `chat-message ${msg.type}`;
                    
                    const bubbleDiv = document.createElement('div');
                    bubbleDiv.className = `chat-bubble ${msg.type}`;
                    bubbleDiv.innerHTML = msg.content.replace(/\\n/g, '<br>');
                    
                    messageDiv.appendChild(bubbleDiv);
                    container.appendChild(messageDiv);
                });
                
                // 最新メッセージまでスクロール
                container.scrollTop = container.scrollHeight;
            }
            
            showTyping() {
                const typingElement = document.getElementById('chat-typing');
                if (typingElement) {
                    typingElement.classList.add('show');
                    const container = document.getElementById('chat-messages');
                    if (container) container.scrollTop = container.scrollHeight;
                }
            }
            
            hideTyping() {
                const typingElement = document.getElementById('chat-typing');
                if (typingElement) {
                    typingElement.classList.remove('show');
                }
            }
            
            handleKeyPress(event) {
                if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    this.sendMessage();
                }
            }
        }
        
        // グローバルチャットボットインスタンス
        let chatBot;
        
        // ページ読み込み時にチャットボット初期化
        document.addEventListener('DOMContentLoaded', function() {
            chatBot = new ProfessorChatBot();
        });
        
        // グローバル関数
        function toggleChat() {
            if (chatBot) chatBot.toggle();
        }
        
        function sendChatMessage() {
            if (chatBot) chatBot.sendMessage();
        }
        
        function handleChatKeyPress(event) {
            if (chatBot) chatBot.handleKeyPress(event);
        }
    """


def _get_chat_bot_html():
    """チャットボットHTML"""
    return """
            <!-- 🤖 チャットボット -->
            <button class="chat-float-btn" onclick="toggleChat()">💬</button>
            <div id="chat-popup" class="chat-popup">
                <div class="chat-header">
                    <span>🎓 ProfMail AI アシスタント</span>
                    <button class="chat-close" onclick="toggleChat()">×</button>
                </div>
                <div id="chat-messages" class="chat-messages"></div>
                <div id="chat-typing" class="chat-typing">
                    <div class="typing-bubble">
                        <span class="typing-dots">入力中...</span>
                    </div>
                </div>
                <div class="chat-input-container">
                    <input 
                        type="text" 
                        id="chat-input" 
                        class="chat-input" 
                        placeholder="メッセージを入力..."
                        onkeypress="handleChatKeyPress(event)"
                    >
                    <button class="chat-send-btn" onclick="sendChatMessage()">📤</button>
                </div>
            </div>
    """


def _get_priority_html_template(priority_level: str, priority_jp: str, emails) -> str:
    """優先度別表示HTMLテンプレート（統一UI）"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{priority_jp}優先度メール - ProfMail</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            {_get_common_styles()}
        </style>
        <script>
            {_get_common_script()}
        </script>
    </head>
    <body>
        <div class="container priority-{priority_level}">
            <div class="header page-header">
                <a href="/" class="back-btn">←</a>
                <h2>
                    <span class="priority-badge">{priority_jp}優先度</span>
                    メール ({len(emails)}件)
                </h2>
            </div>
            
            {generate_email_cards(emails) if emails else '<div class="email-card"><div class="email-header"><p>📭 該当するメールがありません</p></div></div>'}
        </div>
        {_get_chat_bot_html()}
    </body>
    </html>
    """


def _get_completed_html_template(emails) -> str:
    """完了済みメール表示HTMLテンプレート（統一UI）"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>完了済みメール - ProfMail</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            {_get_common_styles()}
        </style>
        <script>
            {_get_common_script()}
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header page-header">
                <a href="/" class="back-btn">←</a>
                <h2>✅ 完了済みメール ({len(emails)}件)</h2>
            </div>
            
            <div class="email-table">
                <table>
                    <thead>
                        <tr>
                            <th>件名</th>
                            <th>送信者</th>
                            <th>カテゴリ</th>
                            <th>完了日時</th>
                            <th>アクション</th>
                        </tr>
                    </thead>
                    <tbody>
                        {generate_completed_email_rows(emails)}
                    </tbody>
                </table>
            </div>
        </div>
        {_get_chat_bot_html()}
    </body>
    </html>
    """


def _get_category_html_template(category_name: str, pending_emails, completed_emails) -> str:
    """カテゴリ別メール表示HTMLテンプレート（統一UI）"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{category_name} - ProfMail</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            {_get_common_styles()}
        </style>
        <script>
            {_get_common_script()}
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header page-header">
                <a href="/" class="back-btn">←</a>
                <h2>{category_name}</h2>
            </div>
            
            <div class="tabs">
                <div class="tab active" onclick="showTab('pending-tab')">未対応 ({len(pending_emails)})</div>
                <div class="tab" onclick="showTab('completed-tab')">完了済み ({len(completed_emails)})</div>
            </div>
            
            <div id="pending-tab" class="tab-content active">
                {generate_email_cards(pending_emails) if pending_emails else '<div class="email-card"><div class="email-header"><p>📭 未対応メールがありません</p></div></div>'}
            </div>
            
            <div id="completed-tab" class="tab-content">
                {generate_email_cards(completed_emails) if completed_emails else '<div class="email-card"><div class="email-header"><p>📭 完了済みメールがありません</p></div></div>'}
            </div>
        </div>
        {_get_chat_bot_html()}
    </body>
    </html>
    """


def _get_all_emails_html_template(emails) -> str:
    """すべてのメール表示HTMLテンプレート（統一UI）"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>すべてのメール - ProfMail</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            {_get_common_styles()}
        </style>
        <script>
            {_get_common_script()}
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header page-header">
                <a href="/" class="back-btn">←</a>
                <h2>📋 すべてのメール ({len(emails)}件)</h2>
            </div>
            
            <div class="email-table">
                <table>
                    <thead>
                        <tr>
                            <th>件名</th>
                            <th>送信者</th>
                            <th>カテゴリ</th>
                            <th>優先度</th>
                            <th>緊急度</th>
                            <th>アクション</th>
                        </tr>
                    </thead>
                    <tbody>
                        {generate_email_table_rows(emails)}
                    </tbody>
                </table>
            </div>
        </div>
        {_get_chat_bot_html()}
    </body>
    </html>
    """