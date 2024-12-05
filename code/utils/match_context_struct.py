
import pandas as pd

import random

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
        print("Failed to read Excel file: ", e)
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
        comments_list.append("{} {}".format(function_header, funcComment))
        
    num_to_select = len(called_functions_list)
    selected_indices = set()
    while len(selected_indices) < num_to_select:
        index = random.randint(0, len(function_df) - 1)
        function_header = function_df.iloc[index]['function_header']
        funcComment = function_df.iloc[index]['comments']              
        comments = "{} {}".format(function_header, funcComment)
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
            def_list.append("No definition found for {}".format(item_name))
    num_to_select = len(used_items_list)
    selected_indices = set()
    while len(selected_indices) < num_to_select:
        index = random.randint(0, len(df) - 1)
        if index not in selected_indices and df.iloc[index][item_def_col] not in def_list:
            def_list.append(df.iloc[index][item_def_col])
            selected_indices.add(index)
    return def_list

import re
def extract_function_info(signature):

    pattern = r'\b(\w+)\s*\(([^)]*)\)'
    match = re.search(pattern, signature)
    if match:
        return match.group(1), match.group(2)
    else:
        return None, None

def check_match(funcName, function_header):
    newfuncName = funcName.replace(" ", "")
    newfuncName1 = '*{}'.format(newfuncName)
    newfuncName2 = '\n{}'.format(newfuncName)
    
    if funcName in function_header:
        return function_header

    if newfuncName1 in function_header:
        return function_header

    if newfuncName2 in function_header:
        return function_header
    
    return None

import json

