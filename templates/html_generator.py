"""
HTML生成関数
"""
from typing import List, Dict, Any
from utils.helpers import truncate_text


def generate_email_cards(emails: List[Dict[str, Any]]) -> str:
    """メールカード生成"""
    if not emails:
        return '<div class="email-card"><div class="email-header"><p>📭 このカテゴリにはメールがありません</p></div></div>'
    
    cards = []
    for email in emails:
        reply_section = ""
        reply_draft = email.get("reply_draft", "")
        email_id = email.get("id", "")
        if reply_draft:
            # マークダウンを簡易HTMLに変換（基本的な変換のみ）
            reply_html = (reply_draft
                .replace('\n### ', '<br><h4>')
                .replace('\n## ', '<br><h3>')
                .replace('\n# ', '<br><h2>')
                .replace('**', '<strong>', 1).replace('**', '</strong>', 1)
                .replace('- ', '<br>• ')
                .replace('\n', '<br>'))
            
            # HTMLタグを閉じる
            reply_html = reply_html.replace('<h4>', '<h4>').replace('<h3>', '<h3>').replace('<h2>', '<h2>')
            
            reply_section = f'''<div class="reply-preview">
                <h5>🤖 AI返信草案</h5>
                <div class="reply-tabs">
                    <button class="tab-btn active" onclick="showReplyTab('{email_id}', 'preview')">👁️ プレビュー</button>
                    <button class="tab-btn" onclick="showReplyTab('{email_id}', 'markdown')">📝 編集可能</button>
                    <button class="copy-actions copy-btn-quick" onclick="copyToClipboard('{email_id}')">📋 ワンクリックコピー</button>
                </div>
                <div id="reply-preview-{email_id}" class="reply-content active">
                    <div class="reply-text">{reply_html}</div>
                </div>
                <div id="reply-markdown-{email_id}" class="reply-content">
                    <textarea id="markdown-textarea-{email_id}" class="markdown-text">{reply_draft}</textarea>
                </div>
            </div>'''
        
        sender = email.get("sender", "Unknown")
        sender_display = truncate_text(sender, 60)
        
        subject = email.get("subject", "No Subject")
        
        # メール本文表示の改善
        summary = email.get("summary", "")
        body = email.get("body", "")
        
        if summary and summary != "メール内容を分析中...":
            # AI分析済みの場合はsummaryを表示
            content_display = summary
        elif body:
            # AI分析前の場合はメール本文のプレビューを表示
            body_preview = body.replace('\n', ' ').replace('\r', ' ').strip()
            content_display = truncate_text(body_preview, 150)
        else:
            content_display = "メール内容を取得中..."
        
        priority = email.get("priority", "中")
        urgency_score = email.get("urgency_score", 5)
        date = email.get("date", "Unknown Date")
        gmail_link = email.get("gmail_link", "#")
        
        card = f'''<div class="email-card">
            <div class="email-header priority-{priority.lower()}">
                <div class="email-subject">{subject}</div>
                <div class="email-meta">
                    From: {sender_display}<br>
                    Date: {date[:25]}<br>
                    Priority: {priority} 
                    <span class="urgency-score">緊急度: {urgency_score}/10</span>
                </div>
                <div class="email-summary">
                    {content_display}
                </div>
                {reply_section}
            </div>
            
            <div class="email-actions">
                <a href="{gmail_link}" target="_blank" class="btn btn-primary">📧 Gmailで開く</a>
                <button onclick="markCompleted('{email_id}')" class="btn btn-success">✅ 完了</button>
                <button onclick="deleteEmail('{email_id}')" class="btn btn-danger">🗑️ 削除</button>
            </div>
        </div>'''
        cards.append(card)
    
    return ''.join(cards)


