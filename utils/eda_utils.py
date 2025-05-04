# -*- coding: utf-8 -*-

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
import fastavro

def read_multiple_csv_from_folder(folder_path, file_extension = '.csv'):
    """
    Read multiple CSV files from a folder and concatenate them into a single DataFrame.

    Parameters:
    folder_path (str): Path to the folder containing the CSV files.
    file_extension (str): File extension of the files to read. Default is '.csv'.

    Returns:
    pd.DataFrame: Concatenated DataFrame containing data from all CSV files.
    """
    import os 
    import glob

    try:
        all_csv_path = glob.glob(os.path.join(folder_path, "*.csv"))
        dataframes = {}

        for path in all_csv_path:
            file_name = os.path.basename(path).replace(".csv", "")
            file_name = file_name[10:]
            file_name = file_name.replace(" ", "_")

            dataframes[file_name] = pd.read_csv(path, sep = ";")

            print(f"File {file_name} loaded!")
        
        return dataframes
    except Exception as e:
        print(f"Error reading files: {e}")
        return None

def quick_overview_data(df, csv_path, open_browser=True):
    """
    Generate a quick overview of the DataFrame and create an HTML report named after the CSV file.

    Parameters:
        df (pd.DataFrame): DataFrame to analyze.
        csv_path (str): Path to the CSV file the DataFrame came from.

    Returns:
        dict: Basic info including shape, column names, and data types.
    """
    import os
    import webbrowser
    from ydata_profiling import ProfileReport

    # Tách tên file không có đuôi .csv
    file_name = os.path.splitext(os.path.basename(csv_path))[0]

    # Tạo folder chứa báo cáo nếu chưa có
    output_dir = "./Data_Report"
    os.makedirs(output_dir, exist_ok=True)

    # Tạo báo cáo
    profile = ProfileReport(df, title=f"EDA Report - {file_name}", explorative=True)
    output_path = os.path.join(output_dir, f"{file_name}.html")
    profile.to_file(output_path)

    # Mở trên trình duyệt
    if open_browser:
        webbrowser.open(output_path)
    else:
        print(f"Report saved to {output_path}")

    return {
        "file_name": file_name,
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "dtypes": df.dtypes.to_dict()
    }

def check_null_overlap(df, columns):
    """
    Check null values for multiple columns and whether they occur in the same rows.

    Parameters:
        df (pd.DataFrame): The input DataFrame.
        columns (list): List of column names to check.

    Returns:
        None: Prints summary of nulls and overlapping results.
    """
    print("🔍 Null Count per Column:")
    for col in columns:
        null_count = df[col].isnull().sum()
        print(f" - {col}: {null_count} nulls")

    # Check if all specified columns have nulls in the same rows
    print("\n📊 Checking if nulls occur in the same rows:")

    # Create a boolean mask per column (True if null)
    null_masks = [df[col].isnull() for col in columns]

    # Combine all masks to see if they are exactly the same
    all_equal = all((null_masks[0] == mask).all() for mask in null_masks[1:])

    if all_equal:
        print("[V] All columns have nulls in the same rows.")
    else:
        print("[X] Nulls do NOT overlap exactly in all columns.")

        # Show which rows differ (optional)
        print("\n Rows with partial nulls (mismatch):")
        mask_any = pd.concat(null_masks, axis=1).any(axis=1)
        mask_all = pd.concat(null_masks, axis=1).all(axis=1)
        mismatch_rows = df[mask_any & ~mask_all]
        display(mismatch_rows.head())  # show only first few rows
    

def check_duplicates(df, columns):
    """
    Check for duplicate rows in the DataFrame based on specified columns and remove duplicates if found.

    Parameters:
        df (pd.DataFrame): The input DataFrame.
        columns (list): List of column names to check for duplicates.

    Returns:
        pd.DataFrame: The DataFrame with duplicates removed if any.
    """
    duplicate_count = df.duplicated(subset=columns).sum()
    print(f"🔍 Duplicate Rows based on data: {duplicate_count} duplicates found.")
    
    if duplicate_count > 0:
        # Get and print rows that are duplicates
        remove_duplicates = df[df.duplicated(subset=columns, keep=False)]
        print("Duplicates found and will be removed:")
        print(remove_duplicates)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=columns, keep='first')
        print("Duplicates removed.")
    else:
        print("No duplicates found. Data is clean.")
    
    return df

def convert_csv_to_avro(df: pd.DataFrame, csv_path: str, output_dir: str = None) -> str:
    """
    Generate an Avro schema from a DataFrame, print it to console, and save it as a .avsc file.

    Parameters:
        df (pd.DataFrame): Source DataFrame.
        csv_path (str): Path to the source CSV file (used for naming).
        output_dir (str, optional): Directory in which to save the .avsc file.
                                    If None, defaults to the CSV’s folder.

    Returns:
        str: Path to the written .avsc file.
    """
    # 1. Determine base name and output path
    base_name = os.path.splitext(os.path.basename(csv_path))[0]
    schema_name = base_name[len("Fecom Inc "):]
    if output_dir is None:
        output_dir = os.path.dirname(csv_path) or os.getcwd()
    os.makedirs(output_dir, exist_ok=True)
    schema_path = os.path.join(output_dir, f"{schema_name}.avsc")

    # 2. Build schema fields
    fields = []
    for col in df.columns:
        dtype = df[col].dtype
        has_null = df[col].isnull().any()

        # Map pandas dtype to Avro type
        if dtype == 'bool' or dtype == np.bool_:
            avro_type = "boolean"
        elif dtype in ('int64', np.int64, 'Int64'):
            avro_type = "int"
        elif dtype in ('float64', np.float64):
            avro_type = "float"
        elif dtype.kind == 'M':  # M nghĩa là datetime64
            avro_type = {"type": "long", "logicalType": "timestamp-millis"}
        else:
            avro_type = "string"

        # Wrap in a null union if needed
        if has_null:
            field_schema = {"name": col, "type": ["null", avro_type], "default": None}
        else:
            field_schema = {"name": col, "type": avro_type}

        fields.append(field_schema)

    schema = {
        "doc": f"Schema for e-commerce {base_name} data",
        "type": "record",
        "name": schema_name,
        "namespace": "com.fecom.ecommerce",
        "fields": fields
    }

    # 3. Print schema for comparison
    schema_json = json.dumps(schema, indent=2)
    print("=== Generated Avro Schema ===")
    print(schema_json)
    print("=============================")

    # 4. Save schema to .avsc
    with open(schema_path, 'w') as f:
        f.write(schema_json)

    print(f"Schema saved to: {schema_path}")
    return schema_path