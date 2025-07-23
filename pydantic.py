from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum

class ScopePattern(str, Enum):
    SCOPE_1 = "スコープ1"
    SCOPE_2 = "スコープ2"
    SCOPE_3 = "スコープ3"
    SCOPE_1_2 = "スコープ1+2"
    SCOPE_1_2_3 = "スコープ1+2+3"

class Scope3Category(str, Enum):
    CATEGORY_1 = "カテゴリ1: 購入した製品・サービス"
    CATEGORY_2 = "カテゴリ2: 資本財"
    CATEGORY_3 = "カテゴリ3: スコープ1,2に含まれない燃料及びエネルギー関連活動"
    CATEGORY_4 = "カテゴリ4: 輸送、配送（上流）"
    CATEGORY_5 = "カテゴリ5: 事業から出る廃棄物"
    CATEGORY_6 = "カテゴリ6: 出張"
    CATEGORY_7 = "カテゴリ7: 雇用者の通勤"
    CATEGORY_8 = "カテゴリ8: リース資産（上流）"
    CATEGORY_9 = "カテゴリ9: 輸送、配送（下流）"
    CATEGORY_10 = "カテゴリ10: 販売した製品の加工"
    CATEGORY_11 = "カテゴリ11: 販売した製品の使用"
    CATEGORY_12 = "カテゴリ12: 販売した製品の廃棄"
    CATEGORY_13 = "カテゴリ13: リース資産（下流）"
    CATEGORY_14 = "カテゴリ14: フランチャイズ"
    CATEGORY_15 = "カテゴリ15: 投資"

class GHGEmission(BaseModel):
    """GHG排出量データ"""
    amount: Optional[float] = Field(None, description="排出量（数値）")
    unit: Optional[str] = Field(None, description="単位（例：t-CO2、千t-CO2等）")
    year: Optional[int] = Field(None, description="対象年度")
    scope3_categories: List[Scope3Category] = Field(default_factory=list, description="スコープ3の場合の該当カテゴリリスト")
    evidence: str = Field(..., description="抽出根拠となる本文の抜粋")

class ReductionResult(BaseModel):
    """削減実績データ（増加の場合は負の値）"""
    reduction_rate: Optional[float] = Field(None, description="削減率（%）、増加の場合は負の値")
    reduction_amount: Optional[float] = Field(None, description="削減量、増加の場合は負の値")
    reduction_unit: Optional[str] = Field(None, description="削減量の単位")
    baseline_year: Optional[int] = Field(None, description="基準年")
    achievement_year: Optional[int] = Field(None, description="達成年")
    scope3_categories: List[Scope3Category] = Field(default_factory=list, description="スコープ3の場合の該当カテゴリリスト")
    is_increase: bool = Field(False, description="排出量が増加した場合はTrue")
    evidence: str = Field(..., description="抽出根拠となる本文の抜粋")

class ReductionTarget(BaseModel):
    """削減目標データ"""
    target_rate: Optional[float] = Field(None, description="目標削減率（%）、カーボンニュートラル・ネットゼロは100%")
    baseline_year: Optional[int] = Field(None, description="基準年")
    target_year: Optional[int] = Field(None, description="目標年")
    scope3_categories: List[Scope3Category] = Field(default_factory=list, description="スコープ3の場合の該当カテゴリリスト")
    is_carbon_neutral: bool = Field(False, description="カーボンニュートラル・ネットゼロ目標かどうか")
    evidence: str = Field(..., description="抽出根拠となる本文の抜粋")

class ThirdPartyVerification(BaseModel):
    """第三者認証・検証情報"""
    is_verified: bool = Field(False, description="第三者による認証・検証を受けているかどうか")
    verification_organization: Optional[str] = Field(None, description="認証・検証機関名")
    verification_standard: Optional[str] = Field(None, description="認証・検証基準")
    evidence: Optional[str] = Field(None, description="抽出根拠となる本文の抜粋")

class ScopeData(BaseModel):
    """スコープ別データ"""
    scope_pattern: ScopePattern = Field(..., description="スコープパターン")
    emissions: List[GHGEmission] = Field(default_factory=list, description="排出量データのリスト")
    reduction_results: List[ReductionResult] = Field(default_factory=list, description="削減実績データのリスト")
    reduction_targets: List[ReductionTarget] = Field(default_factory=list, description="削減目標データのリスト")
    third_party_verification: Optional[ThirdPartyVerification] = Field(None, description="第三者認証・検証情報")

class GHGExtractionResult(BaseModel):
    """GHG情報抽出結果"""
    company_name: Optional[str] = Field(None, description="企業名")
    report_year: Optional[int] = Field(None, description="報告書年度")
    scope_data: List[ScopeData] = Field(default_factory=list, description="スコープ別データのリスト")
    extraction_notes: Optional[str] = Field(None, description="抽出に関する補足事項")


# 有価証券報告書からのGHG情報抽出プロンプト

## 指示
あなたは日本上場企業の有価証券報告書の「サステナビリティに関する考え方及び取組」の章からGHG（温室効果ガス）関連情報を抽出する専門家です。以下の要件に従って、正確かつ構造化された情報抽出を行ってください。

## 抽出対象と要件

### 1. スコープパターンの識別
文書を分析し、以下の5つのスコープパターンのうち、該当するものを特定してください：
- **スコープ1**: 直接排出（自社の燃料使用等）
- **スコープ2**: 間接排出（購入電力等）
- **スコープ3**: その他の間接排出（サプライチェーン等）
- **スコープ1+2**: スコープ1と2の合計
- **スコープ1+2+3**: 全スコープの合計

### 2. 抽出項目
各スコープパターンについて以下の3つの主要項目を抽出してください：

#### A. GHG排出量
- **排出量**: 具体的な数値とその単位（t-CO2、千t-CO2等）
- **対象年度**: その排出量がいつのものか
- **スコープ3カテゴリ**: スコープ3の場合、該当するカテゴリリスト（複数の場合は全て抽出）
- **抽出根拠**: 本文からの直接引用

#### B. 削減実績
- **削減率または削減量**: パーセンテージまたは具体的な削減量と単位
  - **重要**: 排出量が増加している場合は負の値で表現（例：-15%は15%増加）
- **基準年**: 削減の基準となる年
- **達成年**: 削減を達成した年
- **スコープ3カテゴリ**: 該当するカテゴリリスト（複数の場合は全て抽出）
- **増加フラグ**: 排出量が増加した場合の判定
- **抽出根拠**: 本文からの直接引用

#### C. 削減目標
- **目標率**: 削減目標のパーセンテージ
  - カーボンニュートラル・ネットゼロ等の場合は100%として扱う
- **基準年**: 目標設定の基準となる年
- **目標年**: 目標達成予定年
- **スコープ3カテゴリ**: 該当するカテゴリリスト（複数の場合は全て抽出）
- **カーボンニュートラル判定**: CN/ネットゼロ宣言かどうか
- **抽出根拠**: 本文からの直接引用（カーボンニュートラル・ネットゼロの記載を含む）

### 3. 第三者認証・検証の判定
GHG排出量や削減実績について、第三者による認証・検証を受けているかを判定し、以下を抽出してください：
- 認証・検証の有無
- 認証・検証機関名（判明する場合）
- 認証・検証基準（判明する場合）
- 抽出根拠

## 重要な注意事項

### 数値の取り扱い
- 数値は正確に抽出し、概算や推定値の場合はその旨を記録
- 単位は必ず記載（t-CO2、千t-CO2、万t-CO2等）
- 範囲で示されている場合は適切に処理

### 年度の取り扱い
- 年度表記（例：2023年度、令和5年度）は西暦年で統一
- 年度末の場合は適切に判断（例：2023年度→2023年）

### スコープ3カテゴリ
カテゴリが明記されている場合は以下の標準分類リストから該当するものを選択：
- **カテゴリ1**: 購入した製品・サービス
- **カテゴリ2**: 資本財
- **カテゴリ3**: スコープ1,2に含まれない燃料及びエネルギー関連活動
- **カテゴリ4**: 輸送、配送（上流）
- **カテゴリ5**: 事業から出る廃棄物
- **カテゴリ6**: 出張
- **カテゴリ7**: 雇用者の通勤
- **カテゴリ8**: リース資産（上流）
- **カテゴリ9**: 輸送、配送（下流）
- **カテゴリ10**: 販売した製品の加工
- **カテゴリ11**: 販売した製品の使用
- **カテゴリ12**: 販売した製品の廃棄
- **カテゴリ13**: リース資産（下流）
- **カテゴリ14**: フランチャイズ
- **カテゴリ15**: 投資

**重要**: 複数のカテゴリが言及されている場合は、該当する全てのカテゴリをリスト形式で抽出してください。

### 削減率の取り扱い
- **削減の場合**: 正の値（例：15%削減 → 15）
- **増加の場合**: 負の値（例：10%増加 → -10）
- **増加フラグ**: 排出量が増加した場合は`is_increase: true`を設定

### 抽出根拠の記載
- 必ず元文書からの直接引用を含める
- 引用は情報の信頼性を担保するのに十分な長さとする
- 複数箇所からの情報は適切に組み合わせて記載

## 出力形式
JSON形式で出力し、提供されたPydanticスキーマに完全に準拠してください。データが存在しない項目はnullまたは空リストとしてください。

## 品質基準
- **完全性**: 文書内の全てのGHG関連情報を漏れなく抽出
- **正確性**: 数値、年度、分類を正確に抽出
- **一貫性**: 同一企業内での情報の整合性を確保
- **検証可能性**: 抽出根拠により第三者が検証可能

---

**入力文書**: [ここに「サステナビリティに関する考え方及び取組」の章の内容を貼り付け]

上記の文書から、指定されたJSON形式でGHG関連情報を抽出してください。