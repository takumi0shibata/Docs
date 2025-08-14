以下は、有価証券報告書をテキスト化した単一のTXTです（ページや表IDはありません）。
本文中に「表」が埋め込まれている場合があります（CSV/TSV/複数スペース/縦線などの擬似表行）。

あなたのタスクは、本文から下記の最小情報を年度すべて＆該当スコープすべてについて
完全に漏れなく抽出し、指定のPydanticスキーマに**完全準拠**した**JSONのみ**を返すことです。
各レコードには**抽出根拠（Evidence）**を必ず含めます。

【入力メタ】
発行体名: {{issuer}}

【本文（TXT全量。先頭からの文字位置=0起点）】
{{full_txt}}

【抽出対象（この4種類以外は出力禁止）】
1) 開示スコープ項目の組み合わせ（disclosure_items）
   - 本文で実際に確認できた“開示項目”をすべて列挙（順不同・重複なし）
     * "S1"                … scope 1 を開示
     * "S2"                … scope 2 を開示
     * "S1_PLUS_2"         … scope 1 と scope 2 の**合計**を開示（別名：S1+S2/自社排出量/Scope1,2合計 など）
     * "S3"                … scope 3 を開示（合計またはカテゴリ別いずれでも可）
     * "S1_PLUS_2_PLUS_3"  … scope 1, 2, 3 の**合計**を開示（別名：総排出量（S1-3） など）
     * "NONE"              … **開示なし**（GHG排出量/削減率/削減目標のいずれも本文で確認できない）
   - 重要ルール:
     - "NONE" は排他的（["NONE"] のみ許容）。この場合、emissions/reductions/targets は空配列。
     - "NONE" を選ぶ根拠は次のいずれか：
       ① 明示の未開示記述（例：未開示/非開示/未算定/記載なし/該当なし/対象外 等）がある
       ② 上記の開示項目や関連数値・率・目標の**証跡が本文に一切見つからない**

2) GHG排出量（emissions）
   - レコード: { scope, fiscal_year_label, value, unit, (S3なら s3_category_code/name), evidence[] }
   - scope は S1/S2/S3/S1_PLUS_2/S1_PLUS_2_PLUS_3 のいずれか。
   - 年度は原文ラベル（例: "2024年3月期", "FY2023"）。値は数値化（カンマ除去）、単位は原文どおり。
   - S3カテゴリがあれば code(1–15)/name を可能な限り付与。総量のみでも可。
   - **本文で確認できたすべての年度**を網羅。

3) GHG削減率（reductions）
   - レコード: { scope, baseline_year, achievement_year, reduction_rate, evidence[] }
   - reduction_rate は実数（割合）で -1〜1。10%削減→0.10、5%増→-0.05。
   - 率が明記されない場合、同一 scope の排出量から
     (baseline年度の値 - achievement年度の値) / baseline年度の値 で算出してよい（その根拠も evidence に含める）。

4) GHG削減目標（targets）
   - レコード: { scopes[], base_year, target_year, reduction_rate|null, goal_kind, evidence[] }
   - scopes は対象スコープ配列（S1/S2/S3/S1_PLUS_2/S1_PLUS_2_PLUS_3）。
   - goal_kind: "reduction" | "carbon_neutral" | "net_zero"
     - 「カーボンニュートラル/カーボンゼロ」→ carbon_neutral
     - 「ネットゼロ/実質ゼロ」→ net_zero
     - 割合目標のみ → reduction（この場合 reduction_rate は必須）
   - base_year < target_year。reduction_rate がある場合は 0〜1。

【Evidence（根拠）の作り方】
- 各レコードの evidence は **1件以上**。次の形式で作成：
  * quote … 原文からの**短い完全一致抜粋**（5〜180文字、改変・要約禁止）
  * char_start / char_end … TXT先頭からの**0始まり文字位置**（どちらも整数）。少なくとも char_* か line_* を指定。
  * line_start / line_end … TXTの**1始まり行番号**（改行カウントで算出）。少なくとも line_* か char_* を指定。
  * is_table_like … その証跡が表構造（CSV/TSV/複数スペース/縦線）に見える場合は true、通常段落なら false。
  * notes … 解析補足（例：列見出しとセル対応、単位の読み取り等）
- 削減率を「排出量から算出」した場合は、**基準年と達成年の値それぞれの証跡**を evidence に**複数**入れること。

【擬似表の取り扱い】
- 年度列ヘッダ（例：「項目,2023年3月期,2024年3月期」）を検出し、行の項目（Scope1/Scope2/合計/Scope3等）と
  列の年度を対応付けてセル値を解釈してよい。
