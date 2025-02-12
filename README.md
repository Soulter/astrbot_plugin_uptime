# astrbot_plugin_uptime

监测站点，异常时发出警报

## 简介

`astrbot_plugin_uptime` 是一个用于监测站点状态的 AstrBot 插件。当站点出现异常时，插件会发出警报通知用户。

## 安装

将插件代码放置在 AstrBot 插件目录中，并在配置文件中启用插件。

## 配置

配置文件 `_conf_schema.json` 中包含以下配置项：

```json
{
    "interval": {
        "description": "间隔时间",
        "type": "int",
        "hint": "站点监控轮询的间隔时间，分钟",
        "obvious_hint": true,
        "default": 3
    }
}
```

## 使用

### 添加站点

使用以下命令添加一个站点到监控列表：

```
/uptime add <url>
```

例如：

```
/uptime add https://example.com
```

### 列出站点

使用以下命令列出所有监控的站点：

```
/uptime ls
```

### 删除站点

使用以下命令从监控列表中删除一个站点：

```
/uptime del <url>
```

例如：

```
/uptime del https://example.com
```

### 检查站点状态

使用以下命令检查所有监控站点的当前状态：

```
/uptime status
```

## 支持

[帮助文档](https://astrbot.soulter.top/center/docs/%E5%BC%80%E5%8F%91/%E6%8F%92%E4%BB%B6%E5%BC%80%E5%8F%91/)
