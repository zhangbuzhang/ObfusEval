import pandas as pd
import re
# Modified function to extract only the function name
def extract_function_info(signature):
    # Adjust the regex to capture the function name and parameters part, ignoring return type and any modifiers
    pattern = r'\b(\w+)\s*\(([^)]*)\)'
    # Use search instead of match, because match starts matching from the beginning of the string, while search searches for the first occurrence of the pattern throughout the string.
    match = re.search(pattern, signature)
    if match:
        # Return the function name and parameters list
        return match.group(1), match.group(2)
    else:
        # If no match, return None
        return None, None

# Reload the Excel files with the newly uploaded paths
file_path_original_new = "~/LLM_test/work/libvips/libvips_selectedFunc_context_original.xlsx"
file_path_rewrite_new = "~/LLM_test/dataset/libvips/original/rewriteComSelectFuncContext.xlsx"
# Read the data again
df_original_new = pd.read_excel(file_path_original_new)
df_rewrite_new = pd.read_excel(file_path_rewrite_new)

flag = 0
for index, row in df_original_new.iterrows():
    for index1, row1 in df_rewrite_new.iterrows():
        if row["fileName"] == row1["file_path"] and extract_function_info(row["function_header"])[0] == extract_function_info(row1["function_header"])[0]:
            df_original_new.at[index, 'comments'] = row1["contextGenByGpt"]
            flag += 1

print(flag)
df_original_new.to_excel("~/LLM_test/work/libvips/temp.xlsx")
