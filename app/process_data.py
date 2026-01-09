import polars as pl
import numpy as np

# --- IMPORT CENTRALIZED CONFIGURATION ---
from config import (
    STORAGE_OPTIONS, 
    S3_PATH_PATENT, 
    S3_PATH_APP, 
    S3_PATH_CPC, 
    S3_PATH_ASS,
    OUTPUT_CSV
)

def run_analysis():
    # --- Step 0: Loading Patent Metadata (Filter Utility) ---
    print("--- Step 0: Loading Patent Metadata (Filter Utility) ---")
    df_pat = pl.scan_parquet(S3_PATH_PATENT, storage_options=STORAGE_OPTIONS)
    df_pat = df_pat.filter(pl.col("patent_type") == "utility").select("patent_id")

    print("--- Step 1 & 2: Loading Apps & Assignees with Polars ---")
    
    # 1. Load Application and filter by date
    df_app = pl.scan_parquet(S3_PATH_APP, storage_options=STORAGE_OPTIONS)
    df_app = df_app.select(["patent_id", "filing_date"])
    
    df_app = df_app.filter(
        (pl.col("filing_date").str.to_date() >= pl.date(2012, 1, 1)) & 
        (pl.col("filing_date").str.to_date() <= pl.date(2022, 12, 31))
    )

    # 2. Load Assignee and filter out individual inventors (nulls)
    df_ass = pl.scan_parquet(S3_PATH_ASS, storage_options=STORAGE_OPTIONS)
    df_ass = df_ass.select(["patent_id", "disambig_assignee_organization"])
    df_ass = df_ass.filter(pl.col("disambig_assignee_organization").is_not_null())

    # Create reference table
    ref_table = (
        df_pat.join(df_app, on="patent_id")
        .join(df_ass, on="patent_id")
        .rename({"disambig_assignee_organization": "company"})
    )

    print("--- Step 3: Processing 57M CPC rows ---")
    
    # 3. Load CPC and filter Y02
    df_cpc = pl.scan_parquet(S3_PATH_CPC, storage_options=STORAGE_OPTIONS)
    df_cpc = df_cpc.select(["patent_id", "cpc_group"])
    df_cpc = df_cpc.filter(pl.col("cpc_group").str.starts_with("Y02"))

    print("--- Step 4: Joining and Deduplicating (Test-aligned Logic) ---")
    
    # 4. Join and then perform Unique on (company + patent_id)
    # streaming=True enabled for memory efficiency
    result = (
        df_cpc.join(ref_table, on="patent_id")
        .with_columns(pl.col("filing_date").str.to_date().dt.year().alias("year"))
        .unique(subset=["company", "patent_id"]) 
        .group_by(["company", "year"])
        .agg(pl.len().alias("count")) 
        .with_columns((pl.col("count") + 1).log().alias("ln_count_plus_1")) 
        .sort("count", descending=True)
    ).collect(streaming=True)

    print("\n" + "="*50)
    print("TOP 10 GREEN TECH COMPANIES (POLARS ENGINE)")
    print("="*50)
    print(result.head(10))
    
    # Export results using output path from config
    result.write_csv(OUTPUT_CSV)
    print(f"\nSuccess! Results saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    run_analysis()