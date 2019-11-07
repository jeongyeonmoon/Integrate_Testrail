# -*- coding: utf-8 -*-


import datetime
import sys
from TestRailApi import APIClient
from jsonpath_rw import jsonpath, parse

#
server_url = 'https://ygy.testrail.io' # YGY TestRail server
project_id = 2 # YGY Regression Test Project
plan_name = 'YGY Regression Test Plan (Run by Automation) ' + str(datetime.datetime.now())

# test result value
# 1	Passed
# 2	Blocked
# 3	Untested (not allowed when adding a result)
# 4	Retest
# 5	Failed

RESULT_PASSED = 1
RESULT_FAILED = 5

# API request method : 사용하지 않음, TestRailApi.py 로 대체함
# headers = {'Content-Type': 'application/json', 'Authorization': 'Basic cm5kX2NoX3FlQGRlbGl2ZXJ5aGVyby5jby5rcjpxd2VyMTIzNCE='}
#
# def request_testrail_api(api_url, api_method, params):
#
#     request_url = server + api_url
#     resp = {}
#     if api_method == 'GET':
#         headers['Content-Type'] = 'application/json'
#         resp = requests.get(request_url, headers=headers, params=params)
#     elif api_method == 'POST':
#         if api_url[:14] == 'add_attachment':  # 파일 첨부
#             print(params)
#             resp = requests.post(request_url, headers=headers, files=params)
#             print(resp.json())
#         else:
#             headers['Content-Type'] = 'application/json'
#             resp = requests.post(request_url, headers=headers, data=params)
#     else:
#         return resp
#
#     response_json = resp.json()
# #    print(response_json)
#     return response_json

# ============================================= 0. API Object 생성 =============================================
tr = APIClient(server_url)

# ============================================= 1. Plan 생성 =============================================

# project가 갖고 있는 suite list 얻어오기
result = tr.send_get('get_suites/' + str(project_id))
dummy_dic = { 'dummy': result }
jsonpath_expression = parse('$.dummy[*].id')
suite_list = [match.value for match in jsonpath_expression.find(dummy_dic)]
print(suite_list)


# plan 생성하기
result = tr.send_post('add_plan/' + str(project_id), '{ "name": "' + plan_name + '" }')
plan_id = result.get("id")
print(plan_id)


# plan 안에 suite 별로 run 생성하기
for suite in suite_list:
    param = '{ "suite_id": "' + str(suite) + '" }'
    tr.send_post('add_plan_entry/' + str(plan_id), param)


# ============================================= 2. Plan 에 포함된 automated test 정보 저장 =============================================

# test 정보 저장하기

# run list 가져오기
result = tr.send_get('get_plan/' + str(plan_id))
jsonpath_expression = parse('$.entries[*].runs[*].id')
run_list = [match.value for match in jsonpath_expression.find(result)]
print(run_list)

# 각 run에 속한 test 정보 조회하여 automated test list 생성

automated_test_list = []
for run in run_list:
    url = 'get_tests/' + str(run)
    test_list = tr.send_get(url)

    for test in test_list:
        if test.get("custom_testname") is not None:  # 자동화 테스트 정보가 있는 것만
            automated_test = dict(test_id=test.get("id"), classname=test.get("custom_classname"), testname=test.get("custom_testname"))
            automated_test_list.append(automated_test)

print(automated_test_list)


# ============================================= 3. test result 업데이트 =============================================

# failed tests 파일 읽어오기

# 서버 경로를 가져와서 실행하는 것으로 변경해야 함
reportsDirectory = sys.argv[1]
txt_path = reportsDirectory + "/flavors/GOOGLE/testrail/failedTestList.txt"

#txt_path = "/Users/a201710007/PycharmProjects/Integrate_Testrail/failedTestList.txt"

f = open(txt_path)
failed_test_list = f.read().splitlines()
print(failed_test_list)
f.close()


# automated test lis 에 test result 정보 추가하기

for automated_test in automated_test_list:
    if automated_test['testname'] in failed_test_list:
        automated_test['result'] = 'failed'
    else:
        automated_test['result'] = 'passed'

print(automated_test_list)


# test 결과 업데이트하기

for automated_test in automated_test_list:
    if automated_test['result'] == 'passed':
        param = '{ "status_id": "' + str(RESULT_PASSED) + '" }'
        tr.send_post('add_result/' + str(automated_test.get("test_id")), param)  # test result update
    elif automated_test['result'] == 'failed':
        param = '{ "status_id": "' + str(RESULT_FAILED) + '" }'
        result = tr.send_post('add_result/' + str(automated_test.get("test_id")), param)  # test result update
        result_id = result["id"]
        print(result_id)
        # 스크린샷 첨부 (스크린샷 경로 저장하는 코드 추가해야 함)
        file_path = '/Users/a201710007/Downloads/f.jpg'
        result = tr.send_post('add_attachment_to_result/' + str(result_id), file_path)  # file attach
        print(result)









