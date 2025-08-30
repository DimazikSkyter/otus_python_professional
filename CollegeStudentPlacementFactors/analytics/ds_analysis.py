import pandas as pd


def parse_placement_data(csv_file_path):
    """
    Parses the college student placement dataset from a CSV file into a Pandas DataFrame.

    Args:
        csv_file_path (str): The path to the CSV file.

    Returns:
        pandas.DataFrame: The parsed DataFrame.
    """

    try:
        df = pd.read_csv(csv_file_path)
    except FileNotFoundError:
        print(f"Error: File not found at {csv_file_path}")
        return None

    print("DataFrame Head:")
    print(df.head())

    print("\nDataFrame Info:")
    print(df.info())

    # Handle missing values
    for col in df.columns:
        if df[col].isnull().any():
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col].fillna(df[col].mean(), inplace=True)
            else:
                df[col].fillna(df[col].mode()[0], inplace=True)

    # Encode categorical features (one-hot encoding)
    categorical_cols = [col for col in df.columns if df[col].dtype == "object"]
    df = pd.get_dummies(
        df, columns=categorical_cols, drop_first=True
    )  # drop_first to avoid multicollinearity

    print("\nDataFrame after preprocessing:")
    print(df.head())

    return df


if __name__ == "__main__":
    # Replace 'path/to/your/CollegePlacement.csv' with the actual path to your file
    file_path = "path/to/your/CollegePlacement.csv"
    parsed_df = parse_placement_data(file_path)

    if parsed_df is not None:
        print("\nParsed DataFrame shape:", parsed_df.shape)
