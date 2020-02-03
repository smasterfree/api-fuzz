# 命令行工具使用

基本说明

```
$ python mutate_json.py -h
usage: mutate_json.py [-h] -n NUMBER data

positional arguments:
  data                  a valid string json data

optional arguments:
  -h, --help            show this help message and exit
  -n NUMBER, --number NUMBER
                        return how many mutated jsons
```                        
 
`-n` 参数指定返回的mutated json 个数

使用demo
```
$ python mutate_json.py -n 3 '{"network": {"cidr": "20.100.0.0/16", "name": "hzx-vpc-test1", "admin_state_up": true}}'

返回：
['{"network": {"cidr": "5100.100.0.0/16", "name": "hzx-vpc-test1""hzx-vpc-test1""hzx-vpc-test1""hzx-vpc-test1""hzx-vpc-t
est1""hzx-vpc-test1", : true}}', '{"network": {"c\x90\x06\x00\x00: "20.100.0.\x18/16", "name": "hzx-vpc-test1", "admin_s
tate_up": true}}']
```
每次都会随机返回3条变异后的json。

                       