import csv
import time
import psutil
from web3 import Web3, HTTPProvider


def start_listening():
    rpc = "http://localhost:8545"
    block_number = 0
    aver_time = []
    cpu_used = []

    web3 = Web3(HTTPProvider(rpc))
    web3.geth.miner.start(1)
    block_filter = web3.eth.filter('latest')
    time_now = time.time()

    while True:
        for event in block_filter.get_new_entries():
            time_next = time.time()
            block_number += 1
            print("目前处理第"+str(block_number)+'块')
            aver_time.append(time_next-time_now)
            cpu_used.append(psutil.cpu_percent(interval=1))
            if block_number == 100:
                break
            time_now = time_next
        else:
            continue
        break
    return aver_time, cpu_used


def write_head():
    path = "temp.csv"
    with open(path, "a", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['', '50块', '100块', '150块', '200块', '250块',
                         '300块', '350块', '400块', '450块', '500块'])


def save_local(list):
    path = "temp.csv"
    with open(path, "a", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(list)


def cul_data(aver_time, cpu_used):
    result = []
    dic = {}
    result.append('pow----难度1')
    for i in range(10, 110, 10):
        dic['平均出块时间'] = sum(aver_time[:i])/i
        dic['平均cpu占用率'] = sum(cpu_used[:i])/i
        result.append(str(dic))
    print(result)
    return result


if __name__ == '__main__':
    try:
        print("开始统计")
        aver_time, cpu_used = start_listening()
        print("统计结束")
        print("开始写入")
        test_list = cul_data(aver_time, cpu_used)
        write_head()
        save_local(test_list)
        print("写入完毕")
    except Exception as e:
        print(e)
