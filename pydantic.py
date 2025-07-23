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


# Convert JSON to EXCEL

import polars as pl
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd

def convert_ghg_json_to_excel(
    json_data: List[Dict[str, Any]], 
    output_path: str = "ghg_extraction_results.xlsx"
) -> pl.DataFrame:
    """
    GHG抽出結果のJSONデータをPolarsデータフレームに変換し、Excelファイルとして出力
    
    Args:
        json_data: GHGExtractionResultのリスト（JSON形式）
        output_path: 出力するExcelファイルのパス
    
    Returns:
        pl.DataFrame: 変換されたPolarsデータフレーム
    """
    
    # データを格納するリスト
    rows = []
    
    for company_data in json_data:
        company_name = company_data.get('company_name', '')
        report_year = company_data.get('report_year')
        extraction_notes = company_data.get('extraction_notes', '')
        
        for scope_data in company_data.get('scope_data', []):
            scope_pattern = scope_data.get('scope_pattern', '')
            
            # 基本情報の行データ
            base_row = {
                'company_name': company_name,
                'report_year': report_year,
                'scope_pattern': scope_pattern,
                'extraction_notes': extraction_notes,
            }
            
            # 第三者認証・検証情報
            verification = scope_data.get('third_party_verification', {})
            if verification:
                base_row.update({
                    'is_verified': verification.get('is_verified', False),
                    'verification_organization': verification.get('verification_organization', ''),
                    'verification_standard': verification.get('verification_standard', ''),
                    'verification_evidence': verification.get('evidence', '')
                })
            else:
                base_row.update({
                    'is_verified': False,
                    'verification_organization': '',
                    'verification_standard': '',
                    'verification_evidence': ''
                })
            
            # GHG排出量データ
            emissions = scope_data.get('emissions', [])
            if emissions:
                for emission in emissions:
                    row = base_row.copy()
                    row.update({
                        'data_type': 'emission',
                        'amount': emission.get('amount'),
                        'unit': emission.get('unit', ''),
                        'year': emission.get('year'),
                        'scope3_categories': _format_categories(emission.get('scope3_categories', [])),
                        'evidence': emission.get('evidence', ''),
                        # 他の項目は空に設定
                        'reduction_rate': None,
                        'reduction_amount': None,
                        'reduction_unit': '',
                        'baseline_year': None,
                        'achievement_year': None,
                        'target_year': None,
                        'is_increase': False,
                        'target_rate': None,
                        'is_carbon_neutral': False
                    })
                    rows.append(row)
            
            # 削減実績データ
            reduction_results = scope_data.get('reduction_results', [])
            if reduction_results:
                for result in reduction_results:
                    row = base_row.copy()
                    row.update({
                        'data_type': 'reduction_result',
                        'reduction_rate': result.get('reduction_rate'),
                        'reduction_amount': result.get('reduction_amount'),
                        'reduction_unit': result.get('reduction_unit', ''),
                        'baseline_year': result.get('baseline_year'),
                        'achievement_year': result.get('achievement_year'),
                        'scope3_categories': _format_categories(result.get('scope3_categories', [])),
                        'is_increase': result.get('is_increase', False),
                        'evidence': result.get('evidence', ''),
                        # 他の項目は空に設定
                        'amount': None,
                        'unit': '',
                        'year': None,
                        'target_year': None,
                        'target_rate': None,
                        'is_carbon_neutral': False
                    })
                    rows.append(row)
            
            # 削減目標データ
            reduction_targets = scope_data.get('reduction_targets', [])
            if reduction_targets:
                for target in reduction_targets:
                    row = base_row.copy()
                    row.update({
                        'data_type': 'reduction_target',
                        'target_rate': target.get('target_rate'),
                        'baseline_year': target.get('baseline_year'),
                        'target_year': target.get('target_year'),
                        'scope3_categories': _format_categories(target.get('scope3_categories', [])),
                        'is_carbon_neutral': target.get('is_carbon_neutral', False),
                        'evidence': target.get('evidence', ''),
                        # 他の項目は空に設定
                        'amount': None,
                        'unit': '',
                        'year': None,
                        'reduction_rate': None,
                        'reduction_amount': None,
                        'reduction_unit': '',
                        'achievement_year': None,
                        'is_increase': False
                    })
                    rows.append(row)
            
            # データが何もない場合は基本情報のみの行を追加
            if not emissions and not reduction_results and not reduction_targets:
                row = base_row.copy()
                row.update({
                    'data_type': 'no_data',
                    'amount': None,
                    'unit': '',
                    'year': None,
                    'scope3_categories': '',
                    'evidence': '',
                    'reduction_rate': None,
                    'reduction_amount': None,
                    'reduction_unit': '',
                    'baseline_year': None,
                    'achievement_year': None,
                    'target_year': None,
                    'is_increase': False,
                    'target_rate': None,
                    'is_carbon_neutral': False
                })
                rows.append(row)
    
    # Polarsデータフレームを作成
    if not rows:
        # 空のデータフレームを作成
        df = pl.DataFrame(schema=_get_schema())
    else:
        df = pl.DataFrame(rows)
    
    # Excel出力用にPandasに変換（Polarsが直接Excel出力をサポートしていないため）
    pandas_df = df.to_pandas()
    
    # Excelファイルに出力
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        pandas_df.to_excel(writer, sheet_name='GHG_Data', index=False)
        
        # ワークシートの書式設定
        worksheet = writer.sheets['GHG_Data']
        
        # 列幅の自動調整
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)  # 最大50文字に制限
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    print(f"Excel ファイルが生成されました: {output_path}")
    print(f"総行数: {len(df)}")
    print(f"企業数: {df['company_name'].n_unique()}")
    
    return df

