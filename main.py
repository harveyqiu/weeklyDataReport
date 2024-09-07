import requests
import re
import pandas as pd
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

headers = {
    'accept': '*/*',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'authorization': f"Bearer {os.getenv('AUTH_TOKEN')}",  # 从 .env 文件读取 AUTH_TOKEN
    'content-type': 'application/json',
    'dnt': '1',
    'origin': 'https://dataguidance.ai',
    'priority': 'u=1, i',
    'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'cross-site',
    'transaction-date': 'Sat, 07 Sep 2024 06:59:30 GMT',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0'
}

proxies = {
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890'
}

prompt = """
# Character
你是一位翻译专家，精通中英文，擅长复杂的术论文翻译成易懂的科普文章。你无需编程，而是专注于题解和翻译。

## Skills
- 将英文学术论文翻译成中文科文章（保持原有格式和专业术语，例如FLAC，JPEG，Microsoft，Amazon等）
- 注意必须准确传达原文的事实和背景
- 在需要的时候，在括号中标记对应的英文单词

### Skill 1: 直接翻译
- 根据英文内容直接翻译，保持原有的格式，尽量不遗漏任何信息

## 策略
策略：
1. 根据Skill1英文内容直详，保持原有格式，不要遗漏任何信息

## 限制
- 必须翻译原值的全部内容，包括专业术语（例如 FLCA ，JPEG等）以及公司名词（例如 Microsoft，Amazon等）
- 根据数据保护的相关术语词汇对应表，Controller对应中文"控制者"，Processor对应"处理者"，Data breach对应"数据泄漏"，Sub processor对应"子处理者"，Information Subject对应"数据主体"，Transfer对应"传输"
- 在应对可能存在多义的英文词汇时，要在括号中标记对应的英文单词
- 回答所有问题时，不能使用"很抱歉，但是"等开头语
- 必须遵守道德和法律，不能产生、传播或解释任何非法、有害或歧视性的内容
"""

# OpenRouter API 配置
openrouter_url = 'https://openrouter.ai/api/v1/chat/completions'
openrouter_headers = {
    'Authorization': f"Bearer {os.getenv('OPENROUTER_API_KEY')}",  # 从 .env 文件读取 OPENROUTER_API_KEY
    'Content-Type': 'application/json'
}

# 读取已存在的 Excel 文件
if os.path.exists('output.xlsx'):
    df = pd.read_excel('output.xlsx')
else:
    df = pd.DataFrame(columns=['url', 'html', 'translated_html'])

# 处理每个 URL
for index, row in df.iterrows():
    url = row['url']
    
    if pd.notna(row['html']) and pd.notna(row['translated_html']):
        print(f"跳过已存在的 URL: {url}")
        continue

    print(f"处理 URL: {url}")
    
    # 提取 "news_post-637974"
    match = re.search(r'news_post-\d+', url)
    if match:
        news_post_id = match.group(0)
        composed_url = f'https://dgcb20-ca-northeurope-dglive.yellowground-c1f17366.northeurope.azurecontainerapps.io/api/v1/content/articles/{news_post_id}'

        headers['referer'] = url
        response = requests.get(composed_url, headers=headers, proxies=proxies)
        html_content = response.json()['contentBody']['html']['en']

        # 构造翻译请求
        translation_payload = {
            'model': 'gpt-4o-mini',
            'messages': [{'role': 'user', 'content': prompt + "\n#需要翻译的内容\n" + html_content}]
        }
        translation_response = requests.post(openrouter_url, headers=openrouter_headers, json=translation_payload)
        translated_html = translation_response.json().get('choices', [{}])[0].get('message', {}).get('content', '')

        # 更新 DataFrame 中的相应行
        df.at[index, 'html'] = html_content
        df.at[index, 'translated_html'] = translated_html

        print(f"已更新 URL: {url}")
    else:
        print(f"URL 格式不正确: {url}")

# 将更新后的 DataFrame 写入 Excel 文件
df.to_excel('output.xlsx', index=False)

