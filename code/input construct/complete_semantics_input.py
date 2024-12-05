

import pandas as pd

import random

def read_excel_subsheet(file_path, sheet_name, column_names):

    try:
        
        xl = pd.ExcelFile(file_path)  
       
        if sheet_name in xl.sheet_names:
        
            df = xl.parse(sheet_name, names=column_names)
            return df
        else:
            
            return None
    except Exception as e:
        
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


def remove_empty_lines(code):
    lines = code.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    return '\n'.join(non_empty_lines)

def remove_comments(code):
    lines = code.split('\n')
    code_without_comments = []
    in_comment = False
    for line in lines:
        if '/*' in line:
            in_comment = True
            if '*/' in line:
                in_comment = False
        elif '*/' in line:
            in_comment = False
            continue
        if not in_comment and '//' in line:
            line = line.split('//')[0]
        if not in_comment:
            code_without_comments.append(line)
    return '\n'.join(code_without_comments)

def truncate_code(code):
    lines = code.split('\n')
    if len(lines) > 30:
        code = '\n'.join(lines[:10])
    else:
        code = '\n'.join(lines[:len(lines)//3])
    return code


def process_code(code):
    code = remove_empty_lines(code)
    code = remove_comments(code)
    code = truncate_code(code)
    return code


import json
def main():

    repoName = "libvips"
    root_path = "~/LLM test\work/"+repoName+"/"
    funcFile = root_path + repoName +"_selectedFunc_context_semantics.xlsx"
    dataFile = root_path + repoName + "_context_original.xlsx"
    resultFile = root_path + repoName + "_complete_semantics_input.xlsx"

    function_df = pd.read_excel(funcFile)
    context_column_names = ["fileName", "funcName", "calledFunctions", "usedStructs","usedGloVars","usedMacros"]

    context_df = read_excel_subsheet(dataFile,"context",context_column_names)
    context_df = context_df.drop(columns = ['fileName']) 
    # function_df = pd.merge(function_df, context_df, on='funcName', how='inner')
    # function_df.to_excel("demo.xlsx")
    sheet_globalVar = "globalVar"  
    column3_names = ["gloVarName", "gloVarDef"] 
    globalVar_df = read_excel_subsheet(dataFile, sheet_globalVar, column3_names)    
    
    sheet_macro = "macro" 
    column4_names = ["fileName", "macroName", "macroDef"] 

    macro_df = read_excel_subsheet(dataFile, sheet_macro, column4_names)    
    
    sheet_struct = "struct"  
    column5_names = ["structName", "structDef"] 
    struct_df = read_excel_subsheet(dataFile, sheet_struct, column5_names)    
    new_df = pd.DataFrame(columns=['fileName', 'funcName', 'function_header', 'initialInput','partCode','fullCode'])

    initialPrompt = "Here is the functional description and function declaration of the code,Please help me complete the code in C language:\n"
    
    for index, row in function_df.iterrows():
        filename = row['fileName']
        funcName = row['funcName']
        comment = row['contextGenByGpt']
        function_header = row['function_header']
        confusedCode = row['function_code']
        calledFunctions = row['calledFunctions']
        usedStructs = row['usedStructs']
        usedGloVars = row['usedGloVars']
        usedMacros = row['usedMacros']
    
        
        partCode = row['partCode_semantics']
    
        callFuc_list = get_comments_for_called_functions(calledFunctions, function_df)   
        usedStructs_list = get_def_for_used_items(usedStructs, struct_df,'structName','structDef')
        usedGloVars_list = get_def_for_used_items(usedGloVars, globalVar_df,'gloVarName','gloVarDef')
        usedMacros_list = get_def_for_used_items(usedMacros, macro_df,'macroName','macroDef')
        
        initialInput = "" \
                       + "\n This is objective Function Description:\n " + str(comment) \
                       + "\n This is the code for the function that needs to be completed:\n " + str(partCode) + "\n // Here is the code that needs to be completed.\n }\n "\
                       + "\n This is the context that may be needed to complement the objective function :\n "  \
                       + "\n This is a list of functions that may be used:\n " + str(callFuc_list) \
                       + "\n This is a list of structs that may be used:\n " + str(usedStructs_list) \
                       + "\n This is a list of macros that may be used:\n " + str(usedMacros_list) \
                       + "\n This is a list of global variables that may be used:\n " + str(usedGloVars_list) \
                       + "\n"      
        # new_data = {'fileName': filename, 
        #             'funcName': funcName, 
        #             'function_header': function_header, 
        #             'initialInput': initialInput}         
        new_df.loc[len(new_df)] = {'fileName': filename, 'funcName': funcName, 'function_header': function_header, 'initialInput': initialInput,'partCode':partCode, 'fullCode':confusedCode}
           
  
    new_df.to_excel(resultFile, index=False)

    print("New DataFrame saved as function_data.csv")                   
         

if __name__ == '__main__':
    main()
