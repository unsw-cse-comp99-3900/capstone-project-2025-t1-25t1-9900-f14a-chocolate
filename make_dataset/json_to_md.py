"""
自动提取澳大利亚各大学的入学要求信息。它利用 OpenAI GPT 从已有的课程信息 JSON 文件中提取入学要求，并将其存储为 Markdown (.md) 格式的文件。
"""

import numpy as np
import pandas as pd
import os
import json
import re
import openai
import requests
from aiohttp import ClientSession
import sys
import time
import concurrent.futures
import argparse
import math

amb2std_dict = {
    '32_adelaide': 'University of Adelaide (UoA)',
    '12_SCU': 'Southern Cross University (SCU)',
    '05_CSU': 'Charles Sturt University (CSU)',
    '14_canberra': 'University of Canberra (UoC)',
    'USYD': 'University of Sydney (USYD)',
    'UTS': 'University of Technology Sydney (UTS)',
    '26_flinders': 'Flinders University (FU)',
    '17_notredame': 'University of Notre Dame Australia (UNDA)',
    '06_DEAKIN': 'Deakin University (DU)',
    '07_Federation': 'Federation University Australia (FedUni)',
    '01_ACU': 'Australian Catholic University (ACU)',
    '09_latrobe': 'La Trobe University (LTU)',
    '02_ANU': 'Australian National University (ANU)',
    '08_Griffith': 'Griffith University (GU)',
    '30_rmit': 'RMIT University (RMIT)',
    '16_UNSW': 'University of New South Wales (UNSW)',
    '18_unisa': 'University of South Australia (UniSA)',
    '25_ecu': 'Edith Cowan University (ECU)',
    '04_CQU': 'Central Queensland University (CQU)',
    '21_uwa': 'University of Western Australia (UWA)',
    '33_divinity': 'University of Divinity (UoD)',
    '13_torrens': 'Torrens University Australia (TUA)',
    
    '03_BOND': 'Bond University (BOND)',
    '11_QUT': 'Queensland University of Technology (QUT)',
    '15_unimelb': 'University of Melbourne (Unimelb)',
    '19_USC': 'University of the Sunshine Coast (USC)',
    '20_UTAS': 'University of Tasmania (UTAS)',
    '22_cmu': 'Carnegie Mellon University (CMU)',
    '23_cdu': 'Charles Darwin University (CDU)',
    '24_curtin': 'Curtin University (Curtin)',
    '27_James_Cook_university': 'James Cook University (JCU)',
    '28_mq': 'Macquarie University (MQ)',
    '29_Murdoch_Uni': 'Murdoch University (Murdoch Uni)',
    '31_swinburne': 'Swinburne University of Technology (Swinburne)',
    '34_une': 'University of New England (UNE)',
    '35_newcastle': 'University of Newcastle (Newcastle)',
    '36_uq': 'University of Queensland (UQ)',
    '37_UniSQ': 'University of Southern Queensland (UniSQ)',
    #'39_uts': 'University of Technology Sydney (UTS)',
    '40_uow': 'University of Wollongong (UOW)',
    '41_Westerns_sydney_UNI': 'Western Sydney University (Western Sydney UNI)',
    '42_victoria_uni': 'Victoria University (Victoria Uni)'
}

Extract_Requirements_Prompt_Template = '''
### Task
Your task is to read [Materials] and extract the entry requirements related information. Because the [Materials] is too long, so you can only read the 1/3 part. Although you can't read the whole [Materials], you can still extract useful information from the part you read.

### Materials
{materials}

### Important Notes
1. The key words indicating entry requirements are: "entry requirements", "requirement", "requirements", "eligibility", "admission", etc.
2. Pay attention to the requirement for different group of students, e.g., domestic, international, etc.
3. Dont' farbicate information, only extract the information from the materials.
4. If you can't find the information, you can leave it blank.
5. Response using formatted, clear, structural markdown text.

### Response Format
```markdown
Extracted Information:
{{Your extracted information here ...}}
```
'''


aig_dev_key='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'
os.environ['OPENAI_API_KEY'] = aig_dev_key



