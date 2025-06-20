"""
ユーティリティ関数
"""
from datetime import datetime
from typing import Optional


def format_datetime(dt: Optional[datetime], format_str: str = '%Y-%m-%d %H:%M') -> str:
    """日時フォーマット"""
    if dt is None:
        return '未記録'
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except:
            return dt[:19] if len(dt) > 19 else dt
    return dt.strftime(format_str)


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """テキスト切り詰め"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + suffix


def extract_email_domain(email: str) -> str:
    """メールアドレスからドメイン抽出"""
    try:
        return email.split('@')[1] if '@' in email else 'unknown'
    except IndexError:
        return 'unknown'


def clean_html_tags(text: str) -> str:
    """HTMLタグ除去（簡易版）"""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def generate_gmail_link(email_id: str, link_type: str = 'all') -> str:
    """Gmailリンク生成"""
    base_url = "https://mail.google.com/mail/u/0/"
    
    link_map = {
        'all': f"{base_url}#all/{email_id}",
        'inbox': f"{base_url}#inbox/{email_id}",
        'search': f"{base_url}?shva=1#search/rfc822msgid%3A{email_id}"
    }
    
    return link_map.get(link_type, link_map['all'])