import pandas as pd

# Function to calculate form
def calculate_form(df, team, date, is_home):
    matches = df[((df["HomeTeam"] == team) | (df["AwayTeam"] == team)) & (df["Date"] < date)].sort_values(by="Date", ascending=False).head(5)
    form = 0
    for _, match in matches.iterrows():
        if match["HomeTeam"] == team:
            if match["FTR"] == "H":
                form += 3
            elif match["FTR"] == "D":
                form += 1
        else:
            if match["FTR"] == "A":
                form += 3
            elif match["FTR"] == "D":
                form += 1
    return form

# Function to calculate H2H results
def calculate_h2h(df, home_team, away_team, date, num_matches):
    matches = df[(((df["HomeTeam"] == home_team) & (df["AwayTeam"] == away_team)) | ((df["HomeTeam"] == away_team) & (df["AwayTeam"] == home_team))) & (df["Date"] < date)].sort_values(by="Date", ascending=False).head(num_matches)
    if len(matches) < num_matches:
        return 0, 0, 0, 0
    home_results = 0
    away_results = 0
    h2hhomegd = 0
    h2hawaygd = 0 
    for _, match in matches.iterrows():
        if match["HomeTeam"] == home_team:
            if match["FTR"] == "H":
                home_results += 3
            elif match["FTR"] == "D":
                home_results += 1
            h2hhomegd += match["FTHG"] - match["FTAG"]
        elif match["AwayTeam"] == home_team:
            if match["FTR"] == "A":
                home_results += 3
            elif match["FTR"] == "D":
                home_results += 1
            h2hhomegd += match["FTAG"] - match["FTHG"]
        if match["HomeTeam"] == away_team:
            if match["FTR"] == "H":
                away_results += 3
            elif match["FTR"] == "D":
                away_results += 1
            h2hawaygd += match["FTHG"] - match["FTAG"]
        elif match["AwayTeam"] == away_team:
            if match["FTR"] == "A":
                away_results += 3
            elif match["FTR"] == "D":
                away_results += 1
            h2hawaygd += match["FTAG"] - match["FTHG"]
    return home_results, away_results, h2hhomegd, h2hawaygd

# Function to clean and process each dataset
def clean_la_liga_data(file_path, output_path):
    df = pd.read_csv(file_path)  # Load dataset

    # Parse the date column
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)

    # Extract additional features
    df["TotalCorners"] = df["HC"] + df["AC"]
    df["TotalYellowCards"] = df["HY"] + df["AY"]
    df["TotalGoals"] = df["FTHG"] + df["FTAG"]
    df["BothTeamsScored"] = ((df["FTHG"] > 0) & (df["FTAG"] > 0)).astype(int)
    df["2ndHalfHomeGoals"] = df["FTHG"] - df["HTHG"]
    df["2ndHalfAwayGoals"] = df["FTAG"] - df["HTAG"]
    df["2ndHalfTotalGoals"] = df["2ndHalfHomeGoals"] + df["2ndHalfAwayGoals"]
    df["1stHalfTotalGoals"] = df["HTAG"] + df["HTHG"]

    # Calculate form for each match
    df["HomeForm"] = df.apply(lambda row: calculate_form(df, row["HomeTeam"], row["Date"], True), axis=1)
    df["AwayForm"] = df.apply(lambda row: calculate_form(df, row["AwayTeam"], row["Date"], False), axis=1)

    # Debug prints to verify form calculation
    print(df[["Date", "HomeTeam", "AwayTeam", "HomeForm", "AwayForm"]].head(10))

    # Select only the necessary columns
    columns_to_keep = [
        "Div", "Date", "HomeTeam", "AwayTeam",  # Match Details
        "FTHG", "FTAG", "FTR",  # Full-Time Results
        "HTHG", "HTAG", "HTR",  # Half-Time Results
        "HS", "AS", "HST", "AST",  # Match Statistics
        "HC", "AC", "HF", "AF", "HY", "AY", "HR", "AR",  # Additional Stats
        "TotalCorners", "TotalYellowCards", "TotalGoals", "BothTeamsScored", 
        "2ndHalfHomeGoals", "2ndHalfAwayGoals", "2ndHalfTotalGoals", "HomeForm", "AwayForm"
    ]

    df = df[columns_to_keep]  # Keep only the selected columns

    # Save the cleaned dataset
    df.to_csv(output_path, index=False)
    print(f"Saved {output_path}")

# Clean and process each season's data
clean_la_liga_data("C:/Users/sethi/Downloads/la liga 22-23.csv", "cleaned_data22-23.csv")
clean_la_liga_data("C:/Users/sethi/Downloads/la liga 23-24.csv", "cleaned_data23-24.csv")
clean_la_liga_data("C:/Users/sethi/Downloads/la liga 24-25.csv", "cleaned_data24-25.csv")

# Combine the cleaned datasets
df1 = pd.read_csv("cleaned_data22-23.csv")
df2 = pd.read_csv("cleaned_data23-24.csv")
df3 = pd.read_csv("cleaned_data24-25.csv")

combined_df = pd.concat([df1, df2, df3])
print("Combined datasets")

# Sort by date if needed (uncomment the following lines if necessary)
# combined_df["Date"] = pd.to_datetime(combined_df["Date"], dayfirst=True)
# combined_df = combined_df.sort_values(by="Date")

# Add H2H features
combined_df["HomeH2HResults"] = combined_df.apply(lambda row: calculate_h2h(combined_df, row["HomeTeam"], row["AwayTeam"], row["Date"], 5)[0], axis=1)
combined_df["AwayH2HResults"] = combined_df.apply(lambda row: calculate_h2h(combined_df, row["HomeTeam"], row["AwayTeam"], row["Date"], 5)[1], axis=1)
combined_df["HomeH2HGD"] = combined_df.apply(lambda row: calculate_h2h(combined_df, row["HomeTeam"], row["AwayTeam"], row["Date"], 5)[2], axis=1)
combined_df["AwayH2HGD"] = combined_df.apply(lambda row: calculate_h2h(combined_df, row["HomeTeam"], row["AwayTeam"], row["Date"], 5)[3], axis=1)

# Save the combined and sorted dataset
combined_df.to_csv("C:/Users/sethi/Desktop/sportb/combined_cleaned_data_new.csv", index=False)
print("Saved combined_cleaned_data_new.csv")

# Verify the columns in the saved file
saved_df = pd.read_csv("C:/Users/sethi/Desktop/sportb/combined_cleaned_data_new.csv")
print(saved_df.head(10))