def GPT_QA(prompt, model_name="gpt-3.5-turbo", t=0.0,historical_qa=None):
    #gpt-3.5-turbo-16k
    #gpt-3.5-turbo
    openai.api_key =os.environ["OPENAI_API_KEY"]
    MAX_CONTENT_QUESTIONS = 1

    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {openai.api_key}"}

    messages=[]
    answer = ['token limits reached for this prototype, please try with a different question fits for a smaller scope.']
    if historical_qa!=None:
        for (q,a) in historical_qa[-MAX_CONTENT_QUESTIONS:]:
            messages.append({"role": "user", "content": q})
            messages.append({"role": "assistant", "content": a})   
    
    messages.append({"role": "user", "content": prompt})
    data = {
        "model": model_name,
        "messages": messages,
        "temperature": t,
        "n": 1,
    }

    response = requests.post(url, headers=headers, json=data)
    try:
        answer = response.json()["choices"][0]["message"]["content"]
    except KeyError:
        print("Token limits reached.")

    return answer


def process(begin=0,end=1):
    #检查requirement folder是否存在, exist ok 
    os.makedirs('requirement', exist_ok=True)
    end=min(end,len(amb2std_dict))

    for amb_uni_name,std_uni_name in list(amb2std_dict.items())[begin:end]:
        #创建folder
        os.makedirs(f'requirement/{amb_uni_name}', exist_ok=True)
        
        #if degree_info folder exists
        if os.path.exists(f'dataset/{amb_uni_name}/degree_info'):
            #dataset/{amb_uni_name}/degree_info 下面有啥文件夹，就在requirement/{amb_uni_name}/degree_info 下创建对应的文件夹
            for folder in os.listdir(f'dataset/{amb_uni_name}/degree_info'):
                os.makedirs(f'requirement/{amb_uni_name}/degree_info/{folder}', exist_ok=True)
        
        #if any of 07 08 18 26 27 28 36 UTS USYD not in  amb_uni_name          
        if amb_uni_name not in ['07_Federation','08_Griffith','18_unisa','26_flinders','27_James_Cook_university','28_mq','36_uq','UTS','USYD']:
            #对于dataset/{amb_uni_name}/degree_info 下面的所有一层level的文件夹进行遍历
            for folder in os.listdir(f'dataset/{amb_uni_name}/degree_info'):
                #对于每一个文件夹下的所有文件进行遍历
                for degree_file in os.listdir(f'dataset/{amb_uni_name}/degree_info/{folder}'):
                    md_file = degree_file.replace('.json', '.md')
                    md_path=f'requirement/{amb_uni_name}/degree_info/{folder}/{md_file}'
                    #如果文件已经存在，那么跳过
                    if os.path.exists(md_path):
                        #print(f'File {md_file} already exists. Skip.')
                        continue
                    
                    #否则，开始提取信息
                    print(f'Extracting information for dataset/{amb_uni_name}/degree_info/{folder}/{degree_file} ...')

                    #如果文件名不是以.json结尾，那么跳过
                    if not degree_file.endswith('.json'):
                        continue
                    else:
                        #读取文件
                        with open(f'dataset/{amb_uni_name}/degree_info/{folder}/{degree_file}', 'r', encoding='utf-8') as f:
                            degree_info = json.load(f)
                        
                        degree_info_str = json.dumps(degree_info)
                        
                        #按照degree_info的长度，平均切3份，循环
                        #统计degree_info_str的长度，设置max_chunk_size=16000*3, 然后计算切分的份数，取天花板
                        max_chunk_size=16000*3
                        chunk_num= math.ceil(len(degree_info_str)/max_chunk_size)
                        degree_info_parts = [degree_info_str[i:i + len(degree_info_str)//chunk_num] for i in range(0, len(degree_info_str), len(degree_info_str)//chunk_num)]
                        extracted_information_list = []
                        for degree_info_part in degree_info_parts:
                            #给gpt, 提取出entry requirements
                            Extract_Requirements_Prompt=Extract_Requirements_Prompt_Template.format(materials=degree_info_part)
                            response=GPT_QA(Extract_Requirements_Prompt, model_name="gpt-4o-mini", t=0.0,historical_qa=None)
                            #提取出信息, 看看他第一行是不是```markdown
                            if response.startswith('```markdown'):
                                extracted_information = response.split('```markdown')[1].split('```')[0].strip()
                                extracted_information=extracted_information.split('Extracted Information:')[1].strip()
                            else:
                                #再试一次
                                response=GPT_QA(Extract_Requirements_Prompt, model_name="gpt-4o-mini", t=0.0,historical_qa=None)
                                if response.startswith('```markdown'):
                                    extracted_information = response.split('```markdown')[1].split('```')[0].strip()
                                    extracted_information=extracted_information.split('Extracted Information:')[1].strip()
                                else:
                                    extracted_information = 'No information extracted'
                            extracted_information_list.append(extracted_information)
                        
                        #将信息存储
                        extracted_information_all = ''''''
                        for index in range(len(extracted_information_list)):
                            extracted_information_all += f'Part {index + 1}:\n{extracted_information_list[index]}\n\n'

                        #写入文件
                        #文件名为degree_file.md
                        
                        with open(f'requirement/{amb_uni_name}/degree_info/{folder}/{md_file}', 'w', encoding='utf-8') as f:
                            f.write(extracted_information_all)
                        
                        print(f'Extracted information for \'{degree_file}\' has been saved.')
        elif amb_uni_name in ['07_Federation','08_Griffith','18_unisa','26_flinders','27_James_Cook_university','28_mq','36_uq']:
            #对于dataset/{amb_uni_name}/degree_info/domestic, and dataset/{amb_uni_name}/degree_info/international 下面的所有一层level的文件夹进行遍历
            for student in ['domestic','international']:
                for folder in os.listdir(f'dataset/{amb_uni_name}/degree_info/{student}'):
                    #对于每一个文件夹下的所有文件进行遍历
                    for degree_file in os.listdir(f'dataset/{amb_uni_name}/degree_info/{student}/{folder}'):
                        md_file = degree_file.replace('.json', '.md')
                        md_path=f'requirement/{amb_uni_name}/degree_info/{student}/{folder}/{md_file}'
                        #如果文件已经存在，那么跳过
                        if os.path.exists(md_path):
                            #print(f'File {md_file} already exists. Skip.')
                            continue

                        #否则，开始提取信息
                        print(f'Extracting information for dataset/{amb_uni_name}/degree_info/{student}/{folder}/{degree_file} ...')
                        
                        #创建folder
                        os.makedirs(f'requirement/{amb_uni_name}/degree_info/{student}/{folder}', exist_ok=True)

                        #如果文件名不是以.json结尾，那么跳过
                        if not degree_file.endswith('.json'):
                            continue
                        else:
                            #读取文件
                            with open(f'dataset/{amb_uni_name}/degree_info/{student}/{folder}/{degree_file}', 'r', encoding='utf-8') as f:
                                degree_info = json.load(f)
                            
                            degree_info_str = json.dumps(degree_info)
                            
                            #按照degree_info的长度，平均切3份，循环
                            #统计degree_info_str的长度，设置max_chunk_size=16000*3, 然后计算切分的份数，取天花板
                            max_chunk_size=16000*3
                            chunk_num= math.ceil(len(degree_info_str)/max_chunk_size)
                            degree_info_parts = [degree_info_str[i:i + len(degree_info_str)//chunk_num] for i in range(0, len(degree_info_str), len(degree_info_str)//chunk_num)]
                            extracted_information_list = []
                            for degree_info_part in degree_info_parts:
                                #给gpt, 提取出entry requirements
                                Extract_Requirements_Prompt=Extract_Requirements_Prompt_Template.format(materials=degree_info_part)
                                response=GPT_QA(Extract_Requirements_Prompt, model_name="gpt-4o-mini", t=0.0,historical_qa=None)
                                #提取出信息, 看看他第一行是不是```markdown
                                if response.startswith('```markdown'):
                                    extracted_information = response.split('```markdown')[1].split('```')[0].strip()
                                    extracted_information=extracted_information.split('Extracted Information:')[1].strip()
                                else:
                                    #再试一次
                                    response=GPT_QA(Extract_Requirements_Prompt, model_name="gpt-4o-mini", t=0.0,historical_qa=None)
                                    if response.startswith('```markdown'):
                                        extracted_information = response.split('```markdown')[1].split('```')[0].strip()
                                        extracted_information=extracted_information.split('Extracted Information:')[1].strip()
                                    else:
                                        extracted_information = 'No information extracted'
                                extracted_information_list.append(extracted_information)
                            
                            #将信息存储
                            extracted_information_all = ''''''
                            for index in range(len(extracted_information_list)):
                                extracted_information_all += f'Part {index + 1}:\n{extracted_information_list[index]}\n\n'

                            #写入文件
                            #文件名为degree_file.md
                            
                            with open(f'requirement/{amb_uni_name}/degree_info/{student}/{folder}/{md_file}', 'w', encoding='utf-8') as f:
                                f.write(extracted_information_all)
                            
                            print(f'Extracted information for \'{degree_file}.{student}\' has been saved.')
            
            
        elif amb_uni_name in ['UTS','USYD']:
            #对于每一个文件夹下的所有文件进行遍历
            for degree_file in os.listdir(f'dataset/{amb_uni_name}'):
                md_file = degree_file.replace('.json', '.md')
                md_path=f'requirement/{amb_uni_name}/{md_file}'
                #如果文件已经存在，那么跳过
                if os.path.exists(md_path):
                    #print(f'File {md_file} already exists. Skip.')
                    continue
                
                #否则，开始提取信息
                print(f'Extracting information for dataset/{amb_uni_name}/{degree_file} ...')

                #如果文件名不是以.json结尾，那么跳过
                if not degree_file.endswith('.json'):
                    continue
                else:
                    #读取文件
                    with open(f'dataset/{amb_uni_name}/{degree_file}', 'r', encoding='utf-8') as f:
                        degree_info = json.load(f)
                    
                    degree_info_str = json.dumps(degree_info)
                    
                    #按照degree_info的长度，平均切3份，循环
                    #统计degree_info_str的长度，设置max_chunk_size=16000*3, 然后计算切分的份数，取天花板
                    max_chunk_size=16000*3
                    chunk_num= math.ceil(len(degree_info_str)/max_chunk_size)
                    degree_info_parts = [degree_info_str[i:i + len(degree_info_str)//chunk_num] for i in range(0, len(degree_info_str), len(degree_info_str)//chunk_num)]
                    extracted_information_list = []
                    for degree_info_part in degree_info_parts:
                        #给gpt, 提取出entry requirements
                        Extract_Requirements_Prompt=Extract_Requirements_Prompt_Template.format(materials=degree_info_part)
                        response=GPT_QA(Extract_Requirements_Prompt, model_name="gpt-4o-mini", t=0.0,historical_qa=None)
                        #提取出信息, 看看他第一行是不是```markdown
                        if response.startswith('```markdown'):
                            extracted_information = response.split('```markdown')[1].split('```')[0].strip()
                            extracted_information=extracted_information.split('Extracted Information:')[1].strip()
                        else:
                            #再试一次
                            response=GPT_QA(Extract_Requirements_Prompt, model_name="gpt-4o-mini", t=0.0,historical_qa=None)
                            if response.startswith('```markdown'):
                                extracted_information = response.split('```markdown')[1].split('```')[0].strip()
                                extracted_information=extracted_information.split('Extracted Information:')[1].strip()
                            else:
                                extracted_information = 'No information extracted'
                        extracted_information_list.append(extracted_information)
                    
                    #将信息存储
                    extracted_information_all = ''''''
                    for index in range(len(extracted_information_list)):
                        extracted_information_all += f'Part {index + 1}:\n{extracted_information_list[index]}\n\n'

                    #写入文件
                    #文件名为degree_file.md
                    
                    with open(f'requirement/{amb_uni_name}/{md_file}', 'w', encoding='utf-8') as f:
                        f.write(extracted_information_all)
                    
                    print(f'Extracted information for \'{degree_file}\' has been saved.')
            
                       
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--begin', type=int, help='begin')
    parser.add_argument('--end', type=int, help='end')
    args = parser.parse_args()
    process(args.begin,args.end)
    