#!/usr/bin/env python
# -*- coding:utf-8 -*-

from .base import BaseSdkClientFactory
from tencentcloud.cvm.v20170312 import cvm_client


class CVMSdkClientFactory(BaseSdkClientFactory):
    """CVM（云服务器） API客户端工厂类
    """

    def __init__(self, secret_id: str, secret_key: str, region: str):
        super().__init__(secret_id, secret_key, region)
        self._http_profile.endpoint = 'cvm.tencentcloudapi.com'
        self._client_profile.httpProfile = self._http_profile

    def create_client(self):
        """构造CVM API客户端

        :return: CVM API客户端对象
        """
        return cvm_client.CvmClient(self._cred, self._region, self._client_profile)
