import csv
import shutil
import time
import psutil
import subprocess
import json
from web3 import Web3, HTTPProvider

global accounts
accounts = ['UTC--2022-05-22T08-22-09.180330800Z--5e84de7bd940923649a0c07759b819a994d058f1',
            'UTC--2022-05-22T08-23-18.733305800Z--3448ef40dd6efb61bbd3c0457d3006d5a42b3819',
            'UTC--2022-05-22T08-23-46.474668400Z--e064de0926b1a0eb07896e289fdaeac5ac74c42b']

def start_geth(way):
    global cmd
    process_list = []
    nodes = ['node0', 'node1', 'node2']
    http_port = ['8545', '8546', '8547']
    port = ['30303', '30304', '30305']
    log =['geth1.log','geth2.log','geth3.log']

    for i in range(3):
        if way == 'dpos':
            cmd = 'gethdpos --datadir node/'+nodes[i]+' --rpcport '+http_port[i]+' --port '+port[i]+ \
                  ' --rpc --rpcapi "web3,personal,net,eth,miner,txpool,admin" --networkid 88 ' \
                  ' --ipcdisable --nodiscover --rpccorsdomain "*"  2>log/'+log[i]
        else:
            cmd = 'geth --datadir node/'+nodes[i]+' --http.port '+http_port[i]+' --port '+port[i] + \
                  ' --allow-insecure-unlock --ipcdisable --nodiscover ' \
                  ' --http --http.api "web3,personal,net,eth,miner,txpool,admin" ' \
                  ' --http.corsdomain "*" --networkid 2859969064 2>log/'+log[i]
        process_list.append(subprocess.Popen(cmd, stdin=None, stdout=None, stderr=None, shell=True))
    return process_list


def release_node(node_list):
    for i in node_list:
        subprocess.Popen("TASKKILL /F /PID {pid} /T".format(pid=i.pid))
    time.sleep(2)


def update_genesis(way, difficulty):
    global file_name
    if way == 'pow':
        file_name = 'genesis/genesis1.json'
        with open(file_name, 'rb') as f:
            params = json.load(f)
            params['difficulty'] = difficulty
        with open(file_name, 'w') as r:
            json.dump(params, r, sort_keys=True, indent=4)
    elif way == 'poa':
        file_name = 'genesis/genesis2.json'
        with open(file_name, 'rb') as f:
            params = json.load(f)
            params['config']['clique']['period'] = difficulty
        with open(file_name, 'w') as r:
            json.dump(params, r, sort_keys=True, indent=4)
    elif way == 'dpos':
        file_name = 'genesis/genesis3.json'
        with open(file_name, 'rb') as f:
            params = json.load(f)
            params['config']['dpos']['blockInterval'] = difficulty
        with open(file_name, 'w') as r:
            json.dump(params, r, sort_keys=True, indent=4)

    return file_name


def init_node(genesis, way):
    global geth

    if way == 'dpos':
        geth = 'gethdpos'
    else:
        geth = 'geth'

    for i in range(3):
        cmd = geth+' --datadir node/node'+str(i)+' init '+genesis
        process = subprocess.Popen(cmd, stdin=None, stdout=None, stderr=None, shell=True)
        process.wait(2)
        process.kill()
        shutil.copy('accounts/'+accounts[i], 'node/node'+str(i)+'/keystore/'+accounts[i])


def rm_node():
    shutil.rmtree('node')


