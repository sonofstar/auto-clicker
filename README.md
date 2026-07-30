# 自动点击器 & 操作录制

[![GitHub release](https://img.shields.io/badge/release-v1.0.0-blue)](https://github.com/sonofstar/auto-clicker/releases/tag/v1.0.0)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-Windows-green)]()

> 一款轻量级的 Windows 桌面自动点击和操作录制工具，支持自动连点、鼠标键盘动作录制与回放。

[English Documentation](README_EN.md)

## 功能特性

### 自动连点
- 可设置点击间隔（1~60000 毫秒）
- 支持左键、右键、中键点击
- 可设置固定次数或无限连点
- 支持跟随鼠标当前位置或自定义坐标点击

### 操作录制与回放
- 录制鼠标点击和键盘按键操作
- 自动记录操作间的时间间隔
- 回放速度可调（0.5x ~ 8x）
- 录制内容可保存为 JSON 文件，支持加载复用
- 实时显示录制动作列表

### 其他
- 暗色主题界面，简洁美观
- 全局快捷键，窗口不在最前也能响应
- 多线程运行，界面不卡顿
- 已打包为单文件 exe，无需安装 Python 即可使用

## 下载安装

### 方式一：下载 exe（推荐）

1. 前往 [Releases](https://github.com/sonofstar/auto-clicker/releases) 页面
2. 下载 `auto-clicker-v1.0.0.exe`
3. 双击运行即可

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/sonofstar/auto-clicker.git
cd auto-clicker

# 安装依赖
pip install pynput

# 运行
python auto_clicker.py
```

## 使用说明

### 自动连点

1. 在「自动连点」标签页设置参数（间隔、按键、次数、位置）
2. 按 `F6` 或点击「开始连点」按钮启动
3. 将鼠标移到目标位置，程序会自动点击
4. 按 `F6` 或 `ESC` 停止

### 录制与回放

1. 切换到「录制 & 回放」标签页
2. 按 `F7` 开始录制
3. 正常操作鼠标和键盘，所有动作会被记录
4. 按 `F7` 停止录制
5. 选择回放速度
6. 按 `F8` 开始回放
7. 可点击「保存录制」将动作保存为 JSON 文件，下次「加载录制」后直接回放

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `F6` | 开始 / 停止自动连点 |
| `F7` | 开始 / 停止录制 |
| `F8` | 回放已录制操作 |
| `ESC` | 紧急停止所有操作 |

> 快捷键为全局热键，即使程序窗口不在最前面也能响应。

## 版本历史

### v1.0.0 (2025-07-30)

- 首个发布版本
- 自动连点功能（间隔、次数、按键、位置可配置）
- 鼠标键盘操作录制与回放
- 录制内容保存 / 加载（JSON 格式）
- 全局快捷键支持（F6/F7/F8/ESC）
- 暗色主题 GUI 界面
- Windows 单文件 exe 打包

## 技术栈

- **Python 3.13** — 编程语言
- **tkinter** — GUI 框架
- **pynput** — 鼠标键盘控制与监听
- **PyInstaller** — 打包为 exe

## 许可证

[MIT License](LICENSE)
