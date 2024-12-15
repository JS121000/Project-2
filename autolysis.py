import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import requests
import argparse
from tenacity import retry, stop_after_attempt, wait_fixed

# Set your AI Proxy Token
AI_PROXY_TOKEN = os.getenv("AIPROXY_TOKEN")  # Replace with your actual token
AI_PROXY_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"

if not AI_PROXY_TOKEN:
    raise EnvironmentError("AI Proxy Token not found. Please set AIPROXY_TOKEN environment variable.")

# Retry logic for AI Proxy calls to handle potential failures
@retry(stop=stop_after_attempt(5), wait=wait_fixed(2))
def call_ai_proxy(prompt, system_prompt=None, model="gpt-4o-mini"):
    headers = {"Authorization": f"Bearer {AI_PROXY_TOKEN}"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt or "You are a data analyst assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    response = requests.post(AI_PROXY_URL, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

# Function to analyze and visualize the dataset
def analyze_and_visualize(csv_file):
    """
    This function reads the CSV, analyzes it, generates visualizations, and creates a README.
    """
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Read the dataset with encoding handling
    try:
        df = pd.read_csv(csv_file, encoding='ISO-8859-1')  # Try using a different encoding like 'ISO-8859-1'
    except Exception as e:
        print(f"Error reading {csv_file}: {e}")
        return
    
    # Generate basic statistics and null value counts
    description = df.describe(include="all").transpose()
    null_counts = df.isnull().sum()

    # Print column details for the user
    print("Dataset Overview:")
    print(df.info())

    # Summarize data for AI
    system_prompt = f"The dataset contains the following columns:\n{list(df.columns)}\n"
    prompt = (
        f"The dataset has {len(df)} rows and {len(df.columns)} columns. "
        f"Here are some summary statistics:\n\n{description}\n\n"
        f"And here are the counts of null values:\n{null_counts}\n\n"
        "Please analyze this dataset and suggest insights, analyses, or visualizations."
    )
    insights = call_ai_proxy(prompt, system_prompt)

    # Display AI-generated insights
    print("Insights from AI:\n")
    print(insights)

    # Visualize correlations (if numeric columns exist)
    numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns
    if len(numeric_cols) > 0:
        corr_matrix = df[numeric_cols].corr()
        plt.figure(figsize=(10, 8))
        sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", fmt=".2f")
        plt.title("Correlation Matrix")
        plt.xlabel("Variables")
        plt.ylabel("Variables")
        
        # Save the plot as a PNG file in the script's directory
        plt.savefig(os.path.join(script_dir, 'correlation_matrix.png'))
        plt.close()  # Close the figure to avoid memory leaks

    # AI-guided visualization suggestions
    prompt = (
        f"Based on the dataset summary and initial analysis, what specific visualizations would you recommend? "
        "Provide code for generating them using Python's Seaborn or Matplotlib libraries."
    )
    visualization_code = call_ai_proxy(prompt, system_prompt)
    
    # Print AI-generated visualization code for inspection
    print("AI-generated visualization code:\n")
    print(visualization_code)
    
    try:
        # Try executing the AI code
        exec(visualization_code)  # Caution: Ensure validation if using in production
        print("Visualization generated successfully based on AI recommendation.")
    except Exception as e:
        print(f"Error executing AI visualization code: {e}")
        print("You can inspect the generated visualization code above to fix any issues manually.")

    # Narrate the story in Markdown format
    narrative_prompt = (
        f"Create a Markdown story summarizing the analysis. "
        f"Include details about the dataset, analysis, visualizations, and implications. "
        f"Use the correlation matrix."
    )
    narrative = call_ai_proxy(narrative_prompt, system_prompt)

    # Save narrative to README.md in the script's directory
    readme_path = os.path.join(script_dir, "README.md")
    with open(readme_path, "w") as f:
        f.write(narrative)
    print(f"Saved narrative as {readme_path}.")

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Analyze and visualize the CSV dataset.")
    parser.add_argument("csv_file", help="Path to the input CSV file.")
    
    # Parse arguments
    args = parser.parse_args()

    # Run the analysis with the given CSV file
    analyze_and_visualize(args.csv_file)
