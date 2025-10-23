import pandas as pd
import pandera as pa
from pandera import Column, DataFrameSchema
import os
from pathlib import Path

# Define schema for validation
schema = DataFrameSchema({
    "column1": Column(str, nullable=True),
    "column2": Column(str, nullable=True),
    # Add more columns as needed based on your data
})

def load_excel(file_path):
    """Load Excel file and perform initial cleaning."""
    df = pd.read_excel(file_path)
    # Basic normalization: strip whitespaces, handle missing values
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    df = df.dropna(how='all')  # Remove empty rows
    return df

def validate_data(df):
    """Validate data against schema."""
    try:
        validated_df = schema.validate(df)
        return validated_df
    except pa.errors.SchemaError as e:
        print(f"Validation error: {e}")
        return None

def merge_dataframes(dfs):
    """Merge multiple dataframes into one."""
    if not dfs:
        return pd.DataFrame()
    merged = pd.concat(dfs, ignore_index=True)
    # Remove duplicates
    merged = merged.drop_duplicates()
    return merged

def main():
    data_dir = Path(__file__).parent.parent / "data"
    excel_files = list(data_dir.glob("*.xlsx"))
    
    dfs = []
    for file in excel_files:
        print(f"Processing {file.name}")
        df = load_excel(file)
        validated_df = validate_data(df)
        if validated_df is not None:
            dfs.append(validated_df)
    
    merged_df = merge_dataframes(dfs)
    
    # Save to output
    output_path = data_dir / "refined_data.xlsx"
    merged_df.to_excel(output_path, index=False)
    print(f"Refined data saved to {output_path}")

if __name__ == "__main__":
    main()