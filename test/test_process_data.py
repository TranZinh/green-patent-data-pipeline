import polars as pl
import gc
# --- IMPORT CENTRALIZED CONFIGURATION ---
from config import (
    STORAGE_OPTIONS, 
    S3_PATH_PATENT, 
    S3_PATH_APP, 
    S3_PATH_CPC, 
    S3_PATH_ASS, 
    OUTPUT_CSV
)

def run_reconciliation():
    target_year = 2020
    # The "Big Three" for benchmarking data quality
    big_three = [
        "TOYOTA JIDOSHA KABUSHIKI KAISHA",
        "SAMSUNG ELECTRONICS CO., LTD.",
        "LG ELECTRONICS INC."
    ]

    print(f"--- STARTING BRUTE-FORCE RECONCILIATION (Year: {target_year}) ---")

    # 1. Load CSV result for comparison (Uses OUTPUT_CSV from config)
    try:
        df_csv = pl.read_csv(OUTPUT_CSV)
    except Exception as e:
        print(f"Error: Could not find {OUTPUT_CSV}. Please run the analysis script first!")
        return

    # 2. Initialize LazyFrames from MinIO using S3 paths from config
    lf_pat = pl.scan_parquet(S3_PATH_PATENT, storage_options=STORAGE_OPTIONS)
    lf_app = pl.scan_parquet(S3_PATH_APP, storage_options=STORAGE_OPTIONS)
    lf_ass = pl.scan_parquet(S3_PATH_ASS, storage_options=STORAGE_OPTIONS)
    lf_cpc = pl.scan_parquet(S3_PATH_CPC, storage_options=STORAGE_OPTIONS)

    # Pre-filter for optimization: Aligning logic with the main analysis
    print("Pre-filtering metadata for reconciliation...")
    ids_utility = lf_pat.filter(pl.col("patent_type") == "utility").select("patent_id")
    ids_year = lf_app.filter(pl.col("filing_date").str.to_date().dt.year() == target_year).select("patent_id")
    ids_y02 = lf_cpc.filter(pl.col("cpc_group").str.starts_with("Y02")).select("patent_id")

    print(f"\n{'COMPANY':<40} | {'CSV':<8} | {'RAW':<8} | {'STATUS'}")
    print("-" * 75)

    for company in big_three:
        # A. Get count from the previously processed CSV
        csv_row = df_csv.filter((pl.col("company") == company) & (pl.col("year") == target_year))
        csv_count = csv_row["count"][0] if len(csv_row) > 0 else 0

        # B. Calculate raw count from source (Brute-force verification)
        ids_company = lf_ass.filter(pl.col("disambig_assignee_organization") == company).select("patent_id")
        
        raw_count = (
            ids_company.join(ids_utility, on="patent_id") 
            .join(ids_year, on="patent_id")
            .join(ids_y02, on="patent_id")
            .select("patent_id")
            .unique()
            .collect()
        ).height

        # C. Compare and Validate
        if csv_count == raw_count:
            status = "PASS"
        else:
            status = f"FAIL (Diff: {csv_count - raw_count})"
        
        print(f"{company[:40]:<40} | {csv_count:<8} | {raw_count:<8} | {status}")

        # Explicit garbage collection to manage memory for large joins
        gc.collect()

    print("\n" + "=" * 75)
    print("RECONCILIATION PROCESS FINISHED.")

if __name__ == "__main__":
    run_reconciliation()