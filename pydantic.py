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
    text_snippet: str
    char_span_start: Optional[int] = None
    char_span_end: Optional[int] = None
    source_type: SourceType = "text"
    table_excerpt: Optional[str] = None

class DisclosurePattern(BaseModel):
    pattern: Optional[ScopePattern] = Field(
        None,
        description="スコープパターン。開示なしの場合は None"
    )
    note: Optional[str] = None
    evidence: List[Evidence] = Field(default_factory=list)

class EmissionRecord(BaseModel):
    scope: ScopeCoverage
    year_label: Optional[str] = None
    value: Decimal = Field(..., gt=0)
    unit_raw: str
    value_tco2e_normalized: Optional[Decimal] = Field(None, gt=0)
    gas_basis: Optional[Literal["CO2", "CO2e", "unspecified"]] = None
    scope3_category_no: Optional[int] = Field(None, ge=1, le=15)
    category_label: Optional[str] = None
    category_other_note: Optional[str] = None
    scope2_method: Optional[Scope2Method] = None
    evidence: List[Evidence] = Field(default_factory=list)

class ReductionRecord(BaseModel):
    scope_coverage: ScopeCoverage
    baseline_year_label: Optional[str] = None
    achievement_year_label: Optional[str] = None
    reduction_rate_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    change_direction: Optional[Direction] = None
    change_amount_value: Optional[Decimal] = Field(None, gt=0)
    change_amount_unit_raw: Optional[str] = None
    change_amount_tco2e_normalized: Optional[Decimal] = Field(None, gt=0)
    evidence: List[Evidence] = Field(default_factory=list)

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
    net_zero_label: Optional[str] = None
    scope3_categories_covered: Optional[List[int]] = Field(None)
    interim_targets: List[InterimTarget] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)

    @validator("scope3_categories_covered", each_item=True)
    def _check_scope3_list(cls, v):
        if v is not None and not (1 <= v <= 15):
            raise ValueError("scope3_categories_covered は 1〜15")
        return v

class DocumentMetadata(BaseModel):
    issuer_name: Optional[str] = None
    fiscal_year_label: Optional[str] = None
    notes: Optional[str] = None

class ExtractionResult(BaseModel):
    metadata: Optional[DocumentMetadata] = None
    scope_patterns: List[DisclosurePattern] = Field(..., description="本文に現れた全パターン。全く開示がない場合はpattern=Noneの1件のみ")
    emissions: List[EmissionRecord] = Field(default_factory=list)
    reductions: List[ReductionRecord] = Field(default_factory=list)
    targets: List[TargetRecord] = Field(default_factory=list)

    @root_validator
    def ensure_scope_patterns_nonempty(cls, values):
        if not values.get("scope_patterns"):
            raise ValueError("scope_patterns は最低1件必要です")
        return values



