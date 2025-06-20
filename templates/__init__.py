"""
テンプレート関連のパッケージ
"""
from .html_generator import (
    generate_email_cards,
    generate_category_list,
    generate_completed_email_rows,
    generate_email_table_rows
)

__all__ = [
    'generate_email_cards',
    'generate_category_list',
    'generate_completed_email_rows',
    'generate_email_table_rows'
]