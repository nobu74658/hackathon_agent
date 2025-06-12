# User Experience Sharing Issue Analysis and Fix

## Problem Description

The AI system was incorrectly treating user's own experiences as requests for knowledge. Specifically:

### User Examples That Were Misinterpreted:

1. **User sharing IT service proposal experience:**
   ```
   "例えば、初心者のお客様向けにITサービスを紹介する資料では、専門用語を避け、課題→解決策→効果の順に構成し、身近な例を用いて説明しました。"
   ```

2. **User sharing presentation experience:**
   ```
   "「結論→理由→具体例」の順でスライドを構成し、1スライド1メッセージを守ったことで、相手に内容がスムーズに伝わりました。図やアイコンを使って視覚的に整理した点も効果的でした。"
   ```

These were clearly the user sharing their own work experiences, not requesting knowledge from the AI.

## Root Cause Analysis

The issue was in the `_check_for_specific_user_request` method in `/backend/app/services/dialogue_manager.py`. 

### Problems with Original Implementation:

1. **Overly broad pattern matching:**
   ```python
   request_patterns = {
       "example_request": ["例を", "具体例", "サンプル", "実例", "作成して", "見せて", "教えて"],
       # ... other patterns
   }
   ```

2. **Keywords that appeared in experience sharing:**
   - "例" (example) - triggered by "例えば" (for example) when users shared examples
   - "具体例" (specific example) - triggered when users said "具体例を挙げると" (giving a specific example)
   - "作成して" (create) - triggered by "作成しました" (I created) when sharing past work

3. **Insufficient context awareness:**
   - The system didn't distinguish between "例を教えて" (show me an example) vs "例えば私は" (for example, I...)
   - Past tense vs. imperative forms weren't properly distinguished

## Solution Implemented

### 1. Enhanced Pattern Detection

Added explicit experience sharing pattern detection:

```python
# Check for experience sharing patterns first
experience_sharing_patterns = [
    "例えば、", "具体的には、", "実際に", "これまでに", "過去に", 
    "した", "ました", "でした", "していた", "作成しました",
    "構成し", "用いて", "守った", "効果的でした", "スライド", "図や"
]

# If user is sharing experience, it's NOT a request
if any(pattern in user_response for pattern in experience_sharing_patterns):
    return None
```

### 2. More Specific Request Patterns

Made request patterns more specific and explicit:

```python
request_patterns = {
    "example_request": ["例を教えて", "例を見せて", "具体例をください", "サンプルをください", "実例が欲しい"],
    "template_request": ["テンプレートを", "フォーマットを", "ひな形を", "様式を"],
    "reference_request": ["参考資料を", "お手本を", "見本を", "良い例を教えて"],
    "knowledge_request": ["ナレッジを", "資料をください", "ドキュメントを", "先輩の例を", "社内の例を"]
}
```

### 3. Improved LLM Analysis

Enhanced the LLM prompt to better distinguish between experience sharing and requests:

```python
【重要な判定基準】:
1. 新人が自分の経験や体験を共有している場合 → 要求ではない
   例: "例えば、私は〜しました", "実際に〜を作成しました"
   
2. 新人が具体的な資料や例を求めている場合 → 要求である
   例: "例を教えてください", "テンプレートをください"

特に「例えば」「具体的には」「実際に」で始まる文は、通常は経験共有であり要求ではありません。
```

### 4. Higher Confidence Threshold

Increased the confidence threshold from 0.6 to 0.7 to reduce false positives:

```python
# Only process as request if confidence is high
if result.get("has_request", False) and result.get("confidence", 0) > 0.7:
    # Process as request
```

## Testing Results

All test cases now pass correctly:

- ✅ User sharing IT service experience → NOT treated as request
- ✅ User sharing presentation experience → NOT treated as request  
- ✅ Actual requests for examples → Properly handled as requests
- ✅ Actual requests for templates → Properly handled as requests
- ✅ User questions → NOT treated as requests

## Files Modified

1. `/backend/app/services/dialogue_manager.py`
   - Updated `_check_for_specific_user_request` method
   - Added experience sharing detection
   - Improved request pattern matching
   - Enhanced LLM prompt for better analysis

## Impact

This fix ensures that:
1. Users can share their experiences naturally without triggering unwanted knowledge provision
2. The dialogue flow continues smoothly when users provide their own examples
3. Actual requests for knowledge are still properly handled
4. The AI focuses on the user's actual needs rather than misinterpreting their responses

The system now correctly distinguishes between:
- **Experience sharing**: "例えば、私は〜しました" → Continue dialogue
- **Knowledge requests**: "例を教えてください" → Provide knowledge
- **Questions**: "どうすればいいですか？" → Continue dialogue