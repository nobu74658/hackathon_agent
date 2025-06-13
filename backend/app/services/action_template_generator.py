"""
アクションテンプレート生成サービス
具体的で実行可能なアクションテンプレートを生成
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

class ActionTemplateGenerator:
    """アクションプランのテンプレートを生成するサービス"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[str, Any]:
        """アクションテンプレートの初期化"""
        return {
            "新規開拓": {
                "email_campaign": {
                    "title": "ターゲット企業へのメールアプローチキャンペーン",
                    "description": "体系的なメールアプローチで新規顧客を開拓",
                    "steps": [
                        {
                            "step": 1,
                            "action": "ターゲットリスト作成",
                            "details": "業界、規模、地域でセグメント化した50社のリストを作成",
                            "deliverable": "Excel形式のターゲットリスト（企業名、担当者名、連絡先、選定理由）",
                            "duration": "2日",
                            "success_criteria": "決裁者または影響力のある担当者の連絡先が80%以上判明"
                        },
                        {
                            "step": 2,
                            "action": "パーソナライズドメール作成",
                            "details": "各企業の課題や最新ニュースを調査し、カスタマイズしたメールを作成",
                            "template": "email_template_001",
                            "duration": "3日",
                            "success_criteria": "全ターゲットに対して個別化されたメールが完成"
                        },
                        {
                            "step": 3,
                            "action": "A/Bテスト実施",
                            "details": "件名と本文の異なるバージョンでテストを実施",
                            "duration": "1週間",
                            "metrics": ["開封率", "返信率", "アポイント獲得率"],
                            "success_criteria": "開封率30%以上、返信率10%以上"
                        },
                        {
                            "step": 4,
                            "action": "フォローアップ",
                            "details": "未返信の企業に対して、異なるアプローチで再度連絡",
                            "duration": "1週間",
                            "success_criteria": "初回と合わせて返信率15%以上達成"
                        }
                    ],
                    "tools_required": ["CRM", "メール配信ツール", "企業データベース"],
                    "expected_outcome": "50社中7-8社（15%）からのアポイント獲得",
                    "time_investment": "合計3週間（1日2時間）"
                },
                "social_selling": {
                    "title": "LinkedInを活用したソーシャルセリング",
                    "description": "SNSを使った現代的なアプローチ手法",
                    "steps": [
                        {
                            "step": 1,
                            "action": "プロフィール最適化",
                            "details": "顧客視点でのプロフィール作成、実績や価値提案を明確化",
                            "duration": "1日",
                            "checklist": [
                                "プロフェッショナルな写真",
                                "キャッチーなヘッドライン",
                                "具体的な実績数値",
                                "顧客の声や推薦"
                            ]
                        },
                        {
                            "step": 2,
                            "action": "ターゲットとのつながり構築",
                            "details": "週10人のペースで関連性の高い人物とつながる",
                            "duration": "継続的（週2時間）",
                            "success_criteria": "月40人の新規コネクション"
                        },
                        {
                            "step": 3,
                            "action": "価値あるコンテンツ共有",
                            "details": "業界インサイトや成功事例を週2回投稿",
                            "duration": "継続的（週3時間）",
                            "content_ideas": [
                                "業界トレンド分析",
                                "顧客成功事例",
                                "問題解決のヒント",
                                "イベントレポート"
                            ]
                        }
                    ]
                }
            },
            "プレゼンテーション改善": {
                "presentation_mastery": {
                    "title": "プレゼンテーション力向上プログラム",
                    "description": "体系的なトレーニングで商談成功率を向上",
                    "steps": [
                        {
                            "step": 1,
                            "action": "現状分析と録画",
                            "details": "現在のプレゼンを録画し、改善点を特定",
                            "duration": "1日",
                            "evaluation_criteria": [
                                "話すスピードと間の取り方",
                                "ボディランゲージ",
                                "資料の見やすさ",
                                "論理構成"
                            ]
                        },
                        {
                            "step": 2,
                            "action": "ストーリーテリング技術習得",
                            "details": "STAR法（Situation, Task, Action, Result）でストーリーを構築",
                            "practice_topics": [
                                "顧客の課題提起（2分）",
                                "解決策の提示（3分）",
                                "成功事例の紹介（2分）",
                                "次のステップ提案（1分）"
                            ],
                            "duration": "1週間（毎日30分練習）"
                        },
                        {
                            "step": 3,
                            "action": "ロールプレイ実践",
                            "details": "先輩や同僚とのロールプレイで実践練習",
                            "scenarios": [
                                "初回商談（関心喚起）",
                                "詳細説明（機能・価値）",
                                "反論処理（価格、競合）",
                                "クロージング"
                            ],
                            "duration": "2週間（週3回、各1時間）"
                        },
                        {
                            "step": 4,
                            "action": "フィードバック改善サイクル",
                            "details": "実際の商談後に振り返りと改善",
                            "duration": "継続的",
                            "tracking_metrics": [
                                "商談時間",
                                "質問された回数",
                                "次回アポ獲得率",
                                "成約率"
                            ]
                        }
                    ]
                }
            },
            "緊張対策": {
                "confidence_building": {
                    "title": "商談での緊張克服プログラム",
                    "description": "段階的なアプローチで自信を構築",
                    "steps": [
                        {
                            "step": 1,
                            "action": "マインドフルネス導入",
                            "details": "毎朝5分の瞑想で心を整える習慣作り",
                            "techniques": [
                                "4-7-8呼吸法（朝晩実施）",
                                "ボディスキャン瞑想",
                                "ポジティブアファメーション"
                            ],
                            "duration": "2週間"
                        },
                        {
                            "step": 2,
                            "action": "段階的露出療法",
                            "details": "小さな成功体験から始めて徐々にレベルアップ",
                            "stages": [
                                "社内での5分プレゼン",
                                "既存顧客への新機能紹介",
                                "新規顧客への初回アプローチ",
                                "重要商談でのプレゼン"
                            ],
                            "duration": "1ヶ月"
                        },
                        {
                            "step": 3,
                            "action": "事前準備チェックリスト作成",
                            "details": "商談前の準備を体系化して不安を軽減",
                            "checklist": [
                                "想定質問と回答（最低10個）",
                                "相手企業の最新情報確認",
                                "商談のゴール設定",
                                "最初の3分間の台詞暗記",
                                "リラックスルーティン実施"
                            ],
                            "duration": "各商談前1時間"
                        }
                    ]
                }
            },
            "関係構築": {
                "trust_acceleration": {
                    "title": "顧客との信頼関係構築プログラム",
                    "description": "体系的なアプローチで強固な関係を構築",
                    "steps": [
                        {
                            "step": 1,
                            "action": "顧客理解シート作成",
                            "details": "各顧客の詳細情報を体系的に整理",
                            "information_categories": [
                                "ビジネス情報（業界、競合、課題）",
                                "個人情報（趣味、家族、キャリア）",
                                "コミュニケーション嗜好",
                                "意思決定プロセス"
                            ],
                            "duration": "継続的更新"
                        },
                        {
                            "step": 2,
                            "action": "定期接触プログラム",
                            "details": "価値ある情報提供で接触頻度を維持",
                            "touch_points": [
                                "月1回：業界レポート送付",
                                "四半期1回：利用状況レビュー",
                                "随時：関連ニュース共有",
                                "年2回：会食またはイベント招待"
                            ],
                            "duration": "継続的"
                        },
                        {
                            "step": 3,
                            "action": "アドバイザーポジション確立",
                            "details": "単なる営業から信頼されるアドバイザーへ",
                            "activities": [
                                "競合情報の提供",
                                "業界トレンド分析",
                                "他社成功事例の共有",
                                "戦略的アドバイス"
                            ]
                        }
                    ]
                }
            }
        }
    
    async def generate_action_plan(
        self,
        challenge: str,
        context: Dict[str, Any],
        timeline: str = "1ヶ月"
    ) -> Dict[str, Any]:
        """課題に応じたアクションプランを生成"""
        
        # 課題に最も適したテンプレートを選択
        selected_templates = []
        
        # キーワードマッチングで関連テンプレートを探す
        keywords = {
            "新規": ["新規開拓"],
            "開拓": ["新規開拓"],
            "アポ": ["新規開拓"],
            "プレゼン": ["プレゼンテーション改善"],
            "緊張": ["緊張対策"],
            "頭が真っ白": ["緊張対策"],
            "関係": ["関係構築"],
            "信頼": ["関係構築"]
        }
        
        challenge_lower = challenge.lower()
        for keyword, categories in keywords.items():
            if keyword in challenge_lower:
                for category in categories:
                    if category in self.templates:
                        selected_templates.extend([
                            {
                                "category": category,
                                "template_name": template_name,
                                "template": template_data
                            }
                            for template_name, template_data in self.templates[category].items()
                        ])
        
        # デフォルトテンプレートも追加
        if not selected_templates and "新規開拓" in self.templates:
            selected_templates.append({
                "category": "新規開拓",
                "template_name": "email_campaign",
                "template": self.templates["新規開拓"]["email_campaign"]
            })
        
        # タイムラインに基づいて調整
        timeline_days = self._parse_timeline(timeline)
        
        # アクションプランを構築
        action_plan = {
            "challenge": challenge,
            "timeline": timeline,
            "total_duration_days": timeline_days,
            "action_items": [],
            "templates_used": [],
            "success_metrics": {},
            "required_resources": set(),
            "estimated_time_investment": 0
        }
        
        # 選択されたテンプレートからアクションアイテムを生成
        action_id = 1
        for template_info in selected_templates[:2]:  # 最大2つのテンプレートを使用
            template = template_info["template"]
            action_plan["templates_used"].append({
                "category": template_info["category"],
                "name": template_info["template_name"],
                "title": template["title"]
            })
            
            # 各ステップをアクションアイテムに変換
            for step in template.get("steps", []):
                action_item = {
                    "id": f"action_{action_id}",
                    "title": step["action"],
                    "description": step["details"],
                    "priority": "high" if step["step"] <= 2 else "medium",
                    "duration": step.get("duration", "1週間"),
                    "deliverables": step.get("deliverable", step.get("checklist", [])),
                    "success_criteria": step.get("success_criteria", ""),
                    "category": template_info["category"],
                    "template_reference": template_info["template_name"]
                }
                
                # 期限を計算
                if action_id == 1:
                    action_item["due_date"] = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
                else:
                    action_item["due_date"] = (datetime.now() + timedelta(days=7 * action_id)).strftime("%Y-%m-%d")
                
                action_plan["action_items"].append(action_item)
                action_id += 1
            
            # 必要なリソースを追加
            if "tools_required" in template:
                action_plan["required_resources"].update(template["tools_required"])
            
            # 成功指標を追加
            if "expected_outcome" in template:
                action_plan["success_metrics"][template_info["template_name"]] = template["expected_outcome"]
        
        # リソースをリストに変換
        action_plan["required_resources"] = list(action_plan["required_resources"])
        
        # コンテキストに基づいてカスタマイズ
        action_plan = self._customize_plan_for_context(action_plan, context)
        
        return action_plan
    
    def _parse_timeline(self, timeline: str) -> int:
        """タイムラインを日数に変換"""
        if "週間" in timeline:
            weeks = int(timeline.replace("週間", "").strip())
            return weeks * 7
        elif "ヶ月" in timeline or "か月" in timeline:
            months = int(timeline.replace("ヶ月", "").replace("か月", "").strip())
            return months * 30
        else:
            return 30  # デフォルト1ヶ月
    
    def _customize_plan_for_context(
        self,
        action_plan: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """コンテキストに基づいてプランをカスタマイズ"""
        
        # 経験年数に基づいて調整
        experience_years = context.get("experience_years", 1)
        if experience_years < 1:
            # 新人の場合は基礎的なアクションを追加
            basic_action = {
                "id": "action_0",
                "title": "基礎スキル習得",
                "description": "営業の基本を学ぶためのオリエンテーション参加",
                "priority": "high",
                "duration": "1週間",
                "due_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
                "category": "基礎教育"
            }
            action_plan["action_items"].insert(0, basic_action)
        
        # 部署に基づいて調整
        department = context.get("department", "")
        if "新規開拓" in department:
            action_plan["focus_area"] = "新規顧客獲得"
        elif "既存" in department:
            action_plan["focus_area"] = "顧客関係深化"
        
        return action_plan
    
    async def get_template_details(
        self,
        category: str,
        template_name: str
    ) -> Optional[Dict[str, Any]]:
        """特定のテンプレートの詳細を取得"""
        if category in self.templates and template_name in self.templates[category]:
            return self.templates[category][template_name]
        return None
    
    async def list_available_templates(self) -> Dict[str, List[str]]:
        """利用可能なテンプレートのリストを取得"""
        available = {}
        for category, templates in self.templates.items():
            available[category] = [
                {
                    "name": template_name,
                    "title": template_data.get("title", ""),
                    "description": template_data.get("description", "")
                }
                for template_name, template_data in templates.items()
            ]
        return available