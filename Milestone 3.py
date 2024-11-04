import openai
import streamlit as st
import pandas as pd
import easyocr
from PIL import Image
import matplotlib.pyplot as plt
import seaborn as sns
import re

# Set OpenAI API key
openai.api_key = 'API-KEY-HERE'

# Initialize the EasyOCR reader
reader = easyocr.Reader(['en'])

# Set up the Streamlit page
st.set_page_config(page_title="Water Quality Monitor Dashboard", page_icon="🌊", layout="wide")
st.title("🌊 Water Quality Monitor Dashboard")
st.write("This dashboard provides a real-time overview of water quality parameters with analysis tools for environmental monitoring.")

# Sidebar section for data input
st.sidebar.header("Water Quality Parameter Input")
st.sidebar.write("Upload a file or enter values manually for analysis.")

# Single file upload option in the sidebar
uploaded_file = st.sidebar.file_uploader(
    "Upload Water Quality Data (CSV, Excel, JSON, PNG, or JPEG)", 
    type=["csv", "xlsx", "xls", "json", "png", "jpeg", "jpg"]
)

# Determine if manual data input is needed
manual_data = not uploaded_file

# Initialize parameter values
parameter_values = {
    'pH': None,
    'Temperature': None,
    'Turbidity': None,
    'Dissolved Oxygen': None,
    'Conductivity': None
}

# Function to process image files with EasyOCR
def extract_text_from_image(uploaded_image):
    image = Image.open(uploaded_image)
    results = reader.readtext(image, detail=0)
    return "\n".join(results)

# Helper function to extract the first numeric value from a text line
def extract_numeric_value(text):
    match = re.search(r'(\d+(\.\d+)?)', text)
    if match:
        return float(match.group(0))
    return None

# Get parameter values from file or manual input
if manual_data:
    # Manual input section for each parameter if no file is uploaded
    st.sidebar.write("Or, enter values manually:")
    parameter_values['pH'] = st.sidebar.slider("pH Level", 0.0, 14.0, 7.0)
    parameter_values['Temperature'] = st.sidebar.slider("Temperature (°C)", 0.0, 50.0, 25.0)
    parameter_values['Turbidity'] = st.sidebar.slider("Turbidity (NTU)", 0.0, 100.0, 5.0)
    parameter_values['Dissolved Oxygen'] = st.sidebar.slider("Dissolved Oxygen (mg/L)", 0.0, 15.0, 8.0)
    parameter_values['Conductivity'] = st.sidebar.slider("Conductivity (µS/cm)", 0.0, 2000.0, 500.0)
else:
    # If a file is uploaded, process the file and extract values for `parameter_values`
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    try:
        if file_extension == 'csv':
            df = pd.read_csv(uploaded_file)
            st.write("Uploaded CSV Data:")
            st.dataframe(df)
        elif file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(uploaded_file)
            st.write("Uploaded Excel Data:")
            st.dataframe(df)
        elif file_extension == 'json':
            df = pd.read_json(uploaded_file)
            st.write("Uploaded JSON Data:")
            st.dataframe(df)
        elif file_extension in ['png', 'jpeg', 'jpg']:
            # Load the image and apply OCR with EasyOCR
            extracted_text = extract_text_from_image(uploaded_file)
            st.write("Extracted Text from Image:")
            st.write(extracted_text)
            
            # Attempt to extract specific parameters based on keywords
            lines = extracted_text.split('\n')
            for line in lines:
                if 'pH' in line:
                    parameter_values['pH'] = extract_numeric_value(line)
                elif 'Temperature' in line or 'temp' in line.lower():
                    parameter_values['Temperature'] = extract_numeric_value(line)
                elif 'Turbidity' in line:
                    parameter_values['Turbidity'] = extract_numeric_value(line)
                elif 'Dissolved Oxygen' in line or 'Oxygen' in line:
                    parameter_values['Dissolved Oxygen'] = extract_numeric_value(line)
                elif 'Conductivity' in line:
                    parameter_values['Conductivity'] = extract_numeric_value(line)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

# Function for parameter analysis
def analyze_parameter(parameter, value, safe_min, safe_max, unit, insights, recommendations):
    if value is None:
        return f"{parameter} data is not available."
    analysis = f"{parameter}: {value} {unit}. "
    if (safe_min is None or value >= safe_min) and (safe_max is None or value <= safe_max):
        analysis += f"This is within the safe range ({safe_min} - {safe_max} {unit} where applicable). {insights}"
    else:
        if safe_min is not None and value < safe_min:
            analysis += f"The value is too low and below the safe range ({safe_min} - {safe_max} {unit})."
        elif safe_max is not None and value > safe_max:
            analysis += f"The value is too high and exceeds the safe range ({safe_min} - {safe_max} {unit})."
        analysis += f" {recommendations}"
    return analysis

# Define `analysis_texts` after `parameter_values` have been set
analysis_texts = {
    "pH": analyze_parameter("pH", parameter_values['pH'], 6.5, 8.5, "", 
                            "pH levels between 6.5 and 8.5 support biodiversity.", 
                            "Consider adding pH buffers if out of range."),
    "Temperature": analyze_parameter("Temperature", parameter_values['Temperature'], None, 35, "°C", 
                                     "Temperature below 35°C avoids stress on aquatic life.", 
                                     "Consider using aeration or shading."),
    "Turbidity": analyze_parameter("Turbidity", parameter_values['Turbidity'], None, 5, "NTU", 
                                   "Low turbidity indicates clear water.", 
                                   "Implement sediment control if high."),
    "Dissolved Oxygen": analyze_parameter("Dissolved Oxygen", parameter_values['Dissolved Oxygen'], 6, 10, "mg/L", 
                                          "Ideal dissolved oxygen range for aquatic health.", 
                                          "Consider aeration if levels are low."),
    "Conductivity": analyze_parameter("Conductivity", parameter_values['Conductivity'], None, 1000, "µS/cm", 
                                      "Conductivity under 1000 µS/cm is suitable for freshwater.", 
                                      "Check for potential pollutants if high.")
}

# Display the detailed analysis and recommendations
for param, analysis in analysis_texts.items():
    st.write(f"### {param} Analysis")
    st.write(analysis)

# If a file is uploaded, display the source of the data for context
if not manual_data:
    st.info("The above analysis and recommendations are based on data extracted from the uploaded file.")