- 「合計/計/S1+S2/Scope1+2/自社排出量」→ S1_PLUS_2、
  「S1+S2+S3/総排出量（S1-3）」→ S1_PLUS_2_PLUS_3 に正規化してよい。
- 単位は原文のまま unit に格納（数値は value に数値型で）。

【完全網羅と禁止事項】
- 抽出できた**すべての年度**を漏れなく列挙（重複年度は別レコードで可）。
- 推測・補完禁止。見つからないものは出力しない。
- "NONE" の場合は emissions/reductions/targets を空配列にし、disclosure_absence を必ず出力。
- 余計な説明やマークダウンは禁止。**JSONのみ**を返す。
- 出力は Pydantic スキーマ "GHGMinimalExtractionV3" に**完全準拠**。


from typing import List, Optional, Literal, Set
from pydantic import BaseModel, Field, StrictFloat, StrictInt, root_validator, validator

# 公表され得る5項目 + 開示なし
Scope = Literal['S1', 'S2', 'S3', 'S1_PLUS_2', 'S1_PLUS_2_PLUS_3']
DisclosureItem = Literal['S1', 'S2', 'S3', 'S1_PLUS_2', 'S1_PLUS_2_PLUS_3', 'NONE']
GoalKind = Literal['reduction', 'carbon_neutral', 'net_zero']

class Evidence(BaseModel):
    quote: str = Field(..., min_length=5, max_length=180,
                       description="原文からの短い完全一致抜粋（改変なし）")
    # 文字位置か行番号のどちらか（または両方）を指定
    char_start: Optional[int] = Field(None, ge=0, description="TXT先頭からの0始まり文字位置")
    char_end: Optional[int] = Field(None, ge=0, description="TXT先頭からの0始まり文字位置（終端）")
    line_start: Optional[int] = Field(None, ge=1, description="1始まりの開始行番号")
    line_end: Optional[int] = Field(None, ge=1, description="1始まりの終了行番号")
    is_table_like: Optional[bool] = Field(False, description="CSV/TSV/複数スペース/縦線など表構造に見える場合は True")
    notes: Optional[str] = Field(None, description="列見出し対応や単位読み取りなど補足")

    class Config:
        extra = 'forbid'

    @root_validator
    def _require_positions(cls, values):
        cs, ce = values.get('char_start'), values.get('char_end')
        ls, le = values.get('line_start'), values.get('line_end')
        if (cs is None or ce is None) and (ls is None or le is None):
            raise ValueError("Evidence には char_start/char_end または line_start/line_end の少なくとも一方を指定してください")
        if cs is not None and ce is not None and ce < cs:
            raise ValueError("char_end は char_start 以上である必要があります")
        if ls is not None and le is not None and le < ls:
            raise ValueError("line_end は line_start 以上である必要があります")
        return values

class Emission(BaseModel):
    scope: Scope = Field(..., description="S1/S2/S3/S1_PLUS_2/S1_PLUS_2_PLUS_3")
    fiscal_year_label: str = Field(..., description='例: "2024年3月期", "FY2023" など原文ラベル')
    value: StrictFloat = Field(..., ge=0.0, description="数値（カンマ除去済み）")
    unit: str = Field(..., description='例: "t-CO2e", "千t-CO2e"（原文のまま）')
    # Scope 3 の場合のみ任意
    s3_category_code: Optional[StrictInt] = Field(None, ge=1, le=15)
    s3_category_name: Optional[str] = None
    # 根拠（1件以上）
    evidence: List[Evidence] = Field(..., min_items=1)

    class Config:
        extra = 'forbid'

class Reduction(BaseModel):
    scope: Scope
    baseline_year: StrictInt = Field(..., ge=1900, le=2200)
    achievement_year: StrictInt = Field(..., ge=1900, le=2200)
    reduction_rate: StrictFloat = Field(..., ge=-1.0, le=1.0,
        description="(baseline - achievement) / baseline。10%削減=0.10、5%増=-0.05")
    # 根拠（1件以上。算出の場合は基準年と達成年の値それぞれの証跡を含める）
    evidence: List[Evidence] = Field(..., min_items=1)

    class Config:
        extra = 'forbid'

    @root_validator
    def _years_order(cls, values):
        b, a = values.get('baseline_year'), values.get('achievement_year')
        if b is not None and a is not None and b > a:
            raise ValueError("achievement_year は baseline_year 以上である必要があります")
        return values

