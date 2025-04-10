# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np

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

def quick_overview_data(df, csv_path):
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
    webbrowser.open(output_path)

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

    