import shutil
import subprocess
from openai import  OpenAI
import pandas as pd
import re
import unicodedata
import os


client = OpenAI(
    base_url='xxx',
    api_key='xxx',
)

def matchFunc(target_function, stripped, next_stripped, next_next_stripped):


    pattern = r'\b' + target_function + r'\b'
    if re.search(pattern, stripped) and \
            (stripped.endswith(('{', '{\n')) or
             (stripped.endswith((')\n', ')', ') ')) and next_stripped.startswith(('{', '{\n'))) or
             (stripped.endswith((', ', ',', ',\n', ', \n')) and next_stripped.endswith(('{', '{\n'))) or
             (stripped.endswith((', ', ',', ',\n', ', \n')) and next_stripped.endswith(
                 (')', ')\n')) and next_next_stripped.startswith(('{', '{\n')))):
        return True
    return False


def replace_c_function(file_path, target_function, new_function_code):
    if not os.path.exists(file_path): 
        return 0, "File does not exist. Skipping..."
    with open(file_path, 'r') as file:
        lines = file.readlines()


    function_start = None
    function_end = None
    indent = None
    covered = ""
    function_start, function_end, covered = find_c_functionByDefine(lines, target_function)
    if function_start is None or function_end is None:
        print(f"in {file_path} not find fun {target_function}")
        return 0, covered

    covered = '\n'.join(lines[function_start:function_end + 1])
    new_lines = lines[:function_start] + [new_function_code + '\n'] + lines[function_end + 1:]

    with open(file_path, 'w') as file:
        file.writelines(new_lines)

    print(f"success replace fun {target_function}")
    return 1, covered


def find_function_end(text, start_line):
    brace_stack = []

    if not isinstance(text, list):
        text = text.split('\n')

    for i in range(start_line, len(text)):
        line = text[i]

        for char in line:
            if char == '{':
                brace_stack.append(char)
            elif char == '}':
                if brace_stack:
                    brace_stack.pop()
                    if not brace_stack:
                        return i  

    return None


def find_c_function(text, target_function):

    function_start = None
    function_end = None
    brace_stack = []
    if not isinstance(text, list):
        text = text.split('\n')
    for i, line in enumerate(text):
        stripped = line.lstrip()
        split_line = stripped.split("(")

        next_line = text[i + 1] if i + 1 < len(text) else "Blank"
        next_stripped = next_line.lstrip()
        next_next_line = text[i + 2] if i + 2 < len(text) else "Blank"
        next_next_stripped = next_next_line.lstrip()

        if matchFunc(target_function, stripped, next_stripped, next_next_stripped):
            function_start = i
            if split_line[0]== target_function:
                function_start -=1
        elif function_start is not None:
            function_end = find_function_end(text, function_start)
            break

    if function_start is not None and function_end is not None:
        return function_start, function_end, '\n'.join(text[function_start:function_end + 1])
    return None, None, ""

def find_c_functionByDefine(text, target_function):

    function_start = None
    function_end = None
    brace_stack = []
    if not isinstance(text, list):
        text = text.split('\n')
    for i, line in enumerate(text):
        stripped = line.lstrip()
        split_line = stripped.split("(")

        if target_function in stripped and line == stripped:
            function_start = i
            if split_line[0] == target_function:
                function_start -= 1
        elif function_start is not None:
            function_end = find_function_end(text, function_start)
            break

    if function_start is not None and function_end is not None:
        return function_start, function_end, '\n'.join(text[function_start:function_end + 1])
    return None, None, ""

import subprocess
import time


def exacutLinux(command, cwd):
    timeout = 30 * 60
    returncode = -1  # Default return code

    try:

        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd,
                                 timeout=timeout)

        if "test" in command:
            inform = process.stdout.decode()
        else:
            inform = process.stderr.decode()
        returncode = process.returncode
    except subprocess.TimeoutExpired:
        inform = ' '.join(command) + " Command timed out, moving on to the next one."

    return returncode, inform



def replace_function_and_compile(file_path, function_name, new_function_code,cwd):
   
    build_dir="/redis/src"
    state, covered = replace_c_function(file_path, function_name, new_function_code)

    if state == 0: return 0, "fun replace fail", None

    compile_command = ["make","clean"]
    
    returncode, inform = exacutLinux(compile_command, build_dir)

    compile_command2 = ["make"]
    returncode, inform = exacutLinux(compile_command2, build_dir)

    if returncode != 0:  

        return 1, inform, covered
    
    test_command = ["make", "test"]
    returncode, inform = exacutLinux(test_command, build_dir)
    if returncode != 0:  

        return 2, inform, covered
    else:

        return 3, "test success!", covered



def askChatGPT(model, messages,max_retries=3, delay=30):
    
    completion = client.chat.completions.create(
    messages=messages,
    model=model,
    )

    return completion.choices[0].message.content





import json

def chunk_messages(messages, max_length=16385):
    total_length = sum(len(msg["content"]) for msg in messages)
    if total_length <= max_length:
        return messages

    truncated_messages = []
    current_length = 0
    for msg in messages:
        if current_length + len(msg["content"]) <= max_length:
            truncated_messages.append(msg)
            current_length += len(msg["content"])
        else:
            remaining_length = max_length - current_length
            truncated_content = msg["content"][:remaining_length]
            truncated_messages.append({"role": msg["role"], "content": truncated_content})
            break  
    print(truncated_messages)
    return truncated_messages