class Target(BaseModel):
    scopes: List[Scope] = Field(..., min_items=1, description="目標対象のスコープ群")
    base_year: StrictInt = Field(..., ge=1900, le=2200)
    target_year: StrictInt = Field(..., ge=1900, le=2200)
    reduction_rate: Optional[StrictFloat] = Field(None, ge=0.0, le=1.0,
        description="0.5 は 50%削減。割合記載が無ければ null")
    goal_kind: GoalKind
    # 根拠（1件以上）
    evidence: List[Evidence] = Field(..., min_items=1)

    class Config:
        extra = 'forbid'

    @root_validator
    def _years_order(cls, values):
        b, t = values.get('base_year'), values.get('target_year')
        if b is not None and t is not None and b >= t:
            raise ValueError("base_year は target_year より小さい必要があります")
        return values

    @root_validator
    def _rate_required_for_reduction(cls, values):
        kind = values.get('goal_kind')
        rate = values.get('reduction_rate')
        if kind == 'reduction' and rate is None:
            raise ValueError("goal_kind='reduction' の場合、reduction_rate は必須です")
        return values

class DisclosureEvidence(BaseModel):
    item: DisclosureItem = Field(..., description='NONE 以外の開示項目')
    evidence: List[Evidence] = Field(..., min_items=1)

    class Config:
        extra = 'forbid'

class DisclosureAbsence(BaseModel):
    reason: Literal['explicit_statement', 'no_traces_found'] = Field(...,
        description="明示の未開示記述があるか（explicit_statement）、痕跡が無いか（no_traces_found）")
    # explicit_statement の場合は引用必須
    evidence: Optional[List[Evidence]] = Field(None, description="未開示を示す文言の証跡（ある場合）")
    notes: Optional[str] = Field(None, description="用いた探索語や確認範囲など")

    class Config:
        extra = 'forbid'

class GHGMinimalExtractionV3(BaseModel):
    issuer: str = Field(..., description="発行体名")
    disclosure_items: List[DisclosureItem] = Field(..., min_items=1,
        description='本文で確認できた開示項目の組み合わせ。開示なしは ["NONE"] のみ許容。')

    # 開示があった項目ごとの根拠（NONE は含めない）
    disclosure_evidence: Optional[List[DisclosureEvidence]] = Field(None)

    # NONE の場合の理由と根拠
    disclosure_absence: Optional[DisclosureAbsence] = Field(None)

    emissions: List[Emission] = Field(default_factory=list)
    reductions: List[Reduction] = Field(default_factory=list)
    targets: List[Target] = Field(default_factory=list)

    class Config:
        extra = 'forbid'
        anystr_strip_whitespace = True
        validate_assignment = True

    @validator('disclosure_items')
    def _unique_items(cls, v):
        if len(v) != len(set(v)):
            raise ValueError("disclosure_items に重複があります")
        return v

    @root_validator
    def _consistency(cls, values):
        items: List[DisclosureItem] = values.get('disclosure_items') or []
        emissions = values.get('emissions') or []
        reductions = values.get('reductions') or []
        targets = values.get('targets') or []
        de = values.get('disclosure_evidence') or []
        absence = values.get('disclosure_absence')

        if 'NONE' in items:
            # ["NONE"] のみ許容、データは全て空、欠如理由が必要
            if len(items) != 1:
                raise ValueError('disclosure_items に "NONE" を含む場合、["NONE"] のみ許容されます')
            if emissions or reductions or targets:
                raise ValueError('disclosure_items=["NONE"] の場合、emissions/reductions/targets は空でなければなりません')
            if de:
                raise ValueError('disclosure_items=["NONE"] の場合、disclosure_evidence は空/未指定である必要があります')
            if absence is None:
                raise ValueError('disclosure_items=["NONE"] の場合、disclosure_absence を必ず指定してください')
            # explicit_statement の場合は証跡を推奨（あれば1件以上）
            if absence.reason == 'explicit_statement' and not absence.evidence:
                raise ValueError('disclosure_absence.reason="explicit_statement" の場合、未開示を示す Evidence を1件以上含めてください')
            return values

        # "NONE" 以外の場合：データに出てくる全スコープが disclosure_items に包含されていること
        data_scopes: Set[Scope] = set(e.scope for e in emissions)
        data_scopes |= set(r.scope for r in reductions)
        for t in targets:
            data_scopes |= set(t.scopes)

        if not set(items).issuperset(data_scopes):
            missing = sorted(list(data_scopes - set(items)))
            raise ValueError(f"disclosure_items がデータに登場するスコープ {missing} を含んでいません")

        # disclosure_evidence が items（NONE以外）をカバーしていること
        if not de:
            raise ValueError('開示がある場合、disclosure_evidence を指定してください')
        de_items = {d.item for d in de}
        needed = set(i for i in items if i != 'NONE')
        if not de_items.issuperset(needed):
            missing = sorted(list(needed - de_items))
            raise ValueError(f"disclosure_evidence に {missing} の根拠が不足しています")

        return values