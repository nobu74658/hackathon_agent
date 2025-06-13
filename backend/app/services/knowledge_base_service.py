"""
社内ナレッジベースサービス
会社のミッション・ビジョン・バリュー、先輩の資料、ベストプラクティスなどを管理
"""

from typing import Dict, Any, List, Optional
import json
from datetime import datetime
from pathlib import Path

class KnowledgeBaseService:
    """社内ナレッジを管理・検索するサービス"""
    
    def __init__(self):
        self.knowledge_base = self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self) -> Dict[str, Any]:
        """ナレッジベースの初期化（デモ用のハードコードデータ）"""
        return {
            "company_info": {
                "mission": "すべてのビジネスパートナーに最高の価値を提供し、共に成長する",
                "vision": "業界をリードする信頼されるパートナー企業になる",
                "values": [
                    "顧客第一主義 - お客様の成功が私たちの成功",
                    "誠実性 - 約束を守り、透明性を保つ",
                    "イノベーション - 常に改善と革新を追求",
                    "チームワーク - 互いを尊重し、協力して目標達成",
                    "成長マインドセット - 学び続け、挑戦し続ける"
                ]
            },
            "sales_best_practices": {
                "新規開拓": {
                    "templates": {
                        "初回アプローチメール": {
                            "subject": "【{company_name}様】{value_proposition}のご提案",
                            "body": """
{contact_name}様

お世話になっております。
{our_company}の{sender_name}と申します。

{trigger_event}を拝見し、{specific_challenge}の解決に
お役立ちできるのではないかと思い、ご連絡させていただきました。

弊社では、{similar_companies}などの企業様で
{specific_result}という成果を実現しております。

{company_name}様でも、以下のような価値をご提供できると考えております：
・{benefit_1}
・{benefit_2}
・{benefit_3}

もしご興味をお持ちいただけましたら、
15分程度のお電話でより詳しくご説明させていただけないでしょうか。

{contact_name}様のご都合の良い日時をいくつかお教えいただければ幸いです。

お忙しいところ恐縮ですが、ご検討のほどよろしくお願いいたします。

{sender_name}
{sender_title}
{contact_info}
""",
                            "tips": [
                                "相手企業の最新ニュースや課題を事前にリサーチ",
                                "具体的な数値や事例を含める",
                                "長すぎないよう簡潔にまとめる",
                                "次のアクションを明確にする"
                            ]
                        },
                        "電話スクリプト": {
                            "opening": "お忙しいところ恐れ入ります。{company}の{name}と申します。{trigger}について、{value}のご提案でお電話させていただきました。今2-3分お時間よろしいでしょうか？",
                            "value_prop": "実は、{similar_company}様でも同様の課題をお持ちでしたが、弊社のソリューションで{result}という成果を実現されました。",
                            "closing": "もう少し詳しくお話しさせていただく機会をいただけないでしょうか。来週あたりで30分ほどお時間をいただけますでしょうか？"
                        }
                    },
                    "success_metrics": {
                        "アプローチ成功率": "メール開封率30%以上、返信率10%以上を目標",
                        "電話成功率": "接続率40%、アポイント獲得率15%を目標"
                    }
                },
                "プレゼンテーション": {
                    "structure": {
                        "導入": "課題の確認と共感（3分）",
                        "現状分析": "現在の課題による影響の可視化（5分）",
                        "解決策提示": "具体的なソリューションと期待効果（10分）",
                        "事例紹介": "類似企業での成功事例（5分）",
                        "次のステップ": "具体的なアクションプランの提示（5分）",
                        "質疑応答": "懸念事項の解消（5-10分）"
                    },
                    "資料作成チェックリスト": [
                        "1スライド1メッセージの原則を守る",
                        "グラフや図表で視覚的に訴求",
                        "専門用語を避け、相手の言葉で話す",
                        "ROIや投資回収期間を明確に示す",
                        "競合との差別化ポイントを強調"
                    ]
                },
                "関係構築": {
                    "trust_building": [
                        "約束は必ず守る（時間、納期、内容）",
                        "小さな成功体験を積み重ねる",
                        "定期的な情報提供で接触頻度を保つ",
                        "相手の業界や会社について学び続ける",
                        "個人的な関心事も把握し、関係を深める"
                    ]
                }
            },
            "senior_examples": {
                "top_performer_practices": [
                    {
                        "name": "山田太郎（営業部3年目）",
                        "achievement": "新規開拓率150%達成",
                        "key_practices": [
                            "毎朝30分、ターゲット企業の最新ニュースをチェック",
                            "アプローチ前に必ず仮説を3つ以上準備",
                            "断られた理由を分析し、次回のアプローチに活かす",
                            "月1回、既存顧客にフォローアップの連絡"
                        ]
                    },
                    {
                        "name": "鈴木花子（営業部5年目）",
                        "achievement": "顧客満足度No.1、継続率95%",
                        "key_practices": [
                            "初回商談後24時間以内に必ずフォローアップ",
                            "顧客の業界トレンドを毎週レポートにまとめて共有",
                            "四半期に1度、利用状況のレビューミーティング実施",
                            "顧客の成功事例を社内外で積極的に発信"
                        ]
                    }
                ]
            },
            "common_challenges": {
                "緊張で頭が真っ白": {
                    "causes": ["準備不足", "完璧主義", "失敗への恐れ"],
                    "solutions": [
                        "想定問答集を作成し、繰り返し練習",
                        "深呼吸法：4秒吸って、7秒止めて、8秒で吐く",
                        "最初の3分間の話す内容を完全に暗記",
                        "「緊張しています」と正直に伝えることで楽になる",
                        "成功イメージを具体的に描いてから臨む"
                    ],
                    "prevention": [
                        "ロールプレイを最低3回は実施",
                        "録音して自分の話し方をチェック",
                        "先輩の商談に同席して観察学習",
                        "小さな成功体験を積み重ねて自信をつける"
                    ]
                },
                "断られることへの恐怖": {
                    "mindset_shift": [
                        "断られるのは製品であって、あなた個人ではない",
                        "「No」は「Not yet」（まだ）という意味",
                        "断られた数だけ成長できる",
                        "トップセールスも70%は断られている"
                    ],
                    "practical_tips": [
                        "断られた理由を必ず聞いて記録する",
                        "月間目標を「成約数」でなく「アプローチ数」で設定",
                        "断られた後の気持ちの切り替えルーティンを作る",
                        "チームで断られ体験を共有し、学びに変える"
                    ]
                }
            },
            "tools_and_resources": {
                "crm_tips": {
                    "入力ルール": [
                        "商談後30分以内に必ず更新",
                        "次のアクションを必ず記載",
                        "決裁者情報は詳細に記録",
                        "競合情報があれば必ず記載"
                    ]
                },
                "email_templates": {
                    "follow_up": "商談フォローアップ、資料送付、日程調整など",
                    "nurturing": "情報提供、事例紹介、セミナー案内など"
                }
            }
        }
    
    async def search_knowledge(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """ナレッジベースから関連情報を検索"""
        results = []
        query_lower = query.lower()
        
        # カテゴリが指定されている場合は、そのカテゴリのみ検索
        if category:
            if category in self.knowledge_base:
                results.extend(self._search_in_category(self.knowledge_base[category], query_lower, category))
        else:
            # 全カテゴリを検索
            for cat_name, cat_data in self.knowledge_base.items():
                results.extend(self._search_in_category(cat_data, query_lower, cat_name))
        
        # 関連度でソート（簡易的な実装）
        results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return results[:5]  # 上位5件を返す
    
    def _search_in_category(self, category_data: Any, query: str, category_name: str) -> List[Dict[str, Any]]:
        """カテゴリ内での検索"""
        results = []
        
        if isinstance(category_data, dict):
            for key, value in category_data.items():
                if self._contains_query(str(key), query) or self._contains_query(str(value), query):
                    results.append({
                        "category": category_name,
                        "type": key,
                        "content": value,
                        "relevance_score": self._calculate_relevance(str(key) + str(value), query)
                    })
        elif isinstance(category_data, list):
            for item in category_data:
                if self._contains_query(str(item), query):
                    results.append({
                        "category": category_name,
                        "content": item,
                        "relevance_score": self._calculate_relevance(str(item), query)
                    })
        
        return results
    
    def _contains_query(self, text: str, query: str) -> bool:
        """テキストにクエリが含まれるかチェック"""
        return query in text.lower()
    
    def _calculate_relevance(self, text: str, query: str) -> float:
        """関連度スコアを計算（簡易版）"""
        text_lower = text.lower()
        query_words = query.split()
        matches = sum(1 for word in query_words if word in text_lower)
        return matches / len(query_words) if query_words else 0
    
    async def get_template(self, template_type: str) -> Optional[Dict[str, Any]]:
        """特定のテンプレートを取得"""
        for category in self.knowledge_base.values():
            if isinstance(category, dict):
                for key, value in category.items():
                    if isinstance(value, dict) and "templates" in value:
                        if template_type in value["templates"]:
                            return value["templates"][template_type]
        return None
    
    async def get_best_practices(self, topic: str) -> List[Dict[str, Any]]:
        """特定トピックのベストプラクティスを取得"""
        practices = []
        
        if topic in self.knowledge_base.get("sales_best_practices", {}):
            practice_data = self.knowledge_base["sales_best_practices"][topic]
            practices.append({
                "topic": topic,
                "practices": practice_data,
                "source": "sales_best_practices"
            })
        
        # 先輩の事例も含める
        if "senior_examples" in self.knowledge_base:
            for performer in self.knowledge_base["senior_examples"].get("top_performer_practices", []):
                practices.append({
                    "topic": f"{performer['name']}の実践例",
                    "achievement": performer["achievement"],
                    "practices": performer["key_practices"],
                    "source": "senior_examples"
                })
        
        return practices
    
    async def get_solution_for_challenge(self, challenge: str) -> Optional[Dict[str, Any]]:
        """特定の課題に対する解決策を取得"""
        challenges = self.knowledge_base.get("common_challenges", {})
        
        # 完全一致を探す
        if challenge in challenges:
            return {
                "challenge": challenge,
                "solution": challenges[challenge],
                "type": "exact_match"
            }
        
        # 部分一致を探す
        for challenge_key, solution_data in challenges.items():
            if challenge.lower() in challenge_key.lower() or challenge_key.lower() in challenge.lower():
                return {
                    "challenge": challenge_key,
                    "solution": solution_data,
                    "type": "partial_match"
                }
        
        return None
    
    async def get_company_values(self) -> Dict[str, Any]:
        """会社のミッション・ビジョン・バリューを取得"""
        return self.knowledge_base.get("company_info", {})
    
    async def add_knowledge(self, category: str, key: str, content: Any) -> bool:
        """新しいナレッジを追加（将来の拡張用）"""
        if category not in self.knowledge_base:
            self.knowledge_base[category] = {}
        
        if isinstance(self.knowledge_base[category], dict):
            self.knowledge_base[category][key] = content
            return True
        
        return False