def generate_category_list(categories: Dict[str, str], stats: Dict[str, Any]) -> str:
    """カテゴリリスト生成"""
    items = []
    for category, icon in categories.items():
        count = stats.get('category_stats', {}).get(category, 0)
        # 件数に応じてクラスを設定
        count_class = "category-count-zero" if count == 0 else "category-count"
        item = f'''<li class="category-item" onclick="viewCategory('{category}')">
            <span class="category-icon">{icon}</span>
            {category}
            <span class="{count_class}">{count}</span>
        </li>'''
        items.append(item)
    return ''.join(items)


def generate_completed_email_rows(emails: List[Dict[str, Any]]) -> str:
    """完了メール行生成"""
    if not emails:
        return '<tr><td colspan="5" style="text-align: center; padding: 40px;">📭 完了済みメールがありません</td></tr>'
    
    rows = []
    for email in emails:
        subject = email.get("subject", "No Subject")
        sender = email.get("sender", "Unknown")
        category = email.get("category", "その他")
        completed_at = email.get("completed_at", "Unknown")
        gmail_link = email.get("gmail_link", "#")
        
        subject_display = truncate_text(subject, 50)
        sender_display = truncate_text(sender, 30)
        completed_display = completed_at[:19] if completed_at != "Unknown" else "未記録"
        
        row = f'''<tr class="completed-item">
            <td><strong>{subject_display}</strong><br>
                <span class="completed-badge">完了済み</span>
            </td>
            <td>{sender_display}</td>
            <td><span class="category-badge">{category}</span></td>
            <td>{completed_display}</td>
            <td>
                <a href="{gmail_link}" target="_blank" class="btn btn-primary">Gmail</a>
            </td>
        </tr>'''
        rows.append(row)
    
    return ''.join(rows)


def generate_email_table_rows(emails: List[Dict[str, Any]]) -> str:
    """メールテーブル行生成（固定レイアウト対応）"""
    if not emails:
        return '<tr><td colspan="6" style="text-align: center; padding: 40px;">📭 メールがありません</td></tr>'
    
    rows = []
    for email in emails:
        subject = email.get("subject", "No Subject")
        
        # メール本文表示の改善
        summary = email.get("summary", "")
        body = email.get("body", "")
        
        if summary and summary != "メール内容を分析中...":
            # AI分析済みの場合はsummaryを表示
            content_display = summary
        elif body:
            # AI分析前の場合はメール本文のプレビューを表示
            body_preview = body.replace('\n', ' ').replace('\r', ' ').strip()
            content_display = truncate_text(body_preview, 60)
        else:
            content_display = "メール内容を取得中..."
        
        sender = email.get("sender", "Unknown")
        category = email.get("category", "その他")
        priority = email.get("priority", "中")
        urgency_score = email.get("urgency_score", 5)
        gmail_link = email.get("gmail_link", "#")
        
        # 文字数制限を調整（固定幅に合わせて）
        subject_display = truncate_text(subject, 35)
        content_display = truncate_text(content_display, 50)
        sender_display = truncate_text(sender, 20)
        
        # HTMLエスケープ処理
        subject_escaped = subject.replace('"', '&quot;').replace("'", "&#39;")
        content_escaped = content_display.replace('"', '&quot;').replace("'", "&#39;")
        sender_escaped = sender.replace('"', '&quot;').replace("'", "&#39;")
        
        row = f'''<tr class="priority-{priority.lower()}">
            <td>
                <strong class="subject-cell" title="{subject_escaped}">{subject_display}</strong>
                <small class="subject-preview" title="{content_escaped}">{content_display}</small>
            </td>
            <td class="sender-cell" title="{sender_escaped}">{sender_display}</td>
            <td><span class="category-badge">{category}</span></td>
            <td>{priority}</td>
            <td>{urgency_score}/10</td>
            <td>
                <a href="{gmail_link}" target="_blank" class="btn btn-primary">Gmail</a>
                <button onclick="location.href='/category/{category}'" class="btn btn-success">詳細</button>
            </td>
        </tr>'''
        rows.append(row)
    
    return ''.join(rows)