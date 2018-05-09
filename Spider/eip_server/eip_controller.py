import sys
import time
import json
import logging
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.cvm.v20170312 import cvm_client

from eip_server.config import secret_id, secret_key

"""
通过腾讯云api来管理腾讯云eip资源
此处的主要目的：通过更换弹性ip以应对豆瓣关于ip的反爬策略
"""

# 日志监控
log_fmt = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'
logging.basicConfig(filename='log/eip.log', level=logging.INFO, format=log_fmt)


def client_instance(region="ap-guangzhou"):
    """
    实例化要请求产品(以cvm为例)的client对象
    :param region: 地区
    :return:
    """
    try:
        # 实例化一个认证对象
        cred = credential.Credential(secret_id, secret_key)
        client = cvm_client.CvmClient(cred, region)

        return client

    except TencentCloudSDKException as err:
        logging.warning(err)
        sys.exit(1)


def check_eip(client):
    """
    查询弹性公网IP列表
    :param client: client对象
    :return:
    {
      "Response": {
        "TotalCount": 1,
        "AddressSet": [
          {
            "AddressId": "eip-hxlqja90",
            "AddressName": "test",
            "AddressIp": "123.121.34.33",
            "AddressStatus": "BINDED",
            "InstanceId": "ins-m2j0thu6",
            "NetworkInterfaceId": null,
            "PrivateAddressIp": null,
            "IsArrears": False,
            "IsBlocked": False,
            "CreatedTime": "2017-09-12T07:52:00Z"
          }
        ],
        "RequestId": "3c140219-cfe9-470e-b241-907877d6fb03"
      }
    }
    """
    try:
        # 通过client对象调用想要访问的接口，需要传入参数
        resp = client.call('DescribeAddresses', {})
        return json.loads(resp)

    except TencentCloudSDKException as err:
        logging.warning(err)
        sys.exit(1)


def check_eip_quota(client):
    """
    查询弹性公网IP配额
    :param client: client对象
    :return:
    {
        "Response": {
            {
                'QuotaSet': [
                {'QuotaId': 'TOTAL_EIP_QUOTA', 'QuotaCurrent': 0, 'QuotaLimit': 20},
                {'QuotaId': 'DAILY_EIP_APPLY', 'QuotaCurrent': 0, 'QuotaLimit': 40},
                {'QuotaId': 'DAILY_EIP_ASSIGN','QuotaCurrent': 0, 'QuotaLimit': 40},
                 ]
            }
            "RequestId": "6EF60BEC-0242-43AF-BB20-270359FB54A7"
        }
    }
    """
    try:
        # 通过client对象调用想要访问的接口，需要传入参数
        resp = client.call('DescribeAddressQuota', {})
        return json.loads(resp)

    except TencentCloudSDKException as err:
        logging.warning(err)
        sys.exit(1)


def create_eip(client, num=1):
    """
    创建弹性公网IP
    :param client: client对象
    :param num: 创建数目
    :return:
    {
        "Response": {
            "AddressSet": [
                "eip-m44ku5d2"
            ],
            "RequestId": "6EF60BEC-0242-43AF-BB20-270359FB54A7"
        }
    }
    """
    try:
        if num > 5 or num < 1:
            raise TencentCloudSDKException(message='创建弹性公网ip不能超过5或者低于1')

        querystring = {
            'Version': '2017-03-12',
            'AddressCount': num
        }

        resp = client.call('AllocateAddresses', querystring)
        return json.loads(resp)
    except TencentCloudSDKException as err:
        logging.warning(err)


def release_eip(client, address_id):
    """
    释放弹性公网IP
    :param client: client对象
    :param address_id: eip id
    :return:
    {
        "Response": {
            "RequestId": "6EF60BEC-0242-43AF-BB20-270359FB54A7"
        }
    }
    """
    try:
        querystring = {
            'Version': '2017-03-12',
            'AddressIds.0': address_id
        }

        resp = client.call('ReleaseAddresses', querystring)
        return json.loads(resp)
    except TencentCloudSDKException as err:
        logging.warning(err)
        sys.exit(1)


def bind_eip(client, address_id, instance_id):
    """
    绑定弹性公网IP
    :param client: client对象
    :param address_id: eip id
    :param instance_id: 实例id
    :return:
    {
        "Response": {
            "RequestId": "3c140219-cfe9-470e-b241-907877d6fb03"
        }
    }
    """
    try:
        querystring = {
            'Version': '2017-03-12',
            'AddressId': address_id,
            'InstanceId': instance_id
        }

        resp = client.call('AssociateAddress', querystring)
        return json.loads(resp)
    except TencentCloudSDKException as err:
        logging.warning(err)
        sys.exit(1)