def start_listening(way):
    rpc_list = ['http://localhost:8545', 'http://localhost:8546', 'http://localhost:8547']
    block_number = 0
    aver_time = []
    cpu_used = []

    node0 = Web3(HTTPProvider(rpc_list[0]))
    node1 = Web3(HTTPProvider(rpc_list[1]))
    node2 = Web3(HTTPProvider(rpc_list[2]))

    node0_enode = node0.geth.admin.node_info().get('enode')
    node1_enode = node1.geth.admin.node_info().get('enode')

    print('首先启动第一个节点')
    if node0.geth.personal.unlockAccount(node0.toChecksumAddress('0x5e84de7bd940923649a0c07759b819a994d058f1'), '123', 0):
        node0.geth.miner.start()

    if node1.geth.admin.addPeer(node0_enode):
        print('node0,node1连接成功')
    if node2.geth.admin.addPeer(node0_enode):
        print('node0,node2连接成功')
    if node2.geth.admin.addPeer(node1_enode):
        print('node1,node2连接成功')

    if way == 'pow':
        pass
    else:
        print('启动第二个节点')
        if node1.geth.personal.unlockAccount(node1.toChecksumAddress('0x3448ef40dd6efb61bbd3c0457d3006d5a42b3819'), '123', 0):
            node1.geth.miner.start()

        print('启动第三个节点')
        if node2.geth.personal.unlockAccount(node2.toChecksumAddress('0xe064de0926b1a0eb07896e289fdaeac5ac74c42b'), '123', 0):
            node2.geth.miner.start()

    block_filter = node0.eth.filter('latest')
    time_now = time.time()

    while True:
        for event in block_filter.get_new_entries():
            time_next = time.time()
            block_number += 1
            print("目前处理第", block_number, '块')
            aver_time.append(time_next-time_now)
            cpu_used.append(psutil.cpu_percent(interval=1))
            if block_number == 501:
                break
            time_now = time_next
        else:
            continue
        break

    node0.geth.miner.stop()
    node1.geth.miner.stop()
    node2.geth.miner.stop()
    print('结束挖矿')
    return aver_time, cpu_used


def write_head():
    path = "result.csv"
    with open(path, "a", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['', '50块', '100块', '150块', '200块', '250块',
                         '300块', '350块', '400块', '450块', '500块'])


def save_local(list):
    path = "result.csv"
    with open(path, "a", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(list)


def cul_data(test_head, aver_time, cpu_used):
    result = []
    dic = {}
    result.append(test_head)
    for i in range(50, 550, 50):
        dic['平均出块时间'] = sum(aver_time[1:i])/i
        dic['平均cpu占用率'] = sum(cpu_used[1:i])/i
        result.append(str(dic))
    print(result)
    return result


if __name__ == '__main__':
    node_list = []
    test = [
        {'way': 'pow', 'difficulty': '0x5ffffa'}]
    test_list = [{'way': 'pow', 'difficulty': '0x2ffffd'},
                 {'way': 'pow', 'difficulty': '0x5ffffa'},
                 {'way': 'pow', 'difficulty': '0xbffff4'},
                 {'way': 'poa', 'difficulty': 5},
                 {'way': 'poa', 'difficulty': 10},
                 {'way': 'poa', 'difficulty': 15},
                 {'way': 'dpos', 'difficulty': 5},
                 {'way': 'dpos', 'difficulty': 10},
                 {'way': 'dpos', 'difficulty': 15}]
    try:
        write_head()
        for info in test_list:

            print("开始更新初始文件", info['way'], info['difficulty'])
            file_name = update_genesis(info['way'], info['difficulty'])
            print("更新成功", info['way'], info['difficulty'])

            print("开始生成node节点", info['way'], info['difficulty'])
            init_node(file_name, info['way'])
            print("生成node节点成功", info['way'], info['difficulty'])

            print("启动node", info['way'], info['difficulty'])
            node_list = start_geth(info['way'])
            print("启动成功", info['way'], info['difficulty'])

            print("开始统计", info['way'], info['difficulty'])
            aver_time, cpu_used = start_listening(info['way'])
            print("统计结束", info['way'], info['difficulty'])

            print("开始写入", info['way'], info['difficulty'])
            test_list = cul_data(info['way']+str(info['difficulty']), aver_time, cpu_used)
            save_local(test_list)
            print("写入完毕", info['way'], info['difficulty'])

            print("结束释放node节点", info['way'], info['difficulty'])
            release_node(node_list)
            print("释放成功", info['way'], info['difficulty'])

            print("删除node节点", info['way'], info['difficulty'])
            rm_node()
            print("删除成功", info['way'], info['difficulty'])

    except Exception as e:
        release_node(node_list)
        rm_node()
        print(e)

