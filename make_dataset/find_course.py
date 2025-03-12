"""
爬取取澳大利亚天主教大学（ACU, Australian Catholic University）官网的课程手册（Handbook 2024），并提取课程相关信息，保存为 JSON 格式的文件。
"""
import re
import os
import json

import feapder
from feapder.utils.log import log
from tqdm import tqdm

from utils.process import progress


# https://www.acu.edu.au/Handbook/Handbook-2024/unit/PHIL623


def get_task():
    course_codes = []
    for folder in tqdm(os.listdir('json_data')):
        for file in os.listdir(os.path.join('json_data', folder)):
            with open(os.path.join('json_data', folder, file), 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            j1 = ''
            j2 = ''
            try:
                j1 = json.dumps(json_data["domestic"]["course_rules"]["course_rules_data"])
            except:
                pass
            try:
                j2 = json.dumps(json_data["international"]["course_rules"]["course_rules_data"])
            except:
                pass
            course_codes.extend(re.findall(r"'https://www\.acu\.edu\.au/Handbook/Handbook-2024/unit/(.*?)'", j1 + j2))

    finish = [i.replace('.json', '') for i in os.listdir('course_json')]
    return [i for i in set(course_codes) if i not in finish]


class Main(feapder.AirSpider):
    __custom_setting__ = dict(
        LOG_LEVEL='INFO'
    )
    os.makedirs('course_json', exist_ok=True)

    def __init__(self, thread_count=None):
        super().__init__(thread_count)

    def start_requests(self):
        codes = get_task()
        progress.add_tasks(len(codes))
        for code in codes:
            yield feapder.Request(
                # https://www.acu.edu.au/Handbook/Handbook-2024/unit/PHIL623?campus=Please+select%0A%0A
                f'https://www.acu.edu.au/handbook/handbook-2024/unit/{code}?campus=Please+select%0A%0A',
                code=code
            )

    def download_midware(self, request):
        request.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Connection': 'Close'
        }

    def parse(self, request, response):
        data_str = response.xpath('//*[@id="main-content"]/div/section').extract_first()
        if not data_str:
            log.warning(f'无数据 | url={request.url}')
            return
        find = re.findall(r'<h3>\s*(.*?)\s*</h3>\s*(.*?)\s*(?=<h3>|$)', data_str, re.S)
        if not find:
            log.warning(f'无数据 | url={request.url}')
            return

        data = dict(
            course_url=request.url,
            course_code=request.code
        )
        data.update(dict(find))
        with open(os.path.join('course_json', f'{request.code}.json'), encoding='utf-8', mode='w') as f:
            json.dump(data, f, ensure_ascii=False)

    def end_callback(self):
        super().end_callback()


if __name__ == '__main__':
    # print(get_task())
    Main(thread_count=4).start()
