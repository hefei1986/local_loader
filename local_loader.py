#!/usr/bin/env python
#-*- coding: utf-8 -*-
# author: hefei1986@gmail.com

import os
import sys
import threading
import time
import getopt
import commands

from utils import file_get_content

class ResultItem():
    def __init__(self, duration=0, result_len=0, start = 0, end = 0, ret_code = 0):
        self.duration = duration
        self.result_len = result_len
        self.start = start
        self.end = end
        self.ret_code = ret_code
        pass 

    def __del__(self):
        pass

class ResultData():
    def __init__(self):
        self.__result_data = []
        self.__mutex = threading.Lock()

    def __del__(self):
        pass

    def add_item(self,item):
        self.__mutex.acquire()
        self.__result_data.append(item)
        self.__mutex.release()

    def report(self):
        item_num = len(self.__result_data)
        item_duration_max = 0
        item_duration_min = 0
        
        duration_list = [item.duration for item in self.__result_data]
        request_list = [int(item.end) for item in self.__result_data ]
        result_len_list = [int(item.result_len) for item in self.__result_data ]

        #print duration_list
        #print request_list
        #print result_len_list
        
        qps_list = {}
        for item in request_list:
            if item in qps_list:
                qps_list[item] += 1
            else:
                qps_list[item] = 1
        if item_num > 0:
            item_duration_min = self.__result_data[0].duration
            item_duration_max = self.__result_data[0].duration
            item_duration_sum = 0
            for item in self.__result_data:
                item_duration_sum += item.duration
                if item.duration < item_duration_min:
                    item_duration_min = item.duration
                if item.duration > item_duration_max:
                    item_duration_max = item.duration
            
            item_duration_ave = item_duration_sum/item_num

        print '''
----------------------------------------
--------------SUMMARY------------------- 
----------------------------------------
job finished number: %s
max response time  : %s
min response time  : %s
ave response time  : %s'''%(str(item_num),str(item_duration_max),\
                          str(item_duration_min),str(item_duration_ave))



        print '------------QPS INFO--------------------'
        for k in qps_list:
            print "requests in %s is %s"%(k,qps_list[k]) 
        print '----------------END---------------------'

        pass

    __result_data = None
    __mutex = None

class CommandContainer():
    def __init__(self):
        self.__command_list = []
        self.__init__ = 0
        self.__mutex = threading.Lock()
        self.__index = 0
    
    def init(self, command_file_path):
        if not os.path.exists(command_file_path):
            return False
        str_content = file_get_content(command_file_path)
        str_content = str_content.strip()
        self.__command_list = str_content.split('\n')
        if len(self.__command_list) == 0:
            return False
        self.__num = len(self.__command_list)
        return True

    def get_command(self):
        command = ""
        self.__mutex.acquire()
        command = self.__command_list[self.__index % self.__num]
        self.__index += 1
        self.__mutex.release()
        return command
    ##私有变量
    __command_list = None
    __index = None
    __num = None
    __mutex = None

def usage():
    print '''
    python local_loader.py -c 5 -t 100 -f commands 

    -h : for help info
    -c : concurrency number
    -t : duration time [second]
    -f : commands file path

    thank you for using
    '''

#控制执行时间
run_flag = True
def timer(seconds):
    global run_flag
    time.sleep(seconds)
    run_flag = False

def job_runner(command_container, result_data):
    ''' 执行工作任务 '''
    global run_flag
    threadName = threading.currentThread().getName()
    item = None
    while run_flag:
        #(self, duration=0, result_len=0, start = 0, end = 0, ret_code = 0):
        begin = time.time()
        command = command_container.get_command()
        (ret,result) = commands.getstatusoutput(command)
        end = time.time()
        dur = end - begin
        result_len = len(result)
        item = ResultItem(duration = dur, result_len = result_len, start = begin, \
                          end = end, ret_code = ret)
        result_data.add_item(item)
        time.sleep(0.05)
        #实时打印结果
        #print "Job Thread #%s, time used: %s \t ret code: %d \t ret length: %s"%(threadName, str(dur), ret, str(result_len))
        print (threadName, str(dur), ret, str(result_len))
    return 0

def main():
    
    concurrency = None;
    duration = None;
    command_path = None;
    
    ##读取参数 
    try:
        opts, args = getopt.getopt(sys.argv[1:],"hc:t:f:",[])
    except getopt.GetoptError, e:
        usage()
        sys.exit(0)
    
    for k,v in opts:
        if k == '-h':
            usage()
            sys.exit(0)
        
        if k == '-c':
            concurrency = int(v)
        
        if k == '-t':
            duration = int(v) 
        
        if k == '-f':
            command_path = str(v)

    if None == concurrency or None == duration or None == command_path:
        usage()
        sys.exit(0) 

    ##读取命令文件
    job_container = CommandContainer()
    ret = job_container.init(command_path)
    if not ret:
        print "init command file error :%s", (command_path,)
        sys.exit(0)
    #准备好ResultData，用以统计
    result_data =ResultData()
    
    #创建工作线程
    threads = []
    for x in xrange(0, concurrency):
        threads.append(threading.Thread(target=job_runner, args=(job_container, result_data)))
    threads.append(threading.Thread(target=timer, args=(duration,)))
    for t in threads:
        t.start()

    for t in threads:
        t.join()
    result_data.report()

def test():
    pass

if "__main__" == __name__:
    main()
