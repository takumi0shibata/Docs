了解です。以下に「そのまま使える抽出プロンプト（日本語）」と「Pydanticスキーマ（Python）」を用意しました。
テキストは1本の.txtで、表はCSV文字列として本文に埋め込まれている想定です。抽出の“完全性・網羅性”を最優先し、重複や曖昧さも失わない設計にしています（証拠断片・文字位置も保持）。

---

# 抽出プロンプト（LLM用・日本語）

あなたは日本の有価証券報告書（サステナビリティ章）の温室効果ガス（GHG）関連開示から、指定スキーマに沿って**網羅的**に情報を抽出するシステムです。
入力は**プレーンテキスト（.txt）**で、表は**CSV形式の文字列**で本文中に埋め込まれています（ページ情報はありません）。
**出力は必ず有効なJSON**で、指定のPydanticスキーマに一致させてください。自由記述や説明文、推論過程は**一切出力しない**でください。

## 抽出範囲（網羅）

1. **開示スコープパターン**：以下のいずれかの項目が本文に出現したら、**出現した分すべて**を列挙してください（同一文書内に複数パターンが併存する場合があります）。

* `SCOPE1`（Scope1を個別開示）
* `SCOPE2`（Scope2を個別開示）
* `SCOPE1_2`（Scope1+2合計を開示）
* `SCOPE3`（Scope3を開示）
* `SCOPE1_2_3`（Scope1+2+3合計を開示）
* `NONE`（対象スコープが**開示なし**であることを示す明示的記述がある場合。例：「Scope3は開示していない」）

> 補足：Scope1/2単独値と、Scope1+2合計値の両方が載る場合があるため、**併存を許容**してください。同様に、Scope1+2+3合計と各内訳が併存することもあります。

2. **GHG排出量（Emissions）**：見つかったものを**年度ごと・スコープごと・（該当時）Scope3カテゴリごとに**すべて抽出。

   * フィールド：値、単位、生年度（会計年度/暦年の表現は原文どおり）、スコープ、Scope3カテゴリ（1〜15、名称も）、Scope2方式（location-based/market-based/不明）、根拠断片。
   * 単位は原文（例：`t-CO2`, `tCO2e`, `千t-CO2e`, `万t`など）を**unit\_raw**に保持し、**value\_tco2e\_normalized**にトンCO2eへ正規化（`千t`=×1,000、`万t`=×10,000、`kt`=×1,000、`Mt`=×1,000,000）。CO2のみの場合は`gas_basis="CO2"`、CO2eなら`"CO2e"`。

3. **GHG削減率（達成実績としての増減）**：

   * フィールド：基準年、達成年、削減（もしくは増加）率\[%]、増減量（値+単位、正規化値）、対象スコープ（上記パターンのいずれか/複数可）、根拠断片。
   * 削減方向は`"decrease"`/`"increase"`で明示。

4. **GHG削減目標（Target）**：

   * フィールド：基準年、目標年、削減率\[%]または目標量（値+単位、正規化値）、対象スコープ、`target_type`（`ABSOLUTE`/`INTENSITY`/`NET_ZERO`/`CARBON_NEUTRAL`/`OTHER`）、`net_zero_label`（原文に「ネットゼロ」「カーボンニュートラル」等があればその語）、根拠断片。
   * 中間目標が複数あれば**すべて**列挙。対象スコープが曖昧な場合は`scope_coverage="UNSPECIFIED"`とし、根拠に当該文を入れてください。

5. **開示なし（Absence）**：

   * 特定スコープについて**開示なしを示す明文**（例：「Scope3は計測・開示していない」）があれば、`disclosure_absence`に記録し、根拠を付与。

## 重要な指示

* **重複排除をしないで**ください。同じ年・同じスコープでも、出所（本文/別表、location/market方式別など）が異なる場合は**すべて残す**。
* 数値は半角・全角、カンマ、括弧、注記（※）等に頑健に対応。日本語数量表現（億/万）や「▲」「△」などのマイナス表現も解釈。
* 年度は文字列として原文を保持（例：「2023年度」「FY2023」「2022年」）。
* 文字位置は**入力テキスト全体の先頭からの0始まりインデックス**で`char_span_start`/`char_span_end`に格納。表（CSV文字列）由来なら`source_type="table_csv"`にし、`table_excerpt`にCSVの先頭3〜5行をそのまま入れる。
* **根拠（evidence）を必須**にしてください（短い引用と文字位置）。
* Scope3カテゴリは数字1〜15を推定し、原文の日本語ラベル（例：「カテゴリ1 購入した製品・サービス」）も`category_label`に保存。数字が不明なら`category_other_note`に原文を入れてください。
* Scope2は`scope2_method`に`"location"`/`"market"`/`"unspecified"`のいずれか。
* 出力は**指定スキーマのJSONのみ**。それ以外の文字を出力しないこと。

入力：有報サステナ章のプレーンテキスト全量（表はCSV文字列として本文に内包）
出力：指定スキーマに適合するJSON

---

# Pydanticスキーマ（Python / pydantic v1想定）

