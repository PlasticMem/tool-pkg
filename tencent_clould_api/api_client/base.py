#!/usr/bin/env python
# -*- coding:utf-8 -*-

import abc
import time
import json
import hmac
import hashlib
import requests
import aiohttp
from datetime import datetime
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException


class BaseApiRequestFactory(metaclass=abc.ABCMeta):
    """腾讯云API基础类

    基于腾讯云API开发，定义所有API请求的公用配置代码。

    Attribute:
        _secret_id: 密钥ID
        _secret_key: 密钥Key
        _algorithm: 签名算法，目前固定为 TC3-HMAC-SHA256
        _service: 服务名称，如：cvm，cdb，ckafka等
        _host: API host，如：cvm.tencentcloudapi.com
        _http_request_method: HTTP请求方法，如：GET，POST
        _content_type:
            HTTP 请求的 Content-Type，
            目前支持 Content-Type: application/json
            以及 Content-Type: multipart/form-data 两种协议格式
        _canonical_uri: URI参数，API 3.0 固定为正斜杠（/）
        _canonical_headers:
            参与签名的头部信息，至少包含 host 和 content-type 两个头部，
            也可加入自定义的头部参与签名以提高自身请求的唯一性和安全性。
            拼接规则：
                1. 头部 key 和 value 统一转成小写，并去掉首尾空格，按照 key:value\n 格式拼接；
                2. 多个头部，按照头部 key（小写）的 ASCII 升序进行拼接。
        _canonical_query_string:
            发起 HTTP 请求 URL 中的查询字符串，对于 POST 请求，固定为空字符串""，
            对于 GET 请求，则为 URL 中问号（?）后面的字符串内容，
            例如：Limit=10&Offset=0。
            注意：CanonicalQueryString 需要参考 RFC3986 进行 URLEncode，
                 字符集 UTF8，推荐使用编程语言标准库，所有特殊字符均需编码，大写形式。
        _signed_headers:
            参与签名的头部信息，说明此次请求有哪些头部参与了签名，
            和 CanonicalHeaders 包含的头部内容是一一对应的。
            content-type 和 host 为必选头部。
            拼接规则：
                1. 头部 key 统一转成小写；
                2. 多个头部 key（小写）按照 ASCII 升序进行拼接，并且以分号（;）分隔。
    """
    def __init__(self, secret_id: str, secret_key: str, region: str):
        self._secret_id = secret_id
        self._secret_key = secret_key
        self._region = region

        # 固定值
        self._algorithm = 'TC3-HMAC-SHA256'
        self._canonical_uri = '/'
        self._http_request_method = 'POST'
        self._canonical_query_string = ''
        self._signed_headers = 'content-type;host'

        # 子类继承后需要根据实际情况重载的变量
        self._service = ''
        self._host = ''
        self._action = ''
        self._version = ''
        self._content_type = 'application/json'

    @property
    def _canonical_headers(self):
        return f"content-type:{self._content_type}\nhost:{self._host}\n"

    @property
    def _endpoint(self):
        return f"https://{self._host}"

    @staticmethod
    def __sign(key, msg):
        """计算签名摘要函数

        :param key: 签名key
        :param msg: 签名内容
        :return: 签名结果
        """
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256)

    def __generate_authorization(self, timestamp: int, payload: str):
        """计算Authorization

        :param timestamp: 时间戳
        :param payload: 请求参数字符串
        :return: Authorization字符串
        """
        # 拼接规范请求串
        canonical_request = (
                self._http_request_method + "\n"
                + self._canonical_uri + "\n"
                + self._canonical_query_string + "\n"
                + self._canonical_headers + "\n"
                + self._signed_headers + "\n"
                + hashlib.sha256(payload.encode("utf-8")).hexdigest()
        )

        # 拼接待签名字符串
        now_date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
        credential_scope = now_date + "/" + self._service + "/" + "tc3_request"
        hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        signature_content = (
                self._algorithm + "\n"
                + str(timestamp) + "\n"
                + credential_scope + "\n"
                + hashed_canonical_request
        )

        # 计算签名
        secret_date = self.__sign(("TC3" + self._secret_key).encode("utf-8"), now_date).digest()
        secret_service = self.__sign(secret_date, self._service).digest()
        secret_signing = self.__sign(secret_service, "tc3_request").digest()
        signature = self.__sign(secret_signing, signature_content).hexdigest()

        return (
            f"{self._algorithm} Credential={self._secret_id}/{credential_scope}, "
            + f"SignedHeaders={self._signed_headers}, Signature={signature}"
        )

    def __make_headers(self, payload: dict):
        timestamp = int(time.time())
        return {
            'Authorization': self.__generate_authorization(timestamp, json.dumps(payload)),
            'Content-Type': self._content_type,
            'Host': self._host,
            'X-TC-Action': self._action,
            'X-TC-Timestamp': str(timestamp),
            'X-TC-Version': self._version,
            'X-TC-Region': self._region,
            'X-TC-Language': 'zh-CN'
        }

    def send_request(self, payload: dict):
        """发送API请求

        :param payload: 请求参数字典
        :return: API响应数据
        """
        headers = self.__make_headers(payload)

        if self._content_type == 'application/json':
            response = requests.post(self._endpoint, headers=headers, json=payload)
        else:
            response = requests.post(self._endpoint, headers=headers, data=payload)

        data = response.json().get('Response')
        if data.get('Error'):
            code = data["Error"]["Code"]
            message = data["Error"]["Message"]
            request_id = data["RequestId"]
            raise TencentCloudSDKException(code, message, request_id)
        return data

    async def send_async_request(self, payload: dict):
        """协程发送API请求

        :param payload: 请求参数字典
        :return: API响应数据
        """
        headers = self.__make_headers(payload)

        async with aiohttp.ClientSession() as session:
            if self._content_type == 'application/json':
                async with session.post(self._endpoint, headers=headers, json=payload) as response:
                    data = await response.json()
            else:
                async with session.post(self._endpoint, headers=headers, data=payload) as response:
                    data = await response.json()

        data = data.get('Response')
        if data.get('Error'):
            code = data["Error"]["Code"]
            message = data["Error"]["Message"]
            request_id = data["RequestId"]
            raise TencentCloudSDKException(code, message, request_id)
        return data
