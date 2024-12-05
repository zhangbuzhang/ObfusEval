import pandas as pd
import random
import re

def read_excel_subsheet(file_path, sheet_name, column_names):
    try:
        xl = pd.ExcelFile(file_path)
        if sheet_name in xl.sheet_names:
            df = xl.parse(sheet_name, names=column_names)
            return df
        else:
            print(f"Subsheet '{sheet_name}' does not exist.")
            return None
    except Exception as e:
        print(f"Failed to read Excel file: {e}")
        return None

def get_comments_for_called_functions(calledFunctions, function_df):
    if pd.notna(calledFunctions):
        called_functions_list = calledFunctions.split(",")
    else:
        called_functions_list = []

    comments_list = []
    for func_name in called_functions_list:
        matched_row = function_df[function_df['funcName'] == func_name.strip()]
        if not matched_row.empty:
            function_header = matched_row['function_header'].iloc[0]
            funcComment = matched_row['comments'].iloc[0]
        else:
            function_header = func_name
            funcComment = "/**/"
        comments_list.append(f"{function_header} {funcComment}")
        
    num_to_select = len(called_functions_list)
    selected_indices = set()
    while len(selected_indices) < num_to_select:
        index = random.randint(0, len(function_df) - 1)
        function_header = function_df.iloc[index]['function_header']
        funcComment = function_df.iloc[index]['comments']
        comments = f"{function_header} {funcComment}"
        if index not in selected_indices and function_df.iloc[index]['comments'] not in comments_list:
            comments_list.append(comments)
            selected_indices.add(index)
        
    return comments_list

def get_def_for_used_items(used_items, df, item_name_col, item_def_col):
    if pd.notna(used_items):
        used_items_list = used_items.split(",")
    else:
        return []

    def_list = []
    for item_name in used_items_list:
        matched_row = df[df[item_name_col] == item_name.strip()]
        if not matched_row.empty:
            def_list.append(matched_row[item_def_col].iloc[0])
        else:
            def_list.append("No definition found for " + item_name)
    num_to_select = len(used_items_list)
    selected_indices = set()
    while len(selected_indices) < num_to_select:
        index = random.randint(0, len(df) - 1)
        if index not in selected_indices and df.iloc[index][item_def_col] not in def_list:
            def_list.append(df.iloc[index][item_def_col])
            selected_indices.add(index)
    return def_list

def extract_function_info(signature):
    pattern = r'\b(\w+)\s*\(([^)]*)\)'
    match = re.search(pattern, signature)
    if match:
        return match.group(1), match.group(2)
    else:
        return None, None

def check_match(funcName, function_header):
    newfuncName = funcName.replace(" ", "")
    newfuncName1 = '*' + newfuncName
    newfuncName2 = '\n' + newfuncName
    
    if funcName in function_header:
        return function_header
    if newfuncName1 in function_header:
        return function_header
    if newfuncName2 in function_header:
        return function_header
    return None

def main():
    Version = "original"
    repoName = "fluent"
    funcFile = "~/LLM_test/work1/" + repoName + "/needTest_" + repoName + "_new.xlsx"
    dataFile = "~/LLM_test/work1/" + repoName + "/" + repoName + "_context_" + Version + ".xlsx"
    resultFile = "~/LLM_test/work1/" + repoName + "/" + repoName + "_needTest_new.xlsx"
    column1_names = ["fileName", "funcName", "comments", "function_header", "Implementation"]
    context_column_names = ["fileName", "funcName", "calledFunctions", "usedStructs", "usedGloVars", "usedMacros"]

    allFunction_df = read_excel_subsheet(dataFile, "function", column1_names)
    context_df = read_excel_subsheet(dataFile, "context", context_column_names)
    function_df = pd.read_excel(funcFile)
    function_df = function_df.drop_duplicates()
    function_df = function_df.assign(comments='', to_delete='')

    context_df['funcName'] = context_df['funcName'].apply(lambda x: f" {x}(")
    context_df['funcName'] = context_df['funcName'].str.strip().str.rstrip('(').str.lstrip()

    flag = 0
    flag1 = 0
    for index, row in function_df.iterrows():
        bb = False
        for index1, row1 in allFunction_df.iterrows():
            if row1["funcName"] == row["funcName"] and row1["fileName"] in row["file_path"]:
                function_df.at[index, 'comments'] = row1['comments']
                function_df.at[index, 'function_code'] = row1['Implementation']
                bb = True
                flag += 1
        if not bb:
            function_df.at[index, 'to_delete'] = True
            flag1 += 1

    function_df = function_df.drop(function_df[function_df['to_delete'] == True].index)
    function_df.drop(columns=['to_delete'], inplace=True)
    function_df.to_excel(resultFile)

if __name__ == '__main__':
    main()
