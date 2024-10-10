from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
import pandas as pd
from datetime import datetime
import re
from collections import defaultdict

class ExcelDataExtractionView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    
    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')

        if not file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Read the Excel file into a pandas dataframe
            df = pd.read_excel(file)
            print("Excel file read successfully.")
            print(f"DataFrame shape: {df.shape}")
            print(f"Columns in DataFrame: {df.columns.tolist()}")

            # Process the file based on detected format
            data = self.detect_structure(df)

            if data:
                # Convert the extracted data to an Excel file
                output_excel_file = self.convert_to_excel(data)
                response = Response({"message": "Data extracted and converted to Excel successfully."}, status=status.HTTP_200_OK)
                
                response['Content-Disposition'] = f'attachment; filename={output_excel_file}'
                return Response({"data": data}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Unrecognized format"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(f"Exception occurred: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        











    """"==========================CONVERTING TO EXCEL=================================="""


    def convert_to_excel(self, data):
        """
        Converts the extracted data (JSON format) into an Excel file
        where patient names are rows, dates are columns, and only CPT codes are values.
        Also adds DX Codes as comma-separated values if there are multiple.
        """
        # Prepare DataFrame from extracted data (patients are rows, dates are columns)
        formatted_data = {}
        dx_codes = {}
        
        # Iterate through data to extract only CPT Codes for Excel and separate DX Codes
        for patient, records in data.items():
            formatted_data[patient] = {}
            dx_code_list = []
            print('Dx code list', dx_code_list)
            
            for date, info in records.items():
                if isinstance(info, dict):  # Check if info is a dictionary
                    cpt_code = info.get('CPT Code', '')
                    dx_code = info.get('DX Code', '')
                else:
                    cpt_code = info  # If not dict, assume it's the CPT code directly
                    dx_code = ''  # No DX code available

                formatted_data[patient][date] = cpt_code  # Store only CPT code as value
                dx_code_list.append(dx_code)  # Collect DX Codes for the patient
            
            dx_codes[patient] = '/ '.join(filter(None, dx_code_list))  # Join non-empty DX Codes with comma

        # Convert formatted data to DataFrame (Transpose to make patients rows)
        df = pd.DataFrame(formatted_data).T.fillna('')  # Patients as rows, dates as columns

        # Insert the required columns
        df.insert(0, 'Insurance Name', '')    # Add empty "Insurance Name" column
        df.insert(1, 'Patient Names', df.index)  # Use the index for "Patient Names" column
        df.insert(2, 'DX Code', df.index.map(dx_codes))  # Insert the comma-separated DX codes
        df.insert(3, 'Admission Date', '')    # Add empty "Admission Date" column

        # Create an Excel writer
        output_path = 'extracted_data.xlsx'  # Specify the output file path
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            # Write the "Practice Location" text to the first row
            worksheet = writer.book.add_worksheet('Sheet1')
            worksheet.write(0, 0, 'Practice Location BAYLOR SCOTT & WHITE MEDICAL CENTER SUNNYVALE Nachawati, Samer')

            # Write the DataFrame starting from the second row
            df.to_excel(writer, sheet_name='Sheet1', startrow=1, header=True, index=False)

            # Format and adjust the columns
            header_format = writer.book.add_format({'bold': True, 'bg_color': '#ADD8E6'})  # Customize header format
            for col_num in range(len(df.columns)):
                worksheet.write(1, col_num, df.columns[col_num], header_format)  # Write header with formatting

            # Adjust column widths
            for i, col in enumerate(df.columns):
                max_length = max(df[col].astype(str).map(len).max(), len(col))  # Find max length for each column
                worksheet.set_column(i, i, max_length + 2)  # Adjust column width

            # Adjust row height for the header row
            worksheet.set_row(1, 20)  # Adjust the height of the header row

            print(f"Data successfully written to {output_path}")

        return output_path













    """"==========================DETECTING STRUCTURE OF EXCEL SHEET=================================="""


    def detect_structure(self, df):
            print("Detecting structure...")
            patient_col = self.find_column(df, ['Patient Name', 'Name', 'Client', 'Patient'])
            date_col = self.find_column(df, ['Date of Service', 'Service Date', 'DOS'])
            cpt_col = self.find_column(df, ['CPT Code', 'Code', 'Procedure Code', 'CPT'])
            dob_col = self.find_column(df, ['Patient DOB', 'DOB'])
            dx_code = self.find_column(df, ['ICD', 'DX Code', 'Diagnosis', 'ICD.1', 'ICD.2', 'ICD.3'])

            print(f"Detected columns - Patient: {patient_col}, Date: {date_col}, CPT: {cpt_col}, DOB: {dob_col}, DX Code: {dx_code}")

            if patient_col and date_col and cpt_col:
                print("Standard format detected.")
                return self.extract_standard_format(df, patient_col, date_col, cpt_col, dob_col, dx_code)

            # New logic: Check for 'Dates (December, 2023)' pattern in columns
            month_year_pattern = r"Dates\s*\((\w+),\s*(\d{4})\)"
            for col in df.columns:
                if re.match(month_year_pattern, str(col)):
                    match = re.match(month_year_pattern, str(col))
                    if match:
                        month = match.group(1)
                        year = match.group(2)
                        print(f"Month/Year pattern detected in column: {col} - {month}, {year}")
                        return self.extract_dates_pattern(df, df.columns.get_loc(col), month, year)

            # New logic for "MM/DD/YYYY" format
            date_formatted_data = self.extract_date_formatted_columns(df)
            if date_formatted_data:
                return date_formatted_data

            # If no recognizable format is found
            print("No recognizable format found.")
            return None

    











    """"==========================FINDING COLUMNS=================================="""

    def find_column(self, df, possible_names):
        """
        Finds a column by searching for potential header names anywhere in the dataframe.
        Returns the name of the first matched column if found, else None.
        """
        for col in df.columns:  # Loop through each column name in the DataFrame
            for name in possible_names:  # Loop through the list of possible names to search for
                
                
                # Step 2: Check the values inside the column for a simple substring match
                if any(name.lower() in str(cell).lower() for cell in df[col]) or name.lower() in str(col).lower().strip():
                    print(f"Column found by value match: {col}")
                    
                    return col
                
        print("No column match found for: ", possible_names)
        return None 










    """"==========================IF IN STANDARD FORMAT=================================="""


    def extract_standard_format(self, df, patient_col, date_col, cpt_col, dob_col=None, dx_code=None):
        """
        Extracts data from standard format sheets using the detected columns.
        If dx_code contains multiple columns, their values will be concatenated as a comma-separated string.
        """
        result = {}

        # Define placeholders that should be skipped
        placeholder_values = ['ICD', 'DX Code', 'Diagnosis', 'ICD.1', 'ICD.2', 'ICD.3', 'Patient DOB', 'DOB', 'CPT Code', 'Code', 'Procedure Code', 'CPT', 'Date of Service', 'Service Date', 'DOS', 'Patient Name', 'Name', 'Client', 'Patient']

        # Iterate through each row and extract the relevant data
        for i, row in df.iterrows():
            patient_name = row[patient_col]
            date_of_service = row[date_col]
            cpt_code = row[cpt_col]  # Only the CPT code will go into CPT column

            # Handle DX codes (can be one or multiple columns)
            if dx_code:
                if isinstance(dx_code, list):  # If dx_code is a list (multiple columns)
                    diagnosis_code = '/ '.join([str(row[code]) for code in dx_code if pd.notna(row[code])])
                else:
                    diagnosis_code = row[dx_code] if pd.notna(row[dx_code]) else ''
            else:
                diagnosis_code = ''  # If no dx_code column is found, set it to an empty string

            # Handle case where dob_col is not provided
            if dob_col is not None and dob_col in df.columns:
                dob = row[dob_col]
                # Concatenate patient name with DOB (format as needed)
                if pd.notna(dob):
                    full_patient_name = f"{patient_name} {dob}"
                else:
                    full_patient_name = patient_name  # If DOB is NaN, use only the patient name
            else:
                full_patient_name = patient_name  # If no DOB column, use only the patient name

            # Check for placeholder values and skip if any match
            if full_patient_name in placeholder_values or date_of_service in placeholder_values or cpt_code in placeholder_values or diagnosis_code in placeholder_values:
                print(f"Skipping row {i} with placeholder values: Patient: {full_patient_name}, Date: {date_of_service}, CPT Code: {cpt_code}, Dx Code: {diagnosis_code}")
                continue

            print(f"Row {i}: Patient: {full_patient_name}, Date of Service: {date_of_service}, CPT Code: {cpt_code}, Dx Code: {diagnosis_code}")

            if pd.notna(full_patient_name) and (pd.notna(date_of_service) or pd.notna(cpt_code)):
                if full_patient_name not in result:
                    result[full_patient_name] = {}
                result[full_patient_name][str(date_of_service)] = {
                    'CPT Code': cpt_code,  # Only CPT code here
                    'DX Code': diagnosis_code  # DX code will be added as comma-separated if multiple
                }

        # Sort the dates for each patient
        for patient, dates in result.items():
            sorted_dates = dict(sorted(dates.items()))  # Sort dates in ascending order
            result[patient] = sorted_dates

        return result












    """"==========================IF IT IS "NOT" IN STANDARD FORMAT=================================="""
    

    def extract_dates_pattern(self, df, month_year_col_idx, month, year):
        """
        Extracts data when 'Dates (December, 2023)' is in column headers,
        and the subsequent columns have days like 1, 2, 3... corresponding to CPT codes.
        """
        result = {}

        # Identify the row that contains the days (1, 2, 3...)
        days_row = df.iloc[0, month_year_col_idx + 1:]  # Assume days are on the first row after the month-year column
        start_row = 1  # Data for patients starts after the days row

        print(f"Days row identified: {days_row.tolist()}")

        # Iterate through each row starting from start_row to extract patient names and corresponding CPT codes
        for i in range(start_row, len(df)):
            row = df.iloc[i]
            patient_name = row[1]  # Assuming the patient name is in the first column

            if pd.notna(patient_name):  # If patient name is not NaN
                if patient_name not in result:
                    result[patient_name] = {}

                # Now, iterate through each day and get the corresponding CPT code
                for j, day in enumerate(days_row, start=1):
                    cpt_code = row[month_year_col_idx + j]  # CPT code column corresponding to the day

                    if pd.notna(cpt_code):  # Only process if CPT code is not NaN
                        # Convert to "YYYY-MM-DD" format
                        day_int = int(day)
                        date_str = f"{year}-{month}-{day_int}"  # Construct the date string
                        date_obj = datetime.strptime(date_str, "%Y-%B-%d")  # Convert to datetime object
                        formatted_date = date_obj.strftime("%Y-%m-%d")  # Format the date as "YYYY-MM-DD"
                        
                        result[patient_name][formatted_date] = cpt_code
                        print(f"Extracted - Patient: {patient_name}, Date: {formatted_date}, CPT Code: {cpt_code}")
            else:
                print(f"Skipping row {i}, as it does not contain a valid patient name.")

        # Sort the dates for each patient
        for patient, dates in result.items():
            sorted_dates = dict(sorted(dates.items()))  # Sort dates in ascending order
            result[patient] = sorted_dates

        # Return the result
        return result
    







        """"==========================IF DATE FORMAT "MM/DD/YYYY" IN COLUMNS=================================="""



    def extract_date_formatted_columns(self, df):
        def is_date_string(value):
            if isinstance(value, str):
                return re.match(r"\d{4}-\d{2}-\d{2}", value) is not None
            return False

        extracted_data = {}
        date_row_index = None
        patient_column_index = None

        # Debugging output
        print("Starting to scan DataFrame...")

        # Identify the row with dates and column with patient names
        for i, row in df.iterrows():
            for j, cell in row.items():
                if is_date_string(str(cell)):
                    if date_row_index is None:
                        date_row_index = i
                        print(f"Date row identified at index {i}: {cell}")
                elif isinstance(cell, str) and ',' in cell:  # Assuming a patient name contains a comma
                    patient_column_index = j
                    print(f"Patient column identified at index {j}: {cell}")

            if date_row_index is not None and patient_column_index is not None:
                break

        # If date_row_index or patient_column_index is not found, return empty result
        if date_row_index is None or patient_column_index is None:
            print("No date row or patient column found")
            return extracted_data

        # Get the date row
        date_row = df.iloc[date_row_index]
        print(f"Date row data: {date_row.to_dict()}")

        # Iterate over the rows below the date row (CPT codes are one row below patient names)
        for i in range(date_row_index + 1, len(df), 2):  # Iterate with step of 2 to handle patient and CPT rows
            patient_name = df.loc[i, patient_column_index]
            cpt_row = df.iloc[i + 1] if i + 1 < len(df) else None

            if isinstance(patient_name, str) and ',' in patient_name and cpt_row is not None:
                print(f"Processing patient: {patient_name} at row {i}")
                for j, date in enumerate(date_row):
                    if is_date_string(str(date)):
                        cpt_code = cpt_row[j]  # Access the row directly below for CPT code
                        dx_code = ""  # Add logic to extract DX code if present, otherwise leave empty

                        if pd.notna(cpt_code):
                            print(f"Found CPT code {cpt_code} for {patient_name} on {date}")
                            if patient_name not in extracted_data:
                                extracted_data[patient_name] = {}
                            extracted_data[patient_name][str(date)] = {
                                "CPT Code": cpt_code,
                                "DX Code": dx_code  # Include DX Code if you have the extraction logic for it
                            }
                        else:
                            print(f"No CPT code found for {patient_name} on {date}")

        print("Extraction complete.")
        return extracted_data




   