```python
from __future__ import annotations
from typing import List, Optional, Literal
from decimal import Decimal
from pydantic import BaseModel, Field, validator, root_validator

ScopePattern   = Literal["SCOPE1", "SCOPE2", "SCOPE1_2", "SCOPE3", "SCOPE1_2_3", "NONE"]
ScopeCoverage  = Literal["SCOPE1", "SCOPE2", "SCOPE1_2", "SCOPE3", "SCOPE1_2_3", "UNSPECIFIED"]
TargetType     = Literal["ABSOLUTE", "INTENSITY", "NET_ZERO", "CARBON_NEUTRAL", "OTHER"]
SourceType     = Literal["text", "table_csv"]
Scope2Method   = Literal["location", "market", "unspecified"]
Direction      = Literal["decrease", "increase"]

class Evidence(BaseModel):
    text_snippet: str = Field(..., description="根拠となる短い引用（最大300文字程度）")
    char_span_start: Optional[int] = Field(None, description="引用開始の文字位置（0始まり）")
    char_span_end: Optional[int] = Field(None, description="引用終了の文字位置（0始まり、含まない）")
    source_type: SourceType = Field("text", description="本文テキストかCSV表か")
    table_excerpt: Optional[str] = Field(None, description="表由来の場合、CSVの先頭数行")

class DisclosurePattern(BaseModel):
    pattern: ScopePattern
    note: Optional[str] = Field(None, description="判定補足（例：同一箇所で複数パターン併存など）")
    evidence: List[Evidence]

class EmissionRecord(BaseModel):
    scope: ScopeCoverage
    year_label: Optional[str] = Field(None, description="年度・年の表記（例：2023年度, FY2023, 2022年）")
    value: Decimal = Field(..., gt=0, description="数値（raw単位の値）")
    unit_raw: str = Field(..., description="原文の単位（例：t-CO2, tCO2e, 千t-CO2e, 万t など）")
    value_tco2e_normalized: Optional[Decimal] = Field(None, gt=0, description="t-CO2e正規化値（可能なら）")
    gas_basis: Optional[Literal["CO2", "CO2e", "unspecified"]] = None
    scope3_category_no: Optional[int] = Field(None, ge=1, le=15, description="Scope3カテゴリ番号（1〜15）")
    category_label: Optional[str] = None
    category_other_note: Optional[str] = None
    scope2_method: Optional[Scope2Method] = None
    evidence: List[Evidence]

class ReductionRecord(BaseModel):
    scope_coverage: ScopeCoverage
    baseline_year_label: Optional[str] = None
    achievement_year_label: Optional[str] = None
    reduction_rate_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    change_direction: Optional[Direction] = None
    change_amount_value: Optional[Decimal] = Field(None, gt=0)
    change_amount_unit_raw: Optional[str] = None
    change_amount_tco2e_normalized: Optional[Decimal] = Field(None, gt=0)
    evidence: List[Evidence]

class InterimTarget(BaseModel):
    target_year_label: Optional[str] = None
    reduction_rate_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    target_amount_value: Optional[Decimal] = Field(None, gt=0)
    target_amount_unit_raw: Optional[str] = None
    target_amount_tco2e_normalized: Optional[Decimal] = Field(None, gt=0)
    evidence: List[Evidence] = Field(default_factory=list)

class TargetRecord(BaseModel):
    scope_coverage: ScopeCoverage
    baseline_year_label: Optional[str] = None
    target_year_label: Optional[str] = None
    reduction_rate_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    target_amount_value: Optional[Decimal] = Field(None, gt=0)
    target_amount_unit_raw: Optional[str] = None
    target_amount_tco2e_normalized: Optional[Decimal] = Field(None, gt=0)
    target_type: TargetType = "ABSOLUTE"
    net_zero_label: Optional[str] = Field(
        None, description="原文の『ネットゼロ』『カーボンニュートラル』等の語"
    )
    scope3_categories_covered: Optional[List[int]] = Field(
        None, description="対象がScope3のとき、該当カテゴリ（1〜15）を列挙"
    )
    interim_targets: List[InterimTarget] = Field(default_factory=list)
    evidence: List[Evidence]

    @validator("scope3_categories_covered", each_item=True)
    def _check_scope3_list(cls, v):
        if v is not None and not (1 <= v <= 15):
            raise ValueError("scope3_categories_covered は 1〜15")
        return v

class AbsenceRecord(BaseModel):
    scope_coverage: ScopeCoverage
    description: str = Field(..., description="『開示なし』を示す原文趣旨")
    evidence: List[Evidence]

class DocumentMetadata(BaseModel):
    issuer_name: Optional[str] = None
    fiscal_year_label: Optional[str] = None
    notes: Optional[str] = None

class ExtractionResult(BaseModel):
    metadata: Optional[DocumentMetadata] = None
    scope_patterns: List[DisclosurePattern]
    emissions: List[EmissionRecord] = Field(default_factory=list)
    reductions: List[ReductionRecord] = Field(default_factory=list)
    targets: List[TargetRecord] = Field(default_factory=list)
    disclosure_absence: List[AbsenceRecord] = Field(default_factory=list)

    @root_validator
    def ensure_evidence_nonempty(cls, values):
        for key in ["scope_patterns", "emissions", "reductions", "targets", "disclosure_absence"]:
            for item in values.get(key, []):
                if not getattr(item, "evidence", []):
                    raise ValueError(f"{key} の要素に evidence が必要です")
        return values

    # 追加の安全バリデーション（任意）
    @validator(
        "emissions", "reductions", "targets", pre=True, each_item=False
    )
    def _coerce_decimals(cls, v):
        # 文字列数値→Decimalの自動変換はpydanticに任せればOKだが、
        # 必要に応じてカンマ除去などの前処理をここで入れてもよい。
        return v
```

---

## 使い方のヒント（超簡潔）

* LLMへは上の**抽出プロンプト**を提示し、入力にサステナ章の.txt全文を与えます（CSV表も本文中に含まれている前提）。
* 返ってきたJSONを上記Pydanticでバリデート。`value_tco2e_normalized`や`change_amount_tco2e_normalized`は、前処理/後処理で補完してもOKです（LLMが直接計算できない場合に備えて）。
* **重複は保持**し、後段で統合が必要ならキー（`year_label, scope, scope3_category_no, scope2_method`等）で整備してください。

必要なら、このスキーマをあなたのワークフローに合わせて微調整できます。