def _format_categories(categories: List[str]) -> str:
    """スコープ3カテゴリリストを文字列に変換"""
    if not categories:
        return ''
    return '; '.join(categories)

def _get_schema() -> Dict[str, pl.DataType]:
    """データフレームのスキーマを定義"""
    return {
        'company_name': pl.Utf8,
        'report_year': pl.Int64,
        'scope_pattern': pl.Utf8,
        'data_type': pl.Utf8,
        'extraction_notes': pl.Utf8,
        'is_verified': pl.Boolean,
        'verification_organization': pl.Utf8,
        'verification_standard': pl.Utf8,
        'verification_evidence': pl.Utf8,
        'amount': pl.Float64,
        'unit': pl.Utf8,
        'year': pl.Int64,
        'scope3_categories': pl.Utf8,
        'evidence': pl.Utf8,
        'reduction_rate': pl.Float64,
        'reduction_amount': pl.Float64,
        'reduction_unit': pl.Utf8,
        'baseline_year': pl.Int64,
        'achievement_year': pl.Int64,
        'target_year': pl.Int64,
        'is_increase': pl.Boolean,
        'target_rate': pl.Float64,
        'is_carbon_neutral': pl.Boolean
    }

def load_and_convert_from_file(json_file_path: str, output_path: str = None) -> pl.DataFrame:
    """
    JSONファイルからデータを読み込んでExcelに変換
    
    Args:
        json_file_path: 入力JSONファイルのパス
        output_path: 出力Excelファイルのパス（Noneの場合は自動生成）
    
    Returns:
        pl.DataFrame: 変換されたPolarsデータフレーム
    """
    if output_path is None:
        output_path = Path(json_file_path).stem + "_converted.xlsx"
    
    with open(json_file_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # 単一のオブジェクトの場合はリストに変換
    if isinstance(json_data, dict):
        json_data = [json_data]
    
    return convert_ghg_json_to_excel(json_data, output_path)

# 使用例
if __name__ == "__main__":
    # サンプルデータ
    sample_data = [
        {
            "company_name": "三菱商事",
            "report_year": 2023,
            "scope_data": [
                {
                    "scope_pattern": "スコープ1",
                    "emissions": [
                        {
                            "amount": 1234.5,
                            "unit": "t-CO2",
                            "year": 2023,
                            "scope3_categories": [],
                            "evidence": "当社のスコープ1排出量は1,234.5t-CO2でした。"
                        }
                    ],
                    "reduction_results": [
                        {
                            "reduction_rate": 15.0,
                            "baseline_year": 2020,
                            "achievement_year": 2023,
                            "scope3_categories": [],
                            "is_increase": False,
                            "evidence": "2020年比で15%の削減を達成しました。"
                        }
                    ],
                    "reduction_targets": [
                        {
                            "target_rate": 30.0,
                            "baseline_year": 2020,
                            "target_year": 2030,
                            "scope3_categories": [],
                            "is_carbon_neutral": False,
                            "evidence": "2030年までに2020年比30%削減を目指します。"
                        }
                    ],
                    "third_party_verification": {
                        "is_verified": True,
                        "verification_organization": "第三者認証機関A",
                        "verification_standard": "ISO14064",
                        "evidence": "第三者認証機関Aによる検証を受けています。"
                    }
                },
                {
                    "scope_pattern": "スコープ2",
                    "emissions": [
                        {
                            "amount": 2345.6,
                            "unit": "t-CO2",
                            "year": 2023,
                            "scope3_categories": [],
                            "evidence": "スコープ2排出量は2,345.6t-CO2でした。"
                        }
                    ],
                    "reduction_results": [],
                    "reduction_targets": [],
                    "third_party_verification": None
                }
            ],
            "extraction_notes": "全データ抽出完了"
        }
    ]
    
    # 変換実行
    df = convert_ghg_json_to_excel(sample_data, "sample_ghg_data.xlsx")
    print("\nデータフレームの先頭5行:")
    print(df.head())