"""
FastAPI ルート定義 (Slack機能追加版)
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
                    background: #fff9c4; 
                    min-height: 100vh; 
                }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .header {{ 
                    text-align: center; 
                    color: #1565c0; 
                    margin-bottom: 30px; 
                    background: white;
                    padding: 20px;
                    border-radius: 15px;
                    box-shadow: 0 8px 32px rgba(21, 101, 192, 0.1);
                    border: 2px solid #ffd54f;
                }}
                .header h1 {{ 
                    font-size: 2.5em; 
                    margin-bottom: 10px; 
                    background: linear-gradient(45deg, #1565c0, #ffa726);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                }}
                .header p {{ font-size: 1.2em; opacity: 0.8; color: #1565c0; }}
                .dashboard {{ display: grid; grid-template-columns: 1fr 2fr; gap: 20px; }}
                .sidebar {{ 
                    background: white; 
                    border-radius: 15px; 
                    padding: 20px; 
                    box-shadow: 0 8px 32px rgba(21, 101, 192, 0.1);
                    border: 1px solid #e3f2fd;
                }}
                .main-content {{ 
                    background: white; 
                    border-radius: 15px; 
                    padding: 20px; 
                    box-shadow: 0 8px 32px rgba(21, 101, 192, 0.1);
                    border: 1px solid #e3f2fd;
                }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 20px; }}
                .stat-box {{ 
                    background: linear-gradient(135deg, #42a5f5 0%, #1976d2 100%); 
                    padding: 20px; 
                    border-radius: 10px; 
                    text-align: center; 
                    color: white;
                    text-decoration: none;
                    transition: transform 0.3s ease;
                    border: 2px solid #ffd54f;
                }}
                .stat-box:hover {{ transform: translateY(-3px); }}
                .stat-number {{ font-size: 2em; font-weight: bold; }}
                .stat-label {{ font-size: 0.9em; opacity: 0.9; }}
                .category-list {{ list-style: none; padding: 0; }}
                .category-item {{ 
                    background: #f8f9fa; 
                    margin: 10px 0; 
                    padding: 15px; 
                    border-radius: 8px; 
                    cursor: pointer; 
                    transition: all 0.3s; 
                    border-left: 4px solid #1976d2;
                    border: 1px solid #e3f2fd;
                }}
                .category-item:hover {{ 
                    transform: translateX(5px); 
                    box-shadow: 0 4px 12px rgba(21, 101, 192, 0.2);
                    background: #e3f2fd;
                }}
                .category-icon {{ font-size: 1.5em; margin-right: 10px; }}
                .category-count {{ 
                    float: right; 
                    background: #ffa726; 
                    color: white; 
                    padding: 4px 8px; 
                    border-radius: 12px; 
                    font-size: 0.8em; 
                    font-weight: bold;
                }}
                .action-buttons {{ padding: 30px; margin: 20px 0; text-align: center; }}
                .btn {{ 
                    background: linear-gradient(135deg, #1976d2 0%, #42a5f5 100%); 
                    color: white; 
                    padding: 12px 24px; 
                    border: none; 
                    border-radius: 25px; 
                    cursor: pointer; 
                    margin: 5px; 
                    text-decoration: none; 
                    display: inline-block; 
                    transition: all 0.3s;
                    border: 2px solid #ffd54f;
                }}
                .btn:hover {{ 
                    transform: translateY(-2px); 
                    box-shadow: 0 4px 12px rgba(21, 101, 192, 0.3);
                }}
                .btn-success {{ 
                    background: linear-gradient(135deg, #ffa726 0%, #ffb74d 100%);
                    color: #1565c0;
                    font-weight: bold;
                }}
                .btn-slack {{ 
                    background: linear-gradient(135deg, #4a154b 0%, #611f69 100%);
                    color: white;
                    font-weight: bold;
                }}
                #process-btn {{
                    border-radius: 40px !important;
                    padding: 22px 48px !important;
                    font-size: 1.5em !important;
                    font-weight: bold !important;
                    box-shadow: 0 6px 24px rgba(255, 167, 38, 0.18);
                }}
                #slack-test-btn {{
                    border-radius: 30px !important;
                    padding: 12px 24px !important;
                    font-size: 1em !important;
                    margin-top: 10px !important;
                }}
                .priority-high {{ border-left-color: #e74c3c; }}
                .priority-medium {{ border-left-color: #ffa726; }}
                .priority-low {{ border-left-color: #66bb6a; }}
                .clickable {{ cursor: pointer; }}
                
                /* 🎨 統一されたコピーボタンスタイル */
                .copy-btn-unified {{
                    background: linear-gradient(135deg, #1976d2 0%, #42a5f5 100%);
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 25px;
                    cursor: pointer;
                    font-size: 0.9em;
                    font-weight: 600;
                    transition: all 0.3s ease;
                    border: 2px solid rgba(255, 255, 255, 0.2);
                    box-shadow: 0 4px 12px rgba(25, 118, 210, 0.2);
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    text-decoration: none;
                    user-select: none;
                }}
                .copy-btn-unified:hover {{
                    background: linear-gradient(135deg, #1565c0 0%, #1976d2 100%);
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(25, 118, 210, 0.4);
                }}
                .copy-btn-unified.success {{
                    background: linear-gradient(135deg, #4caf50 0%, #66bb6a 100%);
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
                    background: linear-gradient(135deg, #4caf50 0%, #66bb6a 100%);
                    color: white;
                    padding: 16px 24px;
                    border-radius: 12px;
                    box-shadow: 0 8px 32px rgba(76, 175, 80, 0.3);
                    z-index: 1000;
                    font-weight: 600;
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
                    document.getElementById('process-btn').textContent = '処理中...';
                    document.getElementById('process-btn').disabled = true;
                    
                    try {{
                        const response = await fetch('/process', {{ method: 'POST' }});
                        const result = await response.json();
                        
                        if (result.success) {{
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
                            
                            alert(message);
                            location.reload();
                        }} else {{
                            alert('エラー: ' + result.error);
                        }}
                    }} catch (error) {{
                        alert('エラーが発生しました: ' + error.message);
                    }}
                    
                    document.getElementById('process-btn').textContent = '📬 今すぐ処理';
                    document.getElementById('process-btn').disabled = false;
                }}
                
                async function testSlackNotification() {{
                    document.getElementById('slack-test-btn').textContent = '送信中...';
                    document.getElementById('slack-test-btn').disabled = true;
                    
                    try {{
                        const response = await fetch('/slack/test', {{ method: 'POST' }});
                        const result = await response.json();
                        
                        if (result.success) {{
                            alert('✅ Slackテスト通知を送信しました！\\nSlackチャンネルを確認してください。');
                        }} else {{
                            alert('❌ Slack通知送信失敗: ' + (result.error || result.message));
                        }}
                    }} catch (error) {{
                        alert('エラーが発生しました: ' + error.message);
                    }}
                    
                    document.getElementById('slack-test-btn').textContent = 'Slack テスト';
                    document.getElementById('slack-test-btn').disabled = false;
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
                            <a href="/completed" class="stat-box clickable">
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
                                <div style="text-align: center; padding: 30px; border-radius: 12px; transition: all 0.3s; cursor: pointer; background: #ffebee; border: 2px solid #e74c3c;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                                    <div style="font-size: 2em; color: #e74c3c; font-weight: bold;">{stats.get('priority_stats', {}).get('高', 0)}</div>
                                    <div style="color: #e74c3c; font-weight: bold;">高</div>
                                </div>
                            </a>
                            <a href="/priority/medium" style="text-decoration: none; color: inherit;">
                                <div style="text-align: center; padding: 30px; border-radius: 12px; transition: all 0.3s; cursor: pointer; background: #fff8e1; border: 2px solid #ffa726;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                                    <div style="font-size: 2em; color: #ffa726; font-weight: bold;">{stats.get('priority_stats', {}).get('中', 0)}</div>
                                    <div style="color: #ffa726; font-weight: bold;">中</div>
                                </div>
                            </a>
                            <a href="/priority/low" style="text-decoration: none; color: inherit;">
                                <div style="text-align: center; padding: 30px; border-radius: 12px; transition: all 0.3s; cursor: pointer; background: #e8f5e8; border: 2px solid #66bb6a;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                                    <div style="font-size: 2em; color: #66bb6a; font-weight: bold;">{stats.get('priority_stats', {}).get('低', 0)}</div>
                                    <div style="color: #66bb6a; font-weight: bold;">低</div>
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
            "version": "3.3.0 - Status Preservation Edition"
        }


def _get_priority_html_template(priority_level: str, priority_jp: str, emails) -> str:
    """優先度別表示HTMLテンプレート"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{priority_jp}優先度メール - ProfMail</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #e3f2fd 0%, #ffffff 50%, #fff9c4 100%);
            }}
            .container {{ max-width: 1000px; margin: 0 auto; }}
            .header {{ 
                background: white; 
                padding: 20px; 
                border-radius: 10px; 
                margin-bottom: 20px; 
                box-shadow: 0 4px 20px rgba(21, 101, 192, 0.1);
                border: 2px solid #ffd54f;
            }}
            .back-btn {{ 
                background: #1976d2; 
                color: white; 
                padding: 8px 16px; 
                border: none; 
                border-radius: 20px; 
                text-decoration: none; 
                margin-right: 10px;
                border: 2px solid #ffd54f;
            }}
            .priority-badge {{ 
                padding: 8px 16px; 
                border-radius: 20px; 
                color: white; 
                font-weight: bold; 
            }}
            .priority-high .priority-badge {{ background: #e74c3c; }}
            .priority-medium .priority-badge {{ background: #ffa726; }}
            .priority-low .priority-badge {{ background: #66bb6a; }}
            .email-card {{ 
                background: white; 
                margin: 15px 0; 
                border-radius: 10px; 
                box-shadow: 0 4px 20px rgba(21, 101, 192, 0.1); 
                overflow: hidden;
                border: 1px solid #e3f2fd;
            }}
            .email-header {{ 
                padding: 20px; 
                border-left: 4px solid #1976d2; 
            }}
            .email-subject {{ 
                font-size: 1.2em; 
                font-weight: bold; 
                margin-bottom: 10px; 
                color: #1565c0; 
            }}
            .email-meta {{ 
                color: #7f8c8d; 
                font-size: 0.9em; 
                margin-bottom: 15px; 
            }}
            .email-summary {{ 
                color: #34495e; 
                margin-bottom: 15px; 
                padding: 10px; 
                background: #e3f2fd; 
                border-radius: 5px; 
            }}
            .email-actions {{ 
                padding: 0 20px 20px 20px; 
            }}
            .btn {{ 
                padding: 8px 16px; 
                margin: 5px; 
                border: none; 
                border-radius: 5px; 
                cursor: pointer; 
                text-decoration: none; 
                display: inline-block; 
            }}
            .btn-primary {{ background: #1976d2; color: white; }}
            .btn-success {{ background: #ffa726; color: white; }}
            .btn-danger {{ background: #e74c3c; color: white; }}
            .priority-high {{ border-left-color: #e74c3c !important; }}
            .priority-medium {{ border-left-color: #ffa726 !important; }}
            .priority-low {{ border-left-color: #66bb6a !important; }}
            .urgency-score {{ 
                background: #ffa726; 
                color: white; 
                padding: 4px 8px; 
                border-radius: 12px; 
                font-size: 0.8em; 
            }}
            .reply-preview {{ 
                background: #fff8e1; 
                padding: 15px; 
                margin: 10px 0; 
                border-radius: 5px; 
                border-left: 3px solid #ffa726; 
            }}
            .reply-preview h5 {{ 
                margin: 0 0 10px 0; 
                color: #ffa726; 
            }}
            .reply-tabs {{ margin-bottom: 10px; }}
            .tab-btn {{ 
                padding: 5px 12px; 
                border: 1px solid #ffa726; 
                background: white; 
                cursor: pointer; 
                margin-right: 5px; 
                border-radius: 3px; 
            }}
            .tab-btn.active {{ 
                background: #ffa726; 
                color: white; 
            }}
            .reply-content {{ display: none; }}
            .reply-content.active {{ display: block; }}
            .reply-text {{ 
                font-style: italic; 
                color: #495057; 
                line-height: 1.6; 
            }}
            .markdown-text {{ 
                width: 100%; 
                height: 200px; 
                border: 2px solid #e3f2fd; 
                border-radius: 8px; 
                padding: 15px; 
                font-family: 'Courier New', monospace; 
                resize: vertical; 
                font-size: 14px;
                line-height: 1.5;
            }}
            .markdown-text:focus {{ 
                border-color: #1976d2; 
                outline: none;
                box-shadow: 0 0 5px rgba(25, 118, 210, 0.3);
            }}
            .copy-btn-quick {{ 
                background: #1976d2; 
                color: white; 
                border: none; 
                padding: 6px 15px; 
                border-radius: 20px; 
                cursor: pointer; 
                font-size: 0.9em;
                font-weight: bold;
                transition: all 0.3s ease;
                border: 2px solid #fff;
            }}
            .copy-btn-quick:hover {{ 
                background: #1565c0; 
                transform: translateY(-1px);
                box-shadow: 0 2px 8px rgba(25, 118, 210, 0.4);
            }}
            .copy-success-alert {{
                position: fixed;
                top: 20px;
                right: 20px;
                background: #4caf50;
                color: white;
                padding: 15px 20px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                z-index: 1000;
                font-weight: bold;
            }}
            
            /* 🎨 統一されたコピーボタンスタイル */
            .copy-btn-unified {{
                background: linear-gradient(135deg, #1976d2 0%, #42a5f5 100%);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 25px;
                cursor: pointer;
                font-size: 0.9em;
                font-weight: 600;
                transition: all 0.3s ease;
                border: 2px solid rgba(255, 255, 255, 0.2);
                box-shadow: 0 4px 12px rgba(25, 118, 210, 0.2);
                display: inline-flex;
                align-items: center;
                gap: 8px;
                text-decoration: none;
                user-select: none;
            }}
            .copy-btn-unified:hover {{
                background: linear-gradient(135deg, #1565c0 0%, #1976d2 100%);
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(25, 118, 210, 0.4);
            }}
            .copy-btn-unified.success {{
                background: linear-gradient(135deg, #4caf50 0%, #66bb6a 100%);
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
                background: linear-gradient(135deg, #4caf50 0%, #66bb6a 100%);
                color: white;
                padding: 16px 24px;
                border-radius: 12px;
                box-shadow: 0 8px 32px rgba(76, 175, 80, 0.3);
                z-index: 1000;
                font-weight: 600;
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
            
            function showReplyTab(emailId, tabType) {{
                document.querySelectorAll(`#reply-preview-${{emailId}}, #reply-markdown-${{emailId}}`).forEach(el => el.classList.remove('active'));
                document.querySelectorAll(`.tab-btn`).forEach(el => el.classList.remove('active'));
                document.getElementById(`reply-${{tabType}}-${{emailId}}`).classList.add('active');
                event.target.classList.add('active');
            }}
            
            async function copyToClipboard(emailId) {{
                return await copyManager.copyEmailDraft(emailId);
            }}
            
            async function copyTextToClipboard(text, successMessage) {{
                const button = event ? event.target.closest('.copy-btn-unified') : null;
                return await copyManager.copyToClipboard(text, button, successMessage);
            }}
            
            function showCopySuccess(message) {{
                copyManager._showNotification(message, 'success');
            }}
            
            async function markCompleted(emailId) {{
                try {{
                    const response = await fetch(`/emails/${{emailId}}/complete`, {{ method: 'POST' }});
                    const result = await response.json();
                    if (result.success) {{ location.reload(); }}
                    else {{ alert('エラー: ' + result.error); }}
                }} catch (error) {{ alert('エラーが発生しました: ' + error.message); }}
            }}
            
            async function deleteEmail(emailId) {{
                if (confirm('このメールを削除しますか？')) {{
                    try {{
                        const response = await fetch(`/emails/${{emailId}}/delete`, {{ method: 'DELETE' }});
                        const result = await response.json();
                        if (result.success) {{ location.reload(); }}
                        else {{ alert('エラー: ' + result.error); }}
                    }} catch (error) {{ alert('エラーが発生しました: ' + error.message); }}
                }}
            }}
        </script>
    </head>
    <body>
        <div class="container priority-{priority_level}">
            <div class="header">
                <a href="/" class="back-btn">← ダッシュボード</a>
                <h2 style="color: #1565c0;">
                    <span class="priority-badge">{priority_jp}優先度</span>
                    メール ({len(emails)}件)
                </h2>
            </div>
            
            {generate_email_cards(emails) if emails else '<div class="email-card"><div class="email-header"><p>📭 該当するメールがありません</p></div></div>'}
        </div>
    </body>
    </html>
    """


def _get_completed_html_template(emails) -> str:
    """完了済みメール表示HTMLテンプレート"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>完了済みメール - ProfMail</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #e3f2fd 0%, #ffffff 50%, #fff9c4 100%);
            }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ 
                background: white; 
                padding: 20px; 
                border-radius: 10px; 
                margin-bottom: 20px; 
                box-shadow: 0 4px 20px rgba(21, 101, 192, 0.1);
                border: 2px solid #ffd54f;
            }}
            .back-btn {{ 
                background: #1976d2; 
                color: white; 
                padding: 8px 16px; 
                border: none; 
                border-radius: 20px; 
                text-decoration: none; 
                margin-right: 10px;
                border: 2px solid #ffd54f;
            }}
            .email-table {{ 
                background: white; 
                border-radius: 10px; 
                overflow: hidden; 
                box-shadow: 0 4px 20px rgba(21, 101, 192, 0.1);
                border: 1px solid #e3f2fd;
            }}
            .email-table table {{ width: 100%; border-collapse: collapse; }}
            .email-table th {{ 
                background: #66bb6a; 
                color: white; 
                padding: 15px; 
                text-align: left; 
            }}
            .email-table td {{ 
                padding: 15px; 
                border-bottom: 1px solid #e3f2fd; 
            }}
            .email-table tr:hover {{ background: #f8f9fa; }}
            .completed-item {{ 
                background: #e8f5e8; 
                opacity: 0.8; 
            }}
            .btn {{ 
                padding: 5px 10px; 
                margin: 2px; 
                border: none; 
                border-radius: 3px; 
                cursor: pointer; 
                text-decoration: none; 
                font-size: 0.8em; 
            }}
            .btn-primary {{ background: #1976d2; color: white; }}
            .btn-success {{ background: #66bb6a; color: white; }}
            .category-badge {{ 
                background: #66bb6a; 
                color: white; 
                padding: 3px 8px; 
                border-radius: 10px; 
                font-size: 0.7em; 
            }}
            .completed-badge {{ 
                background: #4caf50; 
                color: white; 
                padding: 2px 6px; 
                border-radius: 8px; 
                font-size: 0.7em; 
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <a href="/" class="back-btn">← ダッシュボード</a>
                <h2 style="color: #1565c0;">✅ 完了済みメール ({len(emails)}件)</h2>
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
    </body>
    </html>
    """


def _get_category_html_template(category_name: str, pending_emails, completed_emails) -> str:
    """カテゴリ別メール表示HTMLテンプレート"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{category_name} - ProfMail</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #e3f2fd 0%, #ffffff 50%, #fff9c4 100%);
            }}
            .container {{ max-width: 1000px; margin: 0 auto; }}
            .header {{ 
                background: white; 
                padding: 20px; 
                border-radius: 10px; 
                margin-bottom: 20px; 
                box-shadow: 0 4px 20px rgba(21, 101, 192, 0.1);
                border: 2px solid #ffd54f;
            }}
            .back-btn {{ 
                background: #1976d2; 
                color: white; 
                padding: 8px 16px; 
                border: none; 
                border-radius: 20px; 
                text-decoration: none; 
                margin-right: 10px;
                border: 2px solid #ffd54f;
            }}
            .tabs {{ display: flex; margin-bottom: 20px; }}
            .tab {{ 
                padding: 12px 24px; 
                cursor: pointer; 
                border: 1px solid #ddd; 
                background: #f8f9fa; 
                margin-right: 5px; 
                border-radius: 5px 5px 0 0; 
            }}
            .tab.active {{ 
                background: #1976d2; 
                color: white; 
            }}
            .tab-content {{ display: none; }}
            .tab-content.active {{ display: block; }}
            .email-card {{ 
                background: white; 
                margin: 15px 0; 
                border-radius: 10px; 
                box-shadow: 0 4px 20px rgba(21, 101, 192, 0.1); 
                overflow: hidden;
                border: 1px solid #e3f2fd;
            }}
            .email-header {{ 
                padding: 20px; 
                border-left: 4px solid #1976d2; 
            }}
            .email-subject {{ 
                font-size: 1.2em; 
                font-weight: bold; 
                margin-bottom: 10px; 
                color: #1565c0; 
            }}
            .email-meta {{ 
                color: #7f8c8d; 
                font-size: 0.9em; 
                margin-bottom: 15px; 
            }}
            .email-summary {{ 
                color: #34495e; 
                margin-bottom: 15px; 
                padding: 10px; 
                background: #e3f2fd; 
                border-radius: 5px; 
            }}
            .email-actions {{ 
                padding: 0 20px 20px 20px; 
            }}
            .btn {{ 
                padding: 8px 16px; 
                margin: 5px; 
                border: none; 
                border-radius: 5px; 
                cursor: pointer; 
                text-decoration: none; 
                display: inline-block; 
            }}
            .btn-primary {{ background: #1976d2; color: white; }}
            .btn-success {{ background: #ffa726; color: white; }}
            .btn-danger {{ background: #e74c3c; color: white; }}
            .priority-high {{ border-left-color: #e74c3c !important; }}
            .priority-medium {{ border-left-color: #ffa726 !important; }}
            .priority-low {{ border-left-color: #66bb6a !important; }}
            .urgency-score {{ 
                background: #ffa726; 
                color: white; 
                padding: 4px 8px; 
                border-radius: 12px; 
                font-size: 0.8em; 
            }}
            .reply-preview {{ 
                background: #fff8e1; 
                padding: 15px; 
                margin: 10px 0; 
                border-radius: 5px; 
                border-left: 3px solid #ffa726; 
            }}
            .reply-preview h5 {{ 
                margin: 0 0 10px 0; 
                color: #ffa726; 
            }}
            .reply-tabs {{ margin-bottom: 10px; }}
            .tab-btn {{ 
                padding: 5px 12px; 
                border: 1px solid #ffa726; 
                background: white; 
                cursor: pointer; 
                margin-right: 5px; 
                border-radius: 3px; 
            }}
            .tab-btn.active {{ 
                background: #ffa726; 
                color: white; 
            }}
            .reply-content {{ display: none; }}
            .reply-content.active {{ display: block; }}
            .reply-text {{ 
                font-style: italic; 
                color: #495057; 
                line-height: 1.6; 
            }}
            .markdown-text {{ 
                width: 100%; 
                height: 200px; 
                border: 1px solid #ddd; 
                border-radius: 5px; 
                padding: 10px; 
                font-family: monospace; 
                resize: vertical; 
            }}
            .copy-btn {{ 
                background: #66bb6a; 
                color: white; 
                border: none; 
                padding: 5px 10px; 
                border-radius: 3px; 
                cursor: pointer; 
                margin-top: 5px; 
            }}
            .copy-btn:hover {{ background: #4caf50; }}
            .completed-item {{ 
                opacity: 0.7; 
                background: #e8f5e8; 
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
            
            function showTab(tabName) {{
                document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
                document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
                document.getElementById(tabName).classList.add('active');
                document.querySelector(`[onclick="showTab('${{tabName}}')"]`).classList.add('active');
            }}
            
            function showReplyTab(emailId, tabType) {{
                document.querySelectorAll(`#reply-preview-${{emailId}}, #reply-markdown-${{emailId}}`).forEach(el => el.classList.remove('active'));
                document.querySelectorAll(`.tab-btn`).forEach(el => el.classList.remove('active'));
                document.getElementById(`reply-${{tabType}}-${{emailId}}`).classList.add('active');
                event.target.classList.add('active');
            }}
            
            async function copyToClipboard(emailId) {{
                return await copyManager.copyEmailDraft(emailId);
            }}
            
            async function markCompleted(emailId) {{
                try {{
                    const response = await fetch(`/emails/${{emailId}}/complete`, {{ method: 'POST' }});
                    const result = await response.json();
                    if (result.success) {{ location.reload(); }}
                    else {{ alert('エラー: ' + result.error); }}
                }} catch (error) {{ alert('エラーが発生しました: ' + error.message); }}
            }}
            
            async function deleteEmail(emailId) {{
                if (confirm('このメールを削除しますか？')) {{
                    try {{
                        const response = await fetch(`/emails/${{emailId}}/delete`, {{ method: 'DELETE' }});
                        const result = await response.json();
                        if (result.success) {{ location.reload(); }}
                        else {{ alert('エラー: ' + result.error); }}
                    }} catch (error) {{ alert('エラーが発生しました: ' + error.message); }}
                }}
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <a href="/" class="back-btn">← ダッシュボード</a>
                <h2 style="color: #1565c0;">{category_name}</h2>
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
    </body>
    </html>
    """


def _get_all_emails_html_template(emails) -> str:
    """すべてのメール表示HTMLテンプレート"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>すべてのメール - ProfMail</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #e3f2fd 0%, #ffffff 50%, #fff9c4 100%);
            }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ 
                background: white; 
                padding: 20px; 
                border-radius: 10px; 
                margin-bottom: 20px; 
                box-shadow: 0 4px 20px rgba(21, 101, 192, 0.1);
                border: 2px solid #ffd54f;
            }}
            .back-btn {{ 
                background: #1976d2; 
                color: white; 
                padding: 8px 16px; 
                border: none; 
                border-radius: 20px; 
                text-decoration: none; 
                margin-right: 10px;
                border: 2px solid #ffd54f;
            }}
            .email-table {{ 
                background: white; 
                border-radius: 10px; 
                overflow: hidden; 
                box-shadow: 0 4px 20px rgba(21, 101, 192, 0.1);
                border: 1px solid #e3f2fd;
            }}
            .email-table table {{ width: 100%; border-collapse: collapse; }}
            .email-table th {{ 
                background: #1976d2; 
                color: white; 
                padding: 15px; 
                text-align: left; 
            }}
            .email-table td {{ 
                padding: 15px; 
                border-bottom: 1px solid #e3f2fd; 
            }}
            .email-table tr:hover {{ background: #f8f9fa; }}
            .priority-high {{ background: #ffebee; }}
            .priority-medium {{ background: #fff8e1; }}
            .priority-low {{ background: #e8f5e8; }}
            .btn {{ 
                padding: 5px 10px; 
                margin: 2px; 
                border: none; 
                border-radius: 3px; 
                cursor: pointer; 
                text-decoration: none; 
                font-size: 0.8em; 
            }}
            .btn-primary {{ background: #1976d2; color: white; }}
            .btn-success {{ background: #ffa726; color: white; }}
            .btn-danger {{ background: #e74c3c; color: white; }}
            .category-badge {{ 
                background: #1976d2; 
                color: white; 
                padding: 3px 8px; 
                border-radius: 10px; 
                font-size: 0.7em; 
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <a href="/" class="back-btn">← ダッシュボード</a>
                <h2 style="color: #1565c0;">📋 すべてのメール ({len(emails)}件)</h2>
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
    </body>
    </html>
    """