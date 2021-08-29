#!/usr/bin/env python
# -*- coding:utf-8 -*-

import abc
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile


class BaseSdkClientFactory(metaclass=abc.ABCMeta):
    """腾讯云SDK客户端基础工厂类。

    基于腾讯云SDK开发，定义所有SDK客户端工厂公用的配置代码。
    知识讲解：
        1. 此类是一个抽象类：不可直接实例化，只能被子类继承，且子类需要实现其所有方法。
        2. __init__方法：类的初始化方法，可以理解为构造函数。
        3. 为什么类的属性前都有一个"self."：声明此属性为当前这个类所属。
        4. 为什么属性前都有1个下划线：声明类的属性为保护属性，仅本类及其子类可以访问。
           顺带一提，如果需要声明属性为私有属性，仅需在属性前加2个下划线即可。
           例如：
               公共属性：attr
               保护属性：_attr
               私有属性：__attr

    Attribute:
        _secret_id: 密钥ID
        _secret_key: 密钥Key
        _region: 地域参数
        _cred: credential对象
        _http_profile: HTTP配置对象
        _client_profile: API客户端配置对象
    """

    def __init__(self, secret_id: str, secret_key: str, region: str):
        self._secret_id = secret_id
        self._secret_key = secret_key
        self._region = region

        self._cred = credential.Credential(self._secret_id, self._secret_key)
        self._http_profile = HttpProfile()
        self._client_profile = ClientProfile()

    @abc.abstractmethod
    def create_client(self):
        """构造API客户端的函数

        知识讲解：
        1. 此方法是一个抽象方法（使用了装饰器"@abc.abstractmethod"）：没有定义方法的逻辑，子类在继承后，由子类自行实现。
        2. 由于本类BaseApiClientFactory是一个抽象类，所以子类在继承后，必须实现这个方法。
        """
        pass
