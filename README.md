<div align="center">

# Project. Null

_Another modular bot_

> [ ]

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![Python version: 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)

</div>

~~本项目仍处于开发阶段，暂不建议部署。~~

Discontinued due to bad mental health.

## 目录
  * [目录](#目录)
  * [项目特色](#项目特色)
  * [开始使用](#项目部署)
  * [使用文档](#使用文档)
  * [注意](#注意)
  * [项目结构](#项目结构)
  * [参与贡献](#参与贡献)
  * [许可证](#许可证)
  * [鸣谢](#鸣谢)

## 项目特色

  * 在线插件仓库
  * 基于 SQLAlchemy 的异步 ORM

## 开始使用

<! PlaceHolder !>

## 使用文档

<! PlaceHolder !>

## 注意

<! PlaceHolder !>

## 项目结构

```
Project-Null
├── data ························ 模块数据目录 *
├── library ····················· 程序主体
│   ├── assets ·················· 资源文件
│   │   ├── fonts ··············· 字体文件
│   │   └── icons ··············· 图标文件
│   ├── depend ·················· 依赖注入
│   │   ├── blacklist.py ········ 黑名单
│   │   ├── function_call.py····· 函数调用统计
│   │   ├── interval.py ········· 执行冷却
│   │   ├── permission.py ······· 权限
│   │   └── switch.py ··········· 开关
│   ├── image ··················· 图片处理
│   │   ├── oneui_mock ·········· OneUI 模拟器
│   │   ├── icon.py ············· 图标处理
│   │   ├── image.py ············ 图片处理
│   │   └── text.py ············· 文字处理
│   ├── orm ····················· 数据库
│   │   └── table.py ············ 数据表
│   ├── util ···················· 工具
│   │   ├── blacklist ··········· 黑名单
│   │   ├── dependency.py ······· 项目依赖
│   │   ├── interval.py ········· 执行冷却
│   │   └── switch.py ··········· 开关
│   ├── config.py ··············· 配置
│   ├── context.py ·············· 上下文
│   ├── help.py ················· 帮助
│   └── model.py ················ 模型
├── log ························· 日志目录 *
├── module ······················ 插件目录
│   ├── hub_service ············· 中心服务
│   └── manager ················· 插件管理器
├── CHANGELOG.md ················ 更新日志
├── config.json ················· 项目配置文件 *
├── LICENSE ····················· 许可证
├── main.py ····················· 入口
├── pyproject.toml ·············· 项目依赖 (Poetry)
├── README.md ··················· 项目介绍
└── requirements.txt ············ 项目依赖 (Pip)

* 表示该文件或文件夹在初始化后生成。
```

## 参与贡献

你可以通过以下方式参与到本项目中：

  * 提交 [Issue](https://github.com/ProjectNu11/PN-Plugins/issues)
  * 提交 [Pull Request](https://github.com/ProjectNu11/PN-Plugins/pulls)
  * 在 [Telegram 群组](https://t.me/ProjectNull) 中与我们交流
  * 在 [QQ 群组](https://jq.qq.com/?_wv=1027&k=uKcFPrMI) 中与我们交流

## 许可证

<! PlaceHolder!>

## 鸣谢

  * [mirai](https://github.com/mamoe/mirai), 高效率 QQ 机器人框架 / High-performance bot framework for Tencent QQ
  * [mirai-api-http](https://github.com/project-mirai/mirai-api-http), Mirai HTTP API (console) plugin
  * [Graia Ariadne](https://github.com/GraiaProject/Ariadne), 一个优雅且完备的 Python QQ 自动化框架。基于 Mirai API HTTP v2。
  * [Xenon](https://github.com/BlueGlassBlock/Xenon), 本项目的结构参考
  * [Madoka](https://github.com/MadokaProject/Madoka), 本项目的插件安装实现参考
  * [SAGIRI-BOT](https://github.com/SAGIRI-kawaii/sagiri-bot), 本项目的数据库实现参考
  * [Chitung-public](https://github.com/KadokawaR/Chitung-public), 本项目的配置参考