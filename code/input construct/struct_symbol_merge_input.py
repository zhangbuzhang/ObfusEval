import pandas as pd
import re
def replace_macros(initialInput, all_dict_df, original_col, confused_col):
    for index, row in all_dict_df.iterrows():
        used_macros = row[original_col]
        used_macros_confused = row[confused_col]
        if pd.notnull(used_macros) and used_macros.strip() and used_macros_confused.strip():
            pattern = r"\b" + re.escape(used_macros) + r"\b"
            initialInput = re.sub(pattern, used_macros_confused, initialInput)
    return initialInput

root_path = "~\LLM test\work\\"
version = "libvips"
semantic_df = pd.read_excel(root_path+version+"\\"+version+"_struct_input.xlsx", usecols=["fileName", "funcName",  "function_header",  "initialInput"])   #fileName	funcName	function_header	initialInput

all_dict_df = pd.read_excel(root_path+version+"\\"+"all_dict_struct_se_"+version+".xlsx", usecols=["Function", "Function_confused", "Used_Macros", "Used_Macros_confused", "Used_Global_Vars", "Used_Global_Vars_confused", "Used_Structs", "Used_Structs_confused"])


# Iterate over each row in semantic_df
for index, row in semantic_df.iterrows():
    initialInput = row["initialInput"]
    # Iterate over each row in all_dict_df to replace Used_Macros
    initialInput = replace_macros(initialInput, all_dict_df, "Used_Macros", "Used_Macros_confused")
    initialInput = replace_macros(initialInput, all_dict_df, "Function", "Function_confused")
    initialInput = replace_macros(initialInput, all_dict_df, "Used_Global_Vars", "Used_Global_Vars_confused")
    initialInput = replace_macros(initialInput, all_dict_df, "Used_Structs", "Used_Structs_confused")
    semantic_df.at[index, "initialInput"] = initialInput

semantic_df.to_excel(root_path+version+"\\"+version+"_struct_symbol_input.xlsx", index=False)