def unbind_eip(client, address_id):
    """
    解绑定弹性公网IP
    :param client: client对象
    :param address_id: eip id
    :return:
    {
        "Response": {
            "RequestId": "3c140219-cfe9-470e-b241-907877d6fb03"
        }
    }
    """
    try:
        querystring = {
            'Version': '2017-03-12',
            'AddressId': address_id,
        }

        resp = client.call('DisassociateAddress', querystring)
        return json.loads(resp)
    except TencentCloudSDKException as err:
        logging.warning(err)
        sys.exit(1)


def get_eip_information(eip_dict):
    """
    从查询得到的弹性公网IP列表获取当前绑定着eip的实例的实例id及其eip_id
    :param eip_dict: 查询得到的弹性公网IP列表
    :return: instance_id 和 eip_id
    """
    binded_result = []
    unbinded_result = []

    address_set = eip_dict['AddressSet']
    for address in address_set:
        if address['AddressStatus'] == 'BIND':
            binded_result.append({
                'address_id': address['AddressId'],
                'address_ip': address['AddressIp'],
                'instance_id': address['InstanceId'],
                'create_time': address['CreatedTime']
            })
        else:
            unbinded_result.append({
                'address_id': address['AddressId'],
                'address_ip': address['AddressIp'],
                'create_time': address['CreatedTime']
            })

    return binded_result


def wait_for_unbind(client, address_id):
    """
    等待实例解绑eip成功
    :param client: client对象
    :param address_id: eip id
    :return:
    """
    while True:
        eip_dict = check_eip(client)['Response']
        address_set = eip_dict['AddressSet']
        for address in address_set:
            if address['AddressId'] == address_id and address['AddressStatus'] == 'UNBIND':
                time.sleep(5)
                return

        time.sleep(1)


def wait_for_release(client, address_id):
    """
    等待实例释放eip成功
    :param client: client对象
    :param address_id: eip id
    :return:
    """
    while True:
        eip_dict = check_eip(client)['Response']
        address_set = eip_dict['AddressSet']
        if address_id in [address['AddressId'] for address in address_set]:
            time.sleep(1)
        else:
            time.sleep(5)
            return


def wait_for_create(client, address_id):
    """
    等待实例创建eip成功
    :param client: client对象
    :param address_id: eip id
    :return:
    """
    while True:
        eip_dict = check_eip(client)['Response']
        address_set = eip_dict['AddressSet']
        if address_id in [address['AddressId'] for address in address_set]:
            time.sleep(5)
            return
        else:
            time.sleep(1)


def wait_for_bind(client, address_id):
    """
    等待实例解绑eip成功
    :param client: client对象
    :param address_id: eip id
    :return:
    """
    while True:
        eip_dict = check_eip(client)['Response']
        address_set = eip_dict['AddressSet']
        for address in address_set:
            if address['AddressId'] == address_id and address['AddressStatus'] == 'BIND':
                time.sleep(5)
                return

        time.sleep(1)


def eip_worker(instance_id='ins-kvcaedtu'):
    """
    解绑并释放当前eip，创建并绑定eip
    :return:
    """
    client = client_instance()

    try:
        eip_dict = check_eip(client)['Response']
        bind_eip_list, unbind_eip_list = get_eip_information(eip_dict)

        for bind_eip_element in bind_eip_list:
            # 对于绑定着指定实例的eip进行解绑和释放
            if bind_eip_element['InstanceId'] == instance_id:
                unbind_eip(client, bind_eip_element['address_id'])
                logging.info('实例{}解绑ip为{},id为{}的eip'.format(
                    bind_eip_element['instance_id'],
                    bind_eip_element['address_ip'],
                    bind_eip_element['address_id']))

                wait_for_unbind(client, bind_eip_element['address_id'])
                release_eip(client, bind_eip_element['address_id'])
                logging.info('释放ip为{},id为{}的eip'.format(
                    bind_eip_element['address_ip'],
                    bind_eip_element['address_id']))

                wait_for_release(client, bind_eip_element['address_id'])

                # 释放所有没有绑定的eip
                for unbind_eip_element in unbind_eip_list:
                    release_eip(client, unbind_eip_element['address_id'])
                    logging.info('释放ip为{},id为{}的eip'.format(
                        unbind_eip_element['address_ip'],
                        unbind_eip_element['address_id']))

                    wait_for_release(client, unbind_eip_element['address_id'])

                # 创建一个新的eip
                new_eip = create_eip(client)['Response']['AddressSet'][0]
                logging.info('创建id为{}的eip'.format(new_eip))
                wait_for_create(client, new_eip)

                # 绑定新创建的eip
                bind_eip(client, new_eip, instance_id)
                logging.info('实例{}绑定id为{}的eip'.format(instance_id, new_eip))
                wait_for_bind(client, new_eip)

    except TencentCloudSDKException as err:
        logging.warning(err)
        sys.exit(1)
    except Exception as ex:
        logging.warning(ex)
        sys.exit(1)


# 主程序
if __name__ == '__main__':
    eip_worker()
