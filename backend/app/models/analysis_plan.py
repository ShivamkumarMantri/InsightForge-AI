from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator

AllowedOperation = Literal[
    "groupby",
    "date_grouping",
    "aggregation",
    "sort",
    "filter",
    "correlation",
    "summary_statistic",
    "top_k",
    "scatter",
    "histogram",
    "comparison",
    "driver_analysis"
]

AllowedAggFunc = Literal["sum", "mean", "median", "count", "min", "max", "std"]

AllowedVisualizationType = Literal[
    "bar",
    "line",
    "area",
    "pie",
    "donut",
    "scatter",
    "histogram",
    "metric",
    "none"
]

class VisualizationSpecModel(BaseModel):
    type: AllowedVisualizationType = "bar"
    title: str = Field(default="Data Analysis Visualization", max_length=150)
    x: Optional[str] = None
    y: Optional[str] = None

class GeminiAnalysisPlanModel(BaseModel):
    """
    Strict Pydantic schema for validating Gemini-generated analysis plans.
    Guarantees:
    - Only approved operations can be requested
    - Only approved aggregation functions
    - Valid limits
    - Safe structured format
    """
    intent: Optional[str] = Field(default="aggregation", max_length=50)
    analysis: Optional[str] = Field(default="Analytical Query", max_length=200)
    operation: AllowedOperation = "groupby"
    columns: Optional[List[str]] = Field(default_factory=list)
    group_by: Optional[str] = None
    target_column: Optional[str] = None
    agg_func: AllowedAggFunc = "sum"
    comparison_entities: Optional[List[str]] = None
    filter: Optional[Dict[str, Any]] = None
    dimension: Optional[str] = None
    date_freq: Optional[str] = Field(default="M", max_length=10)
    sort_order: Optional[Literal["asc", "desc"]] = "desc"
    limit: Optional[int] = Field(default=None, ge=1, le=100)
    need_clarification: bool = False
    answer: Optional[str] = None
    context_used: bool = False
    visualization: Optional[VisualizationSpecModel] = None

    @field_validator("group_by", mode="before")
    def clean_group_by(cls, v):
        if isinstance(v, list):
            return str(v[0]) if v else None
        return v

    @field_validator("columns", mode="before")
    def clean_columns(cls, v):
        if isinstance(v, list):
            return [str(c) for c in v if c]
        return []

class SingleAutoInsightModel(BaseModel):
    """Strict Pydantic validation for the 5 AI Discovered Executive Insights."""
    type: Literal["trend", "performer", "driver", "anomaly", "quality"]
    title: str = Field(..., max_length=60)
    badge: str = Field(..., max_length=50)
    category: str = Field(..., max_length=60)
    statement: str = Field(..., min_length=5, max_length=400)
    detail: Optional[str] = Field(default=None, max_length=300)