def main():
    Version = "struct"
    repoName = "libvips"
    
   funcFile = "~/LLM_test/work/libvips/libvips_success_struct.xlsx"
    commentFile = "~/LLM_test/work/libvips/libvips_selectedFunc_context_original.xlsx"
    dataFile = "~/LLM_test/work/libvips/libvips_context_struct.xlsx"
    resultFile = "~/LLM_test/work/libvips/libvips_selectedFunc_context_struct.xlsx"
    column1_names = ["fileName", "funcName", "function_header", "function_code", "comments", "contextGenByGpt", "calledFunctions", "usedStructs", "usedGloVars", "usedMacros"]
    context_column_names = ["fileName", "funcName", "calledFunctions", "usedStructs", "usedGloVars", "usedMacros"]  

    allFunction_df = read_excel_subsheet(commentFile, "Sheet1", column1_names)
    context_df = read_excel_subsheet(dataFile,"context",context_column_names)
    function_df = pd.read_excel(funcFile)
    function_df = function_df.drop_duplicates()
    function_df = function_df.assign(
        funcName = '',
        comments = '',
        contextGenByGpt = '',
        calledFunctions = '', 
        usedStructs = '',
        usedGloVars = '',
        usedMacros = '',
        to_delete = '',
        match_found = ''
    )

    function_df['funcName'] = function_df['function_header'].apply(lambda x: extract_function_info(x)[0] if extract_function_info(x) else None)
    function_df['match_found'] = function_df.apply(lambda row: check_match(row['funcName'], row['function_header']), axis=1)


    context_df['funcName'] = context_df['funcName'].apply(lambda x: f" {x}(")
    # context_df['function_header'] = context_df['funcName'].apply(lambda x: check_match(x, function_df['function_header']))
    context_df['funcName'] = context_df['funcName'].str.strip().str.rstrip('(').str.lstrip()

    flag = 0
    flag1 = 0
    for index,row in function_df.iterrows():
        bb = False
        for index1,row1 in allFunction_df.iterrows():
            # if extract_function_info(row1["function_header"])[0] == extract_function_info(row["function_header"])[0]:
            #     print(row["funcName"])
            if row1["funcName"] == row["funcName"] and row1["fileName"] == row["fileName"] and row1["function_header"] == row["function_header"]:
                function_df.at[index, 'comments'] = row1['comments']
                function_df.at[index, 'contextGenByGpt'] = row1['contextGenByGpt']
                bb = True
                flag = flag+1
        if not bb:
            # print(row["funcName"])
            function_df.at[index, 'to_delete'] = True
            flag1 = flag1 + 1
    print(flag)
    print(flag1)
    function_df = function_df.drop(function_df[function_df['to_delete'] == True].index)

    flag = 0
    flag1 = 0
    for index,row in function_df.iterrows():
        bb = False
        for index1,row1 in context_df.iterrows():
            # if extract_function_info(row1["function_header"])[0] == extract_function_info(row["function_header"])[0]:
            #     print(row["funcName"])
            if row1["funcName"] == row["funcName"] and row1["fileName"] in row["fileName"]:
                function_df.at[index, 'calledFunctions'] = row1['calledFunctions']
                function_df.at[index, 'usedStructs'] = row1['usedStructs']
                function_df.at[index, 'usedGloVars'] = row1['usedGloVars']
                function_df.at[index, 'usedMacros'] = row1['usedMacros']
                bb = True
                flag = flag+1
        if not bb:
            # print(row["funcName"])
            function_df.at[index, 'to_delete'] = True
            flag1 = flag1 + 1
    print(flag)
    print(flag1)
    function_df = function_df.drop(function_df[function_df['to_delete'] == True].index)
    function_df.drop(columns=['to_delete'], inplace=True)
    function_df.to_excel(resultFile)

    sheet_globalVar = "globalVar" 
    column3_names = ["fileName","gloVarName", "gloVarDef"]

    globalVar_df = read_excel_subsheet(dataFile, sheet_globalVar, column3_names)    
    
    sheet_macro = "macro"  
    column4_names = ["fileName", "macroName", "macroDef"] 
 
    macro_df = read_excel_subsheet(dataFile, sheet_macro, column4_names)    
    
    sheet_struct = "struct"  
    column5_names = ["structName", "structDef"] 

    struct_df = read_excel_subsheet(dataFile, sheet_struct, column5_names)    
    new_df = pd.DataFrame(columns=['fileName', 'funcName', 'function_header', 'initialInput'])



    for index, row in context_df.iterrows():
        filename = row['fileName']
        funcName = row['funcName']
        comment = row['contextGenByGpt']
        function_header = row['function_header']
        calledFunctions = row['calledFunctions']
        usedStructs = row['usedStructs']
        usedGloVars = row['usedGloVars']
        usedMacros = row['usedMacros']
        callFuc_list = get_comments_for_called_functions(calledFunctions, allFunction_df)   
        usedStructs_list = get_def_for_used_items(usedStructs, struct_df,'structName','structDef')
        usedGloVars_list = get_def_for_used_items(usedGloVars, globalVar_df,'gloVarName','gloVarDef')
        usedMacros_list = get_def_for_used_items(usedMacros, macro_df,'macroName','macroDef')
        
        initialInput = "" \
                       + "\n This is objective Function Description:\n " + str(comment) \
                       + "\n This is the declaration of the objective function:\n " + str(function_header) \
                       + "\n This is the context that may be needed to generate the objective function:\n "  \
                       + "\n This is a list of functions that may be used:\n " + str(callFuc_list) \
                       + "\n This is a list of structs that may be used:\n " + str(usedStructs_list) \
                       + "\n This is a list of macros that may be used:\n " + str(usedMacros_list) \
                       + "\n This is a list of global variables that may be used:\n " + str(usedGloVars_list) \
                       + "\n"      
        # new_data = {'fileName': filename, 
        #             'funcName': funcName, 
        #             'function_header': function_header, 
        #             'initialInput': initialInput}         
        new_df.loc[len(new_df)] = {'fileName': filename, 'funcName': funcName, 'function_header': function_header, 'initialInput': initialInput}
           
  
    new_df.to_excel(resultFile, index=False)

    print("New DataFrame saved as function_data.csv")    

if __name__ == '__main__':
    main()

        