def askChatGPT_with_retry(model, messages,max_retries=30, delay=30):
    max_length=16385
    messages = chunk_messages(messages, max_length)
    for i in range(max_retries):
        try:

            chat_completion = client.chat.completions.create(
            messages=messages,
            model=model,
            )
            return chat_completion.choices[0].message.content  
        except Exception as e:

            print(f"request fail the {i + 1}/{max_retries}. error: {e}")
            time.sleep(delay)  

    raise Exception("Max retries reached, failed to get a valid response from the API.")




def clean_text(text):

    lines = text.split('\n')

    clean_lines = [line for line in lines if not re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', line)]
    clean_lines = [line for line in clean_lines if '[34mCC' not in line]

    clean_text = '\n'.join(clean_lines)

    return clean_text

def check_and_release_port(inform):  #

    if "Starting test server at port" in inform and "couldn't open socket: address already in use" in inform:

        port_match = re.search(r"Starting test server at port (\d+)", inform)
        if port_match:
            port_number = port_match.group(1)

            netstat_command = f"netstat -tuln | grep {port_number}"
            process = subprocess.run(netstat_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output = process.stdout


            return True, False  
    return False, False  


import random



def shuffle_multiline(cell_content):
    lines = cell_content.split('\n')  
    lines = [line for line in lines if line.strip() != '']  
    random.shuffle(lines)  

    return '\n'.join(lines)  


if __name__ == '__main__':
    numOfInter = 5  
    testModel = "gpt-4-0125-preview"  # gpt-3.5-turbo   gpt-4 gpt-4-0125-preview

    root_path = "/redis/" 
    sourceCode_path = "src/"
    sourceCode_path_copy="src_copy/"


    dataFile = root_path + "complete_original_input_redis_pp_p1.xlsx"
    resultFile = root_path + testModel + "_complete_original_input_redis_pp_p1.xlsx"

    columns = ["fileName", "funcName", "function_header","initialInput"] 

    df_testSample = pd.read_excel(dataFile, names=columns)
    df_testSample = df_testSample.fillna("")  

    resultFile_df = pd.DataFrame()

    for i in range(numOfInter):
        resultFile_df['v' + str(i + 1) + 'code'] = ''
        resultFile_df['v' + str(i + 1) + 'Inform'] = ''
        resultFile_df['v' + str(i + 1) + 'Response'] = ''
        resultFile_df['v' + str(i + 1) + 'covered'] = ''
    resultFile_df['Messages'] = ''
    codeGenPrompt = "From now on, you play the role of the  C code generator, "\
                    "You can generate the objective function code according to the function description provided by" \
                    " the user. " \
                    " Please do not return anything other than the target code.  \n" \
                    "The process is as follows: \n[prompt-input]\n[output]\n"

    for index, row in df_testSample.iterrows():



        fileName = row['fileName']
        inputMessage = row['initialInput']

        funcName = row['funcName']
        function_header = row['function_header']
        messages = [{"role": "system", "content": codeGenPrompt}] 

        temp = {"role": "user", "content": inputMessage}
        messages.append(temp)

        for i in range(numOfInter):


            original_file_name = root_path + sourceCode_path + fileName
            original_src_name = root_path + sourceCode_path +"redis/"
            new_src_name = root_path + sourceCode_path_copy+"redis/"
            
            shutil.rmtree(original_src_name)
            shutil.copytree(new_src_name,original_src_name,dirs_exist_ok=True)



            print(funcName + "the " + str(i + 1) + " chat")

            response = askChatGPT_with_retry(testModel, messages)

            if "InvalidRequestError" in response:
                inform = "openai.error.InvalidRequestError: This model's maximum context length is 4097 tokens. "
                print(funcName + inform)
                resultFile_df.at[index, 'v' + str(i + 1) + 'Inform'] = inform
                resultFile_df.at[index, 'v' + str(i + 1) + 'Response'] = response
                continue

            codeStart, codeEnd, code = find_c_function(response, funcName)

            if code == "":
                inform = "can't find code from response"
                print(funcName + " can't find code from response")
                resultFile_df.at[index, 'v' + str(i + 1) + 'Inform'] = inform
                resultFile_df.at[index, 'v' + str(i + 1) + 'Response'] = response
                continue

            state, inform, covered = replace_function_and_compile(original_file_name, funcName, code, root_path)

            inform = clean_text(inform) 
            if state == 0:  
                inform = "not find the fun\n" + inform
                resultFile_df.at[index, 'v' + str
                (i + 1) + 'Inform'] = inform
                break
            elif state == 1: 

                inform = inform.split('\n')
                inform = [line for line in inform if "modifier ignored since" not in line]
                inform = '\n'.join(inform)

                temp = {"role": "assistant", "content": response}
                messages.append(temp)
                error = "[prompt-errors]\n" + inform + "\n[output]"
                temp = {"role": "user", "content": error}
                messages.append(temp)
                inform = "compile fail\n" + inform

            elif state == 2:
                inform = "test fail\n" + inform

            elif state == 3:
                inform = "test success \n" + inform

            resultFile_df.at[index, 'v' + str(i + 1) + 'covered'] = covered
            resultFile_df.at[index, 'v' + str(i + 1) + 'code'] = code
            resultFile_df.at[index, 'v' + str(i + 1) + 'Inform'] = inform
            resultFile_df.at[index, 'v' + str(i + 1) + 'Response'] = response

            if state == 3: break  


        resultFile_df.at[index, 'Messages'] = messages
        resultFile_df.to_excel(resultFile, index=False)


        zhanYong, jieChu = check_and_release_port(inform)
        if zhanYong:
            time.sleep(600)
            zhanYong, jieChu = check_and_release_port(inform)
            if zhanYong